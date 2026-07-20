import json
import pathlib
import re
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from fairscape_models.schema import Schema, Property

from fairscape_cli.config import (
    DEFAULT_CONTEXT,
    DEFAULT_SCHEMA_TYPE,
    NAAN,
)
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
from fairscape_cli.utils.serialization import model_dump_pruned, write_json_atomic

CANONICAL_TYPES = {'integer', 'number', 'string', 'array', 'boolean', 'object'}
SOURCE_TYPE_KEY = 'source-type'


def frictionless_type_to_json_schema(field_type: str) -> str:
    """Convert Frictionless types to JSON Schema types"""
    type_mapping = {
        'string': 'string',
        'integer': 'integer',
        'number': 'number',
        'boolean': 'boolean',
        'date': 'string',
        'datetime': 'string',
        'year': 'integer',
        'yearmonth': 'string',
        'duration': 'string',
        'geopoint': 'array',
        'geojson': 'object',
        'array': 'array',
        'object': 'object',
        'time': 'string'
    }
    return type_mapping.get(field_type, 'string')


def generate_schema_guid(name: str) -> str:
    """Generate a unique identifier for a schema"""
    prefix = f"schema-{name.lower().replace(' ', '-')}"
    return f"ark:{NAAN}/{prefix}-{GenerateDatetimeSquid()}"


# --------------------------------------------------------------------------- #
# Validation error record + frictionless adapter
# --------------------------------------------------------------------------- #

class ValidationErrorRecord(BaseModel):
    message: str
    failed_keyword: str = "error"
    error_type: str = "ValidationError"
    field: Optional[str] = None
    row: Optional[int] = None
    path: Optional[str] = None

    @property
    def location(self) -> str:
        parts = [
            part for part in (
                self.path,
                f"row {self.row}" if self.row is not None else None,
                self.field,
            ) if part
        ]
        return " / ".join(parts) or "-"


def frictionless_error_to_record(error, path: Optional[str] = None) -> ValidationErrorRecord:
    """Convert a frictionless error object to a ValidationErrorRecord.

    Frictionless 5.x exposes row/field attributes under both snake_case and
    camelCase depending on error class and minor version, so check both.
    """
    row = getattr(error, 'row_number', None)
    if row is None:
        row = getattr(error, 'rowNumber', None)
    field = getattr(error, 'field_name', None)
    if field is None:
        field = getattr(error, 'fieldName', None)
    return ValidationErrorRecord(
        message=error.message,
        row=row,
        field=field,
        failed_keyword=getattr(error, 'type', 'error') or 'error',
        path=path,
    )


# --------------------------------------------------------------------------- #
# Handler contract + registry
# --------------------------------------------------------------------------- #

class SchemaHandler(ABC):
    """Contract for per-format schema inference and validation.

    Implementations may use any machinery internally, but infer() must return
    the canonical fairscape_models Schema and validate() must consume it.
    Register implementations with @register_handler('ext', ...).
    """

    extensions: ClassVar[Tuple[str, ...]] = ()

    @abstractmethod
    def infer(self, filepath: str, name: str, description: str,
              guid: Optional[str] = None) -> Schema:
        """Infer a canonical Schema from a data file."""

    @abstractmethod
    def validate(self, schema: Schema, filepath: str) -> List[ValidationErrorRecord]:
        """Validate a data file against a canonical Schema."""

    def new_schema(self, *, name: str, description: str,
                   properties: Dict[str, Property], required: List[str],
                   guid: Optional[str] = None, separator: str = ",",
                   header: bool = True, **extra) -> Schema:
        return Schema.model_validate({
            "@id": guid or generate_schema_guid(name),
            "@context": DEFAULT_CONTEXT,
            "@type": DEFAULT_SCHEMA_TYPE,
            "name": name,
            "description": description,
            "properties": properties,
            "required": required,
            "separator": separator,
            "header": header,
            **extra,
        })


_HANDLERS: Dict[str, SchemaHandler] = {}


def register_handler(*extensions: str):
    """Class decorator: instantiate the handler and map each extension to it.

    Third parties can add formats by subclassing SchemaHandler and decorating
    with @register_handler('myext') in code that imports fairscape_cli.
    """
    def decorator(cls):
        handler = cls()
        for ext in extensions:
            _HANDLERS[ext.lower().lstrip('.')] = handler
        return cls
    return decorator


def get_handler(filepath: str) -> SchemaHandler:
    ext = pathlib.Path(filepath).suffix.lower().lstrip('.')
    try:
        return _HANDLERS[ext]
    except KeyError:
        raise ValueError(
            f"Unsupported file extension '{ext}'. "
            f"Supported extensions: {', '.join(supported_extensions())}"
        )


def supported_extensions() -> List[str]:
    return sorted(_HANDLERS)


# --------------------------------------------------------------------------- #
# Loading (with backward-compat normalization) + writing
# --------------------------------------------------------------------------- #

# Same index pattern the canonical Property model accepts
_INDEX_PATTERN = re.compile(r'^\d+$|^-?\d+::|^-?\d+::-?\d+$|^::-?\d+')


def _valid_index(value) -> bool:
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        return bool(_INDEX_PATTERN.match(value))
    return False


def normalize_property(name: str, prop: dict, index_fallback: int) -> dict:
    """Normalize a single property dict to canonical Property shape.

    Handles legacy HDF5 schema JSON where each dataset entry is a full
    TabularValidationSchema dump (nested 'properties' but no 'index'), and
    legacy non-canonical type strings like 'datetime'/'year'.
    """
    if not isinstance(prop, dict):
        return prop

    nested = prop.get('properties')
    if isinstance(nested, dict) and not _valid_index(prop.get('index')):
        # Legacy HDF5 dataset entry: rebuild as an object Property, dropping
        # the schema-level wrapper keys the old dump carried.
        return {
            'type': 'object',
            'index': index_fallback,
            'description': prop.get('description') or f"Dataset at {name}",
            'hdf5-path': name,
            'properties': {
                child_name: normalize_property(child_name, child, i)
                for i, (child_name, child) in enumerate(nested.items())
            },
        }

    normalized = dict(prop)
    prop_type = normalized.get('type')
    if prop_type is None:
        normalized['type'] = 'string'
    elif prop_type not in CANONICAL_TYPES:
        normalized.setdefault(SOURCE_TYPE_KEY, prop_type)
        normalized['type'] = frictionless_type_to_json_schema(prop_type)

    if not _valid_index(normalized.get('index')):
        normalized['index'] = index_fallback
    if not normalized.get('description'):
        normalized['description'] = f"Column {name}"

    if isinstance(nested, dict):
        normalized['properties'] = {
            child_name: normalize_property(child_name, child, i)
            for i, (child_name, child) in enumerate(nested.items())
        }
    return normalized


def normalize_schema_document(data: dict) -> dict:
    """Normalize a schema JSON document so legacy files validate canonically."""
    data = dict(data)
    data.setdefault('@type', DEFAULT_SCHEMA_TYPE)
    data.setdefault('separator', ',')
    data.setdefault('header', True)
    data['properties'] = {
        name: normalize_property(name, prop, i)
        for i, (name, prop) in enumerate(data.get('properties', {}).items())
    }
    return data


def load_schema(path: Union[str, pathlib.Path]) -> Schema:
    """Read a schema JSON file into the canonical Schema model."""
    with open(path) as f:
        data = json.load(f)
    return Schema.model_validate(normalize_schema_document(data))


def write_schema(schema: Schema, output_file: Union[str, pathlib.Path]) -> None:
    """Write a canonical Schema to a JSON file."""
    write_json_atomic(output_file, model_dump_pruned(schema, by_alias=True))

from typing import List, Optional

from fairscape_models.schema import Schema, Property

from fairscape_cli.models.schema.core import (
    SchemaHandler,
    ValidationErrorRecord,
    frictionless_type_to_json_schema,
    generate_schema_guid,
    SOURCE_TYPE_KEY,
    register_handler,
    get_handler,
    supported_extensions,
    load_schema,
    write_schema,
    normalize_schema_document,
)
from fairscape_cli.models.schema.properties import (
    DatatypeEnum,
    Items,
    NullProperty,
    StringProperty,
    ArrayProperty,
    BooleanProperty,
    NumberProperty,
    IntegerProperty,
    AppendProperty,
    ClickAppendProperty,
)

# Importing handlers registers the built-in csv/tsv, hdf5, and parquet handlers.
import fairscape_cli.models.schema.handlers  # noqa: F401,E402


def infer_schema(filepath: str, name: str, description: str,
                 guid: Optional[str] = None) -> Schema:
    """Infer a canonical Schema from a data file, dispatching by extension."""
    return get_handler(filepath).infer(filepath, name, description, guid=guid)


def validate_schema(schema: Schema, filepath: str) -> List[ValidationErrorRecord]:
    """Validate a data file against a canonical Schema, dispatching by extension."""
    return get_handler(filepath).validate(schema, filepath)


__all__ = [
    'Schema',
    'Property',
    'SchemaHandler',
    'ValidationErrorRecord',
    'frictionless_type_to_json_schema',
    'generate_schema_guid',
    'SOURCE_TYPE_KEY',
    'register_handler',
    'get_handler',
    'supported_extensions',
    'load_schema',
    'write_schema',
    'normalize_schema_document',
    'infer_schema',
    'validate_schema',
    'DatatypeEnum',
    'Items',
    'NullProperty',
    'StringProperty',
    'ArrayProperty',
    'BooleanProperty',
    'NumberProperty',
    'IntegerProperty',
    'AppendProperty',
    'ClickAppendProperty',
]

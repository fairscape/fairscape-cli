"""
fairscape_cli.models.schema — CLI-facing schema surface.

The typed schema hierarchy, per-format infer/validate, dispatch, and legacy
loading live in `fairscape_models.schema`; this package re-exports them together
with the CLI-only property builders and the file writer.
"""

from fairscape_models.schema import (
    Schema,
    Property,
    TabularSchema,
    HDF5Schema,
    SignalSchema,
    ImageSchema,
    NDArraySchema,
    ValidationErrorRecord,
    generate_schema_guid,
    SOURCE_TYPE_KEY,
    frictionless_type_to_json_schema,
    load_schema,
    normalize_schema_document,
    schema_class_for_file,
    infer_schema,
    validate_schema,
)

from fairscape_cli.models.schema.properties import (
    write_schema,
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

__all__ = [
    'Schema',
    'Property',
    'TabularSchema',
    'HDF5Schema',
    'SignalSchema',
    'ImageSchema',
    'NDArraySchema',
    'ValidationErrorRecord',
    'generate_schema_guid',
    'SOURCE_TYPE_KEY',
    'frictionless_type_to_json_schema',
    'load_schema',
    'write_schema',
    'normalize_schema_document',
    'schema_class_for_file',
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

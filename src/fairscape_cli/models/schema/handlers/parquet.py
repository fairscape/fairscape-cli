from typing import List, Optional

import pyarrow as pa
import pyarrow.parquet as pq

from fairscape_models.schema import Schema, Property

from fairscape_cli.models.schema.core import (
    SchemaHandler,
    ValidationErrorRecord,
    register_handler,
    SOURCE_TYPE_KEY,
)


def arrow_type_to_json_schema(arrow_type: pa.DataType) -> str:
    """Map an Arrow type to one of the six canonical JSON Schema types."""
    if pa.types.is_boolean(arrow_type):
        return 'boolean'
    if pa.types.is_integer(arrow_type):
        return 'integer'
    if pa.types.is_floating(arrow_type) or pa.types.is_decimal(arrow_type):
        return 'number'
    if (pa.types.is_list(arrow_type) or pa.types.is_large_list(arrow_type)
            or pa.types.is_fixed_size_list(arrow_type)):
        return 'array'
    if pa.types.is_struct(arrow_type) or pa.types.is_map(arrow_type):
        return 'object'
    # string/binary/timestamp/date/time/duration/dictionary/...
    return 'string'


@register_handler('parquet')
class ParquetHandler(SchemaHandler):
    """Native Parquet handler.

    Reads the file's embedded Arrow schema directly — no full-table read and
    no pandas round-trip — so exact source types (int64 vs float64,
    timestamp[us] vs date32) are preserved in each Property's 'source-type'.
    Validation compares the embedded schema against the declared one without
    scanning rows.
    """
    extensions = ('parquet',)

    def infer(self, filepath: str, name: str, description: str,
              guid: Optional[str] = None) -> Schema:
        arrow_schema = pq.read_schema(filepath)

        properties = {}
        required_fields = []

        for i, field in enumerate(arrow_schema):
            properties[field.name] = Property(
                type=arrow_type_to_json_schema(field.type),
                description=f"Column {field.name}",
                index=i,
                **{SOURCE_TYPE_KEY: str(field.type)},
            )
            required_fields.append(field.name)

        return self.new_schema(
            name=name,
            description=description,
            guid=guid,
            properties=properties,
            required=required_fields,
        )

    def validate(self, schema: Schema, filepath: str) -> List[ValidationErrorRecord]:
        arrow_schema = pq.read_schema(filepath)
        file_fields = {field.name: field for field in arrow_schema}

        errors = []

        for name, prop in schema.properties.items():
            field = file_fields.get(name)
            if field is None:
                errors.append(ValidationErrorRecord(
                    message=f"Column {name} not found in parquet file",
                    failed_keyword="required",
                    field=name,
                ))
                continue

            actual_source = str(field.type)
            actual_canonical = arrow_type_to_json_schema(field.type)
            declared_source = (prop.model_extra or {}).get(SOURCE_TYPE_KEY)

            if declared_source is not None and declared_source == actual_source:
                continue
            # Fall back to comparing canonical categories so hand-authored
            # schemas (no source-type) or compatible physical-type rewrites
            # still validate.
            if prop.type != actual_canonical:
                declared = declared_source or prop.type
                errors.append(ValidationErrorRecord(
                    message=f"Column {name} type mismatch: schema declares {declared}, file has {actual_source}",
                    failed_keyword="type",
                    field=name,
                ))

        if schema.additionalProperties is False:
            for name in file_fields:
                if name not in schema.properties:
                    errors.append(ValidationErrorRecord(
                        message=f"Column {name} present in parquet file but not declared in schema",
                        failed_keyword="additionalProperties",
                        field=name,
                    ))

        return errors

import pathlib
from typing import Dict, List, Optional

from frictionless import (
    Schema as FrictionlessSchema,
    Resource,
    Dialect,
    Report,
    describe,
    fields,
    formats,
)

from fairscape_models.schema import Schema, Property

from fairscape_cli.models.schema.core import (
    SchemaHandler,
    ValidationErrorRecord,
    frictionless_error_to_record,
    frictionless_type_to_json_schema,
    register_handler,
    SOURCE_TYPE_KEY,
)

_TYPE_TO_FRICTIONLESS_FIELD = {
    'string': fields.StringField,
    'integer': fields.IntegerField,
    'number': fields.NumberField,
    'boolean': fields.BooleanField,
}


def _get_either(prop_details: dict, *keys):
    for key in keys:
        if prop_details.get(key) is not None:
            return prop_details[key]
    return None


def build_frictionless_schema(properties: Dict[str, Property]) -> FrictionlessSchema:
    """Rebuild a frictionless Schema from canonical Properties for row validation."""
    properties_input = {
        name: prop.model_dump(by_alias=True, exclude_none=True)
        for name, prop in properties.items()
    }

    frictionless_schema_obj = FrictionlessSchema()

    sorted_prop_items = []
    spanning_array_prop_name = None
    spanning_array_prop_details = None

    for name, prop_details in properties_input.items():
        index_val = prop_details.get("index")
        if prop_details.get("type") == "array" and isinstance(index_val, str) and "::" in index_val:
            if spanning_array_prop_name is not None:
                raise ValueError("Multiple spanning array properties (index: 'X::') are not supported.")
            spanning_array_prop_name = name
            spanning_array_prop_details = prop_details
        elif isinstance(index_val, int):
            sorted_prop_items.append((name, prop_details, index_val))
        else:
            sorted_prop_items.append((name, prop_details, float('inf')))

    sorted_prop_items.sort(key=lambda x: x[2])

    for name, prop_details, _ in sorted_prop_items:
        field_class = _TYPE_TO_FRICTIONLESS_FIELD.get(prop_details.get('type', 'string'), fields.StringField)

        constraints = {}
        if 'minimum' in prop_details: constraints['minimum'] = prop_details['minimum']
        if 'maximum' in prop_details: constraints['maximum'] = prop_details['maximum']
        if 'pattern' in prop_details: constraints['pattern'] = prop_details['pattern']
        if 'minLength' in prop_details: constraints['minLength'] = prop_details['minLength']
        if 'maxLength' in prop_details: constraints['maxLength'] = prop_details['maxLength']

        if prop_details.get('type') == 'array':
            field = fields.ArrayField(name=name, description=prop_details.get('description', ''), constraints=constraints)
        else:
            field = field_class(name=name, description=prop_details.get('description', ''), constraints=constraints)
        frictionless_schema_obj.add_field(field)

    if spanning_array_prop_name and spanning_array_prop_details:
        prop_name_original = spanning_array_prop_name
        details = spanning_array_prop_details
        item_details = details.get('items', {})
        item_type = item_details.get('type', 'number')
        item_field_class = _TYPE_TO_FRICTIONLESS_FIELD.get(item_type, fields.NumberField)

        # min/max item counts appear as 'min-items'/'max-items' (canonical alias)
        # or 'minItems'/'maxItems' (CLI property models) depending on origin
        num_items = _get_either(details, 'min-items', 'minItems')
        max_items = _get_either(details, 'max-items', 'maxItems')
        if num_items is None or num_items != max_items:
            raise ValueError(f"Spanning array '{prop_name_original}' must have equal and defined minItems and maxItems.")

        for i in range(num_items):
            field_name_for_frictionless = f"{prop_name_original}_{i}"  # e.g., embed_0, embed_1, ...
            field = item_field_class(name=field_name_for_frictionless, description=f"Element {i} of {prop_name_original}")
            frictionless_schema_obj.add_field(field)

    return frictionless_schema_obj


@register_handler('csv', 'tsv')
class TabularHandler(SchemaHandler):
    extensions = ('csv', 'tsv')

    def infer(self, filepath: str, name: str, description: str,
              guid: Optional[str] = None) -> Schema:
        ext = pathlib.Path(filepath).suffix.lower().lstrip('.')
        separator = '\t' if ext == 'tsv' else ','

        resource = describe(filepath)

        properties = {}
        required_fields = []

        for i, field in enumerate(resource.schema.fields):
            json_schema_type = frictionless_type_to_json_schema(field.type)
            extra = {}
            if json_schema_type != field.type:
                extra[SOURCE_TYPE_KEY] = field.type

            properties[field.name] = Property(
                type=json_schema_type,
                description=field.description or f"Column {field.name}",
                index=i,
                **extra,
            )
            required_fields.append(field.name)

        return self.new_schema(
            name=name,
            description=description,
            guid=guid,
            properties=properties,
            required=required_fields,
            separator=separator,
            header=True,
        )

    def validate(self, schema: Schema, filepath: str) -> List[ValidationErrorRecord]:
        frictionless_schema = build_frictionless_schema(schema.properties)

        file_dialect = Dialect()
        file_dialect.header = schema.header if schema.header is not None else True

        if schema.separator:
            csv_control = formats.csv.CsvControl(delimiter=schema.separator)
            file_dialect.add_control(csv_control)

        resource = Resource(
            path=filepath,
            schema=frictionless_schema,
            dialect=file_dialect,
        )

        report: Report = resource.validate()
        errors_list = []
        if not report.valid:
            for task in report.tasks:
                for error_detail in task.errors:
                    errors_list.append(frictionless_error_to_record(error_detail))

        return errors_list

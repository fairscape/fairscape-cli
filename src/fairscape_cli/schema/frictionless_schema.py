import click
import json
from prettytable import PrettyTable
import pathlib
from pydantic import (
    ValidationError
)
from typing import (
    Union,
    Type
)

from fairscape_cli.models.schema.frictionless_tabular import (
    TabularValidationSchema,
    HDF5ValidationSchema,
    write_schema as WriteSchema,
    read_schema as ReadSchema,
    StringProperty,
    NumberProperty,
    IntegerProperty,
    BooleanProperty,
    ArrayProperty,
    AppendProperty,
    ClickAppendProperty,
    DatatypeEnum,
    Items,
    PropertyNameException,
    ColumnIndexException
)

from fairscape_cli.config import (
    FAIRSCAPE_URI
)

@click.group('schema')
def schema():
    """Invoke operations on dataset schema.
    """
    pass

@schema.command('create-tabular')
@click.option('--name', required=True, type=str)
@click.option('--description', required=True, type=str)
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--separator', type=str, required=True)
@click.option('--header', required=False, type=bool, default=False)
@click.argument('schema_file', type=str)
@click.pass_context
def create_tabular_schema(
    ctx,
    name,
    description,
    guid,
    header,
    separator,
    schema_file
):
    """Initialize a Tabular Schema.
    """
    try:
        schema_model = TabularValidationSchema.model_validate({
            "name": name,
            "description":description,
            "guid":guid,
            "properties":{},
            "required": [],
            "header":header,
            "separator": separator
        })

    except ValidationError as metadataError:
        click.echo("ERROR Validating TabularValidationSchema")
        for validationFailure in metadataError.errors():
            click.echo(f"property: {validationFailure.get('loc')} \tmsg: {validationFailure.get('msg')}")
        ctx.exit(code=1)

    WriteSchema(schema_model, schema_file)
    click.echo(f"Wrote Schema: {str(schema_file)}")

@schema.group('add-property')
def add_property():
    """Add a Property to an existing schema.
    """
    pass

@add_property.command('string')
@click.option('--name', type=str, required=True)
@click.option('--index', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.option('--pattern', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_string(ctx, name, index, description, value_url, pattern, schema_file):
    """Add a String Property to an existing Schema.
    """
    try: 
        stringPropertyModel = StringProperty.model_validate({
            "name": name,
            "index": index,
            "type": "string",
            "description": description,
            "valueURL": value_url,
            "pattern": pattern
            })
    except ValidationError as metadataError:
        click.echo("ERROR Validating StringProperty")
        for validationFailure in metadataError.errors():
            click.echo(f"property: {validationFailure.get('loc')} \tmsg: {validationFailure.get('msg')}")
        ctx.exit(code=1)

    ClickAppendProperty(ctx, schema_file, stringPropertyModel, name)

@add_property.command('number')
@click.option('--name', type=str, required=True)
@click.option('--index', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--maximum', type=float, required=False)
@click.option('--minimum', type=float, required=False)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_number(ctx, name, index, description, maximum, minimum, value_url, schema_file):
    """Add a Numeric property to an existing Schema.
    """
    try:
        numberPropertyModel = NumberProperty.model_validate({
            "name": name,
            "index": index,
            "type": "number",
            'maximum': maximum,
            'minimum': minimum,
            "description": description,
            "valueURL": value_url
            })
    except ValidationError as metadataError:
        click.echo("ERROR Validating NumberProperty")
        for validationFailure in metadataError.errors():
            click.echo(f"property: {validationFailure.get('loc')} \tmsg: {validationFailure.get('msg')}")
        ctx.exit(code=1)

    ClickAppendProperty(ctx, schema_file, numberPropertyModel, name)

@add_property.command('boolean')
@click.option('--name', type=str, required=True)
@click.option('--index', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_boolean(ctx, name, index, description, value_url, schema_file):
    """Add a Boolean property to an existing Schema.
    """
    try: 
        booleanPropertyModel = BooleanProperty.model_validate({
            "name": name,
            "index": index,
            "type": "boolean",
            "description": description,
            "valueURL": value_url
            })
    except ValidationError as metadataError:
        click.echo("ERROR Validating BooleanProperty")
        for validationFailure in metadataError.errors():
            click.echo(f"property: {validationFailure.get('loc')} \tmsg: {validationFailure.get('msg')}")
        ctx.exit(code=1)

    ClickAppendProperty(ctx, schema_file, booleanPropertyModel, name)

@add_property.command('integer')
@click.option('--name', type=str, required=True)
@click.option('--index', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--maximum', type=int, required=False)
@click.option('--minimum', type=int, required=False)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_integer(ctx, name, index, description, maximum, minimum, value_url, schema_file):
    """Add an Integer property to an existing Schema.
    """
    try:
        integerPropertyModel = IntegerProperty.model_validate({
            "name": name,
            "index": index,
            "type": "integer",
            "description": description,
            "maximum": maximum,
            "minimum": minimum,
            "valueURL": value_url
            })
    except ValidationError as metadataError:
        click.echo("ERROR Validating IntegerProperty")
        for validationFailure in metadataError.errors():
            click.echo(f"property: {validationFailure.get('loc')} \tmsg: {validationFailure.get('msg')}")
        ctx.exit(code=1)

    ClickAppendProperty(ctx, schema_file, integerPropertyModel, name)

@add_property.command('array')
@click.option('--name', type=str, required=True)
@click.option('--index', type=str, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.option('--items-datatype', type=str, required=True)
@click.option('--min-items', type=int, required=False)
@click.option('--max-items', type=int, required=False)
@click.option('--unique-items', type=bool, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_array(ctx, name, index, description, value_url, items_datatype, min_items, max_items, unique_items, schema_file):
    """Add an Array property to an existing Schema.
    """
    try:
        datatype_enum = DatatypeEnum(items_datatype)
    except Exception:
        print(f"ITEMS Datatype {items_datatype} invalid\n" +
            "ITEMS must be oneOf 'boolean'|'object'|'string'|'number'|'integer'" 
        )
        ctx.exit(code=1)

    try:
        arrayPropertyModel = ArrayProperty(
            datatype='array',
            index=index,
            description=description,
            valueURL=value_url,
            maxItems=max_items,
            minItems=min_items,
            uniqueItems=unique_items,
            items=Items(datatype=datatype_enum)
            )
    except ValidationError as metadataError:
        print("ERROR: MetadataValidationError")
        for validationFailure in metadataError.errors(): 
            click.echo(f"property: {validationFailure.get('loc')} \tmsg: {validationFailure.get('msg')}")
        ctx.exit(code=1)

    ClickAppendProperty(ctx, schema_file, arrayPropertyModel, name)

def determine_schema_type(filepath: str) -> Type[Union[TabularValidationSchema, HDF5ValidationSchema]]:
    """Determine which schema type to use based on file extension"""
    ext = pathlib.Path(filepath).suffix.lower()[1:]
    if ext in ('h5', 'hdf5'):
        return HDF5ValidationSchema
    elif ext in ('csv', 'tsv', 'parquet'):
        return TabularValidationSchema
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

@schema.command('validate')
@click.option('--schema', type=str, required=True)
@click.option('--data', type=str, required=True)
@click.pass_context
def validate(ctx, schema, data): 
    """Execute validation of a Schema against the provided data."""
    if 'ark' not in schema:
        schema_path = pathlib.Path(schema)
        if not schema_path.exists():
            click.echo(f"ERROR: Schema file at path {schema} does not exist")
            ctx.exit(1)
    
    data_path = pathlib.Path(data)
    if not data_path.exists():
        click.echo(f"ERROR: Data file at path {data} does not exist")
        ctx.exit(1)

    try:
        with open(schema) as f:
            schema_json = json.load(f)
        
        schema_class = determine_schema_type(data)
        validation_schema = schema_class.model_validate(schema_json)
        
        validation_errors = validation_schema.validate_file(data)

        if len(validation_errors) != 0:
            error_table = PrettyTable()
            if isinstance(validation_schema, HDF5ValidationSchema):
                error_table.field_names = ['path', 'error_type', 'failed_keyword', 'message']
            else:
                error_table.field_names = ['row', 'error_type', 'failed_keyword', 'message']

            for err in validation_errors:
                if isinstance(validation_schema, HDF5ValidationSchema):
                    error_table.add_row([
                        err.get("path"), 
                        err.get("type"), 
                        err.get("failed_keyword"), 
                        str(err.get('message'))
                    ])
                else:
                    error_table.add_row([
                        err.get("row"), 
                        err.get("type"), 
                        err.get("failed_keyword"), 
                        str(err.get('message'))
                    ])

            print(error_table)
            ctx.exit(1)
        else:
            print('Validation Success')
            ctx.exit(0)

    except ValidationError as metadata_error:
        click.echo("Error with schema definition")
        for validation_failure in metadata_error.errors(): 
            click.echo(f"property: {validation_failure.get('loc')} \tmsg: {validation_failure.get('msg')}")
        ctx.exit(1)
    except Exception as e:
        click.echo(f"Error during validation: {str(e)}")
        ctx.exit(1)

@schema.command('infer')
@click.option('--name', required=True, type=str)
@click.option('--description', required=True, type=str)
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('schema_file', type=str)
@click.pass_context
def infer_schema(ctx, name, description, guid, input_file, schema_file):
    """Infer a schema from a file (CSV, TSV, Parquet, or HDF5)."""
    try:
        schema_class = determine_schema_type(input_file)
        
        schema_model = schema_class.infer_from_file(
            input_file, 
            name, 
            description
        )
        if guid:
            schema_model.guid = guid
            
        WriteSchema(schema_model, schema_file)
        
        ext = pathlib.Path(input_file).suffix.lower()[1:]
        click.echo(f"Inferred Schema from {ext} file: {str(schema_file)}")
    
    except ValueError as e:
        click.echo(f"Error with file type: {str(e)}")
        ctx.exit(code=1)
    except Exception as e:
        click.echo(f"Error inferring schema: {str(e)}")
        ctx.exit(code=1)
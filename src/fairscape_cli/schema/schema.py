import click
import json
from prettytable import PrettyTable
import pathlib
from pydantic import (
        ValidationError
)


from fairscape_cli.models.schema.tabular import (
    TabularValidationSchema,
    ReadSchema,
    ImportDefaultSchemas,
    WriteSchema,
    StringProperty,
    NumberProperty,
    IntegerProperty,
    BooleanProperty,
    ArrayProperty,
    ClickAppendProperty,
    PropertyNameException,
    ColumnIndexException,
    DatatypeEnum,
    Items
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
    """Initalize a Tabular Schema.
    """
    # create the model
    try:
        schema_model = TabularValidationSchema.model_validate({
            "name": name,
            "description":description,
            "guid":guid,
            "propeties":{},
            "required": [],
            "header" :header,
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
    # instantiate the StringProperty
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
    """Add a Numberic property to an existing Schema.
    """
    # instantiate the NumberPropertyModel
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
            datatype = 'array',
            index = index,
            description = description,
            valueURL = value_url,
            maxItems = max_items,
            minItems = min_items,
            uniqueItems = unique_items,
            items = Items(datatype=datatype_enum)
            )

    except ValidationError as metadataError:
        print("ERROR: MetadataValidationError")
        for validationFailure in metadataError.errors(): 
            click.echo(f"property: {validationFailure.get('loc')} \tmsg: {validationFailure.get('msg')}")
        ctx.exit(code=1)

    ClickAppendProperty(ctx, schema_file, arrayPropertyModel, name)
    


@schema.command('validate')
@click.option('--schema', type=str, required=True)
@click.option('--data', type=str, required=True)
#@click.option('--ro-crate', type=str, required=False, default=None)
@click.pass_context
def validate(ctx, schema, data): 
    """Execute validation of a Schema against the provided data.
    """


    # if not a default schema
    if 'ark' not in schema:
        schemaPath = pathlib.Path(schema)
        if not schemaPath.exists():
            click.echo(f"ERROR: Schema file at path {schema} does not exist")
            ctx.exit(1)
    
    dataPath = pathlib.Path(data)
    if not dataPath.exists():
        click.echo(f"ERROR: Data file at path {data} does not exist")
        ctx.exit(1)

    try:
        tabular_schema = ReadSchema(schema)
    except ValidationError as metadataError:
        click.echo("Error with schema definition")
        for validationFailure in metadataError.errors(): 
            click.echo(f"property: {validationFailure.get('loc')} \tmsg: {validationFailure.get('msg')}")
        ctx.exit(1)

    validation_errors = tabular_schema.execute_validation(data)

    if len(validation_errors) !=0:
        # print out all errors

        # create a pretty table of validation errors
        errorTable = PrettyTable()
        errorTable.field_names = ['row', 'error_type', 'failed_keyword',  'message']

        for err in validation_errors:
            errorTable.add_row([err.get("row"), err.get("type"), err.get("failed_keyword"), str(err.get('message'))])

        print(errorTable)
        ctx.exit(1)

    else:
        print('Validation Success')
        ctx.exit(0)



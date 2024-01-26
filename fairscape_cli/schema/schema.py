import click
import json

from fairscape_cli.models.schema.image import (
    ImageSchema,
    ImageValidation,
    ImageValidationException,
    ImagePathNotFoundException,
)
from fairscape_cli.models.schema.tabular import (
    TabularValidationSchema,
    ReadSchema,
    WriteSchema,
    StringProperty,
    NumberProperty,
    IntegerProperty,
    BooleanProperty,
    ArrayProperty,
    ClickAppendProperty,
    PropertyNameException,
    ColumnIndexException,
)

from fairscape_cli.models.utils import (
    InstantiateModel
)

from fairscape_cli.config import (
    FAIRSCAPE_URI
)





@click.group('schema')
def schema():
    pass

@schema.group('create')
def create():
    pass


@schema.command('create-tabular')
@click.option('--name', required=True, type=str)
@click.option('--description', required=True, type=str)
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--seperator', type=str, required=True)
@click.option('--header', required=False, type=bool, default=False)
@click.argument('schema_file', type=click.Path(exists=False))
@click.pass_context
def create_tabular(
     name,
     description,
     guid,
     header,
     seperator,
     schema_file,
     ctx
):
    # create the model
    try:
        schema_model = TabularValidationSchema.model_validate({
            "name": name,
            "description":description,
            "guid":guid,
            "propeties":{},
            "required": [],
            "header" :header,
            "seperator": seperator
        })
    except ValidationError as metadataError:
        click.echo("ERROR Validating TabularValidationSchema")
        for validationFailure in metadataError.errors():
            click.echo(f"loc: {validationFailure.loc}\tinput: {validationFailure.input}\tmsg: {validationFailure.msg}")
        click.exit(code=1)

    WriteSchema(schema_model, schema_file)
    click.echo(f"Wrote Schema: {str(schema_file)}") 



@schema.group('add-property')
def add_property():
    """ Add a Property to an existing schema
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
    # instantiate the StringProperty
    stringPropertyMetadata = {
            "name": name,
            "index": index,
            "type": "string",
            "description": description,
            "valueURL": value_url,
            "pattern": pattern
            }
    stringPropertyModel = InstantiateModel(ctx, stringPropertyMetadata, StringProperty)
    ClickAppendProperty(ctx, schema_file, stringPropertyModel, name)



@add_property.command('number')
@click.option('--name', type=str, required=True)
@click.option('--index', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_number(ctx, name, index, description, value_url, schema_file):
    # instantiate the NumberPropertyModel
    numberPropertyMetadata = {
        "name": name,
        "index": index,
        "description": description,
        "valueURL": value_url
        }
    numberPropertyModel = InstantiateModel(ctx, numberPropertyMetadata, NumberProperty)
    ClickAppendProperty(ctx, schema_file, numberPropertyModel, name)



@add_property.command('boolean')
@click.option('--name', type=str, required=True)
@click.option('--index', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_boolean(ctx, name, index, description, value_url, schema_file):
    booleanPropertyMetadata = {
        "name": name,
        "index": index,
        "description": description,
        "valueURL": value_url
        }
    booleanPropertyModel = InstantiateModel(ctx, booleanPropertyMetadata, BooleanProperty) 
    ClickAppendProperty(ctx, schema_file, booleanPropertyModel, name)


@add_property.command('integer')
@click.option('--name', type=str, required=True)
@click.option('--index', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_integer(ctx, name, index, description, value_url, schema_file):
    integerPropertyMetadata = {
        "name": name,
        "index": index,
        "description": description,
        "valueURL": value_url
        }
    integerPropertyModel = InstantiateModel(ctx, integerPropertyMetadata, IntegerProperty)
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
    arrayPropertyModel = InstantiateArrayModel(ctx, name, index, description, value_url, items_datatype, min_items, max_items, unique_items)
    ClickAppendProperty(ctx, schema_file, arrayPropertyModel, name)
    

@create.command('image')
def create_image():
    pass

@schema.command('validate')
@click.option('--schema', type=str, required=True)
@click.option('--data', type=str, required=True)
@click.option('--ro-crate', type=str, required=False, default=None)
@click.pass_context
def validate(ctx, schema, data, ro_crate):

    # if ro-crate was passed
    if ro_crate:
        print('Not Yet Implemented')
        ctx.exit(0)

        # TODO find all schemas in RO-Crate
        # TODO find all data using schemas in RO-Crate

        # TODO execute validation on all RO-Crate schema

    elif schema and data:
        tabular_schema = ReadSchema(schema)
        validation_errors = tabular_schema.execute_validation(data)

        if len(validation_errors) !=0:
            # print out all errors
            print('Errors Validating Data')
            for key, value in validation_errors:
                print(f'{key}: {value}')
            ctx.exit(1)

        else:
            print('\nValidation Success')
            ctx.exit(0)

    else:
        print('ERROR: must pass either schema & data or ro_crate path')


@schema.command('register')
@click.option('--schema', type=str, required=True)
def register(schema):

    # TODO read the schema

    # TODO upload to remote fairscape
    pass


@schema.command('list')
@click.option('--fairscape-uri', type=str, required=False, default=FAIRSCAPE_URI)
def list(fairscape_uri):

    # TODO list all schemas from fairscape remote
    pass


@schema.command('get')
@click.option('--schema-guid', type=str, required=True)
@click.option('--fairscape-uri', type=str, required=False, default=FAIRSCAPE_URI)
def get(schema_guid, fairscape_uri):

    # TODO get schema spec from fairscape remote
    pass

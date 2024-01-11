import click

from fairscape_cli.models.schema.image import (
    ImageSchema,
    ImageValidation,
    ImageValidationException,
    ImagePathNotFoundException,
)
from fairscape_cli.models.schema.tabular import (
    TabularValidationSchema,
    WriteSchema,
    InstantiateStringModel,
    InstantiateBooleanModel,
    InstantiateIntegerModel,
    InstantiateNumberModel,
    InstantiateArrayModel,
    ClickAppendProperty,
    PropertyNameException,
    ColumnIndexException,
)
import json




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
def create_tabular(
     name,
     description,
     guid,
     header,
     seperator,
     schema_file
):
    # create the model
    schema_model = TabularValidationSchema(
        **{
        "name": name,
        "description":description,
        "guid":guid,
        "propeties":{},
        "required": [],
        "header" :header,
        "seperator": seperator
    })


    WriteSchema(schema_model, schema_file)
    click.echo(f"Wrote Schema: {str(schema_file)}") 



@schema.group('add-property')
def add_property():
    """ Add a Property to an existing schema
    """
    pass


@add_property.command('string')
@click.option('--name', type=str, required=True)
@click.option('--number', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.option('--pattern', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_string(ctx, name, number, description, value_url, pattern, schema_file):
    # instantiate the StringProperty
    stringPropertyModel = InstantiateStringModel(ctx, name, number, description, value_url, pattern)
    ClickAppendProperty(ctx, schema_file, stringPropertyModel, name)





@add_property.command('number')
@click.option('--name', type=str, required=True)
@click.option('--number', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_number(ctx, name, number, description, value_url, schema_file):
    ctx = click.get_context()

    # instantiate the StringProperty
    numberPropertyModel = InstantiateStringModel(ctx, name, number, description, value_url, schema_file)
    ClickAppendProperty(ctx, schema_file, numberPropertyModel, name)



@add_property.command('boolean')
@click.option('--name', type=str, required=True)
@click.option('--number', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_boolean(ctx, name, number, description, value_url, schema_file):
    booleanPropertyModel = InstantiateBooleanModel(ctx, name, number, description, value_url) 
    ClickAppendProperty(ctx, schema_file, booleanPropertyModel, name)


@add_property.command('integer')
@click.option('--name', type=str, required=True)
@click.option('--number', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_integer(ctx, name, number, description, value_url, schema_file):
    # instantiate the StringProperty
    integerPropertyModel = InstantiateIntegerModel(ctx, name, number, description, value_url)
    ClickAppendProperty(ctx, schema_file, integerPropertyModel, name)


@add_property.command('array')
@click.option('--name', type=str, required=True)
@click.option('--number', type=str, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.option('--items-datatype', type=str, required=True)
@click.option('--min-items', type=int, required=False)
@click.option('--max-items', type=int, required=False)
@click.option('--unique-items', type=bool, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
@click.pass_context
def add_property_array(ctx, name, number, description, value_url, items_datatype, min_items, max_items, unique_items, schema_file):
# {{{
    arrayPropertyModel = InstantiateArrayModel(ctx, name, number, description, value_url, items_datatype, min_items, max_items, unique_items)
    ClickAppendProperty(ctx, schema_file, arrayPropertyModel, name)
    



    


@create.command('image')
def create_image():
    pass

@schema.command('validate')
def validate():
    pass

@schema.command('register')
def add_column():
    pass

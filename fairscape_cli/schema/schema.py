import click

from fairscape_cli.models.schema.image import (
    ImageSchema,
    ImageValidation,
    ImageValidationException,
    ImagePathNotFoundException,
)
from fairscape_cli.models.schema.tabular import (
    TabularValidationSchema,
    StringProperty,
    BooleanProperty,
    NumberProperty,
    IntegerProperty,
    ArrayProperty,
    DatatypeEnum,
    Items
)
import json


def write_schema(tabular_schema: TabularValidationSchema, schema_file):
    """ Helper Function for writing files
    """

    schema_dictionary = tabular_schema.model_dump(by_alias=True) 
    schema_json = json.dumps(schema_dictionary, indent=2)

    # dump json to a file
    with open(schema_file, "w") as output_file:
        output_file.write(schema_json)


def read_schema(schema_file) -> TabularValidationSchema:
    """ Helper function for reading the schema and marshaling into the pydantic model
    """
    # read the schema
    with open(schema_file, "r") as input_schema:
        input_schema_data = input_schema.read()
        schema_json =  json.loads(input_schema_data) 

        # load the model into 
        return TabularValidationSchema(**schema_json)



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

    # TODO if -i flag is included
    # interactive prompt for creating properties

    #if click.confirm("Add a property?"):
        # add property
    #    click.echo("good choice")

    schema_dictionary = schema_model.model_dump(by_alias=True) 
    schema_json = json.dumps(schema_dictionary, indent=2)

    # dump json to a file
    with open(schema_file, "w") as output_file:
        output_file.write(schema_json)

    #click.echo(f"Wrote Schema: {str(schema_file)}")    



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
def add_property_string(name, number, description, value_url, pattern, schema_file):

    try:
        schema_model = read_schema(schema_file)
    # TODO improve exception handling
    except Exception as e:
        click.echo(f"Exception Loading Schema\n{str(e)}")

    # instantiate the StringProperty
    property_model = StringProperty(
        type = "string",
        number = number,
        description = description,
        valueURL = value_url,
        pattern = pattern
    )

    # set the property
    schema_model.properties[name] = property_model

    try:
        write_schema(schema_model, schema_file)
        click.echo(f"Updated Schema: {schema_file}")      
    # TODO improve exception handling
    except Exception as e:
        click.echo(f"Error Dumping Schema\n{str(e)}")



@add_property.command('number')
@click.option('--name', type=str, required=True)
@click.option('--number', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
def add_property_number(name, number, description, value_url, schema_file):

    try:
        schema_model = read_schema(schema_file)
    # TODO improve exception handling
    except Exception as e:
        click.echo(f"Exception Loading Schema\n{str(e)}")

    # instantiate the StringProperty
    property_model = NumberProperty(
        type = "number",
        number = number,
        description = description,
        valueURL = value_url,
    )

    # set the property
    schema_model.properties[name] = property_model

    try:
        write_schema(schema_model, schema_file)
        click.echo(f"Updated Schema: {schema_file}")      
        click.exit(code=0)
    # TODO improve exception handling
    except Exception as e:
        click.echo(f"Error Dumping Schema\n{str(e)}")
        click.exit(code=1)


@add_property.command('boolean')
@click.option('--name', type=str, required=True)
@click.option('--number', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
def add_property_boolean(name, number, description, value_url, schema_file):

    try:
        schema_model = read_schema(schema_file)
    # TODO improve exception handling
    except Exception as e:
        click.echo(f"Exception Loading Schema\n{str(e)}")

    # instantiate the StringProperty
    property_model = BooleanProperty(
        type = "boolean",
        number = number,
        description = description,
        valueURL = value_url,
    )

    # set the property
    schema_model.properties[name] = property_model

    try:
        write_schema(schema_model, schema_file)
        click.echo(f"Updated Schema: {schema_file}")      
    # TODO improve exception handling
    except Exception as e:
        click.echo(f"Error Dumping Schema\n{str(e)}")



@add_property.command('integer')
@click.option('--name', type=str, required=True)
@click.option('--number', type=int, required=True)
@click.option('--description', type=str, required=True)
@click.option('--value-url', type=str, required=False)
@click.argument('schema_file', type=click.Path(exists=True))
def add_property_integer(name, number, description, value_url, schema_file):

    try:
        schema_model = read_schema(schema_file)
    # TODO improve exception handling
    except Exception as e:
        click.echo(f"Exception Loading Schema\n{str(e)}")

    # instantiate the StringProperty
    property_model = IntegerProperty(
        type = "integer",
        number = number,
        description = description,
        valueURL = value_url,
    )

    # set the property
    schema_model.properties[name] = property_model

    try:
        write_schema(schema_model, schema_file)
        click.echo(f"Updated Schema: {schema_file}")      
    # TODO improve exception handling
    except Exception as e:
        click.echo(f"Error Dumping Schema\n{str(e)}")


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
def add_property_array(name, number, description, value_url, items_datatype, min_items, max_items, unique_items, schema_file):
# {{{
    try:
        datatype_enum = DatatypeEnum(items_datatype)
    except Exception as e:
        click.echo(f"ITEMS Datatype {itemsDatatype} invalid\n" +
            "ITEMS must be oneOf 'boolean'|'object'|'string'|'number'|'integer'" 
        )
        click.exit()

    try:
        schema_model = read_schema(schema_file)

    # TODO improve exception handling
    except Exception as e:
        click.echo(f"Exception Loading Schema\n{str(e)}")

    # instantiate the StringProperty
    property_model = ArrayProperty(
        type = "array",
        number = number,
        description = description,
        valueURL = value_url,
        maxItems = max_items,
        minItems = min_items,
        uniqueItems = unique_items,
        items = Items(datatype=datatype_enum)
    )

    # set the property
    schema_model.properties[name] = property_model

    try:
        write_schema(schema_model, schema_file)
        click.echo(f"Updated Schema: {schema_file}")      
    # TODO improve exception handling
    except Exception as e:
        click.echo(f"Error Dumping Schema\n{str(e)}")# }}}


@create.command('image')
def create_image():
    pass

@schema.command('validate')
def validate():
    pass

@schema.command('register')
def add_column():
    pass

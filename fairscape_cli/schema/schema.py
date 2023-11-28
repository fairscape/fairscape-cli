import click

from fairscape_cli.schema.image import (
    ImageSchema,
    ImageValidation,
    ImageValidationException,
    ImagePathNotFoundException,
)
from fairscape_cli.schema.tabular import (
    ValidationSchema,

)



@click.group('schema')
def schema():
    pass

@schema.group('create')
def create():
    pass


@create.command('tabular')
@click.option('--name', required=True, type=str)
@click.option('--description', required=True, type=str)
@click.option('--sperator', required=True, type=str)
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--additionalProperties', required=False, default=False)
@click.option('--required', type=str, multiple=True)
@click.option('--header', required=False, type=bool, default=False,)
@click.parameter('output_path', type=str)
def create_tabular(
     name,
     description,
     guid,
     additionalProperties,
     required,
     header,
     output_path
):
    schema_model = ValidationSchema(
        name=name,
        description=description,
        guid=guid,
        propeties={},
        additionalProperties=additionalProperties,
        required=required,
        header=header
    )

    if click.confirm("Add a property?"):
        # add property
        click.echo("good choice")
    

@schema.command('addProperty')
def addProperty(schema_path):
    """ Add a Property to an existing schema
    """
    pass


@addProperty.command('string')
@click.parameter('schema_path', type=str)
def addPropertyString(schema_path):
    pass


@addProperty.command('number')
@click.parameter('schema_path', type=str)
def addPropertyNumber(schema_path):
    pass


@addProperty.command('bool')
@click.parameter('schema_path', type=str)
def addPropertyBool(schema_path):
    pass


@addProperty.command('int')
@click.parameter('schema_path', type=str)
def addPropertyInt(schema_path):
    pass


@addProperty.command('null')
@click.parameter('schema_path', type=str)
def addPropertyNull(schema_path):
    pass


@addProperty.command('array')
@click.option('--items')
@click.parameter('schema_path', type=str)
def addPropertyArray(items, schema_path):
    pass


@create.command('image')
def create_image():
    pass

@schema.command('validate')
def validate():
    pass

@schema.command('register')
def add_column():
    pass

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

from fairscape_cli.models import ReadROCrateMetadata, AppendCrate

from fairscape_cli.models.schema.tabular import (
    TabularValidationSchema,
    HDF5ValidationSchema,
    write_schema as WriteSchema,
    StringProperty,
    NumberProperty,
    IntegerProperty,
    BooleanProperty,
    ArrayProperty,
    ClickAppendProperty,
    DatatypeEnum,
    Items,
)

@click.group('schema')
def schema():
    """Invoke operations on dataset schema.
    """
    pass

@schema.command('create-tabular')
@click.option('--name', required=True, type=str)
@click.option('--description', required=True, type=str)
@click.option('--guid', required=False, type=str, default=None, show_default=False)
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
        validation_schema = schema_class.from_dict(schema_json)
        
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
                        err.path,
                        err.type,
                        err.failed_keyword,
                        str(err.message)
                    ])
                else:
                    error_table.add_row([
                        err.row,
                        err.type, 
                        err.failed_keyword,
                        str(err.message)
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

@schema.command('infer')
@click.option('--name', required=True, type=str)
@click.option('--description', required=True, type=str)
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--rocrate-path', required=False, type=click.Path(exists=True, path_type=pathlib.Path), help='Optional path to an RO-Crate to append the schema to')
@click.argument('schema_file', type=str)
@click.pass_context
def infer_schema_rocrate(ctx, name, description, guid, input_file, rocrate_path, schema_file):
    """Infer a schema from a file and optionally append it to an RO-Crate.
    
    INPUT_FILE: File to infer schema from (CSV, TSV, Parquet, or HDF5)
    SCHEMA_FILE: Path to save the schema file
    """
    try:
        # Determine schema type and infer schema
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
        
        # If RO-Crate path is provided, append the schema to it
        if rocrate_path:
            
            # Read the RO-Crate to verify it exists and is valid
            try:
                ReadROCrateMetadata(rocrate_path)
            except Exception as exc:
                click.echo(f"ERROR Reading ROCrate: {str(exc)}")
                ctx.exit(code=1)
            
            # Append to RO-Crate
            AppendCrate(cratePath=rocrate_path, elements=[schema_model])
            click.echo(f"Added Schema to RO-Crate with ID: {schema_model.guid}")
        
    except ValueError as e:
        click.echo(f"Error with file type: {str(e)}")
        ctx.exit(code=1)
    except Exception as e:
        click.echo(f"Error inferring schema: {str(e)}")
        ctx.exit(code=1)


@schema.command('add-to-crate')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.argument('schema-file', type=click.Path(exists=True))
@click.pass_context
def register_schema(
    ctx,
    rocrate_path: pathlib.Path,
    schema_file: str,
):
    """Register a JSON Schema with the specified RO-Crate.
    
    ROCRATE-PATH: Path to the RO-Crate to add the schema to
    SCHEMA-FILE: Path to the schema JSON file
    """
    try:
        
        try:
            ReadROCrateMetadata(rocrate_path)
        except Exception as exc:
            click.echo(f"ERROR Reading ROCrate: {str(exc)}")
            ctx.exit(code=1)
        
        # Read schema file
        with open(schema_file, 'r') as f:
            schema_data = json.load(f)
        
        try:
            schema_model = TabularValidationSchema.from_dict(schema_data)
            click.echo(f"Loaded schema as TabularValidationSchema")
        except Exception as tabular_error:
            # If that fails, try HDF5ValidationSchema
            try:
                schema_model = HDF5ValidationSchema.from_dict(schema_data)
                click.echo(f"Loaded schema as HDF5ValidationSchema")
            except Exception as hdf5_error:
                click.echo(f"ERROR: Could not recognize schema format")
                click.echo(f"TabularValidationSchema error: {str(tabular_error)}")
                click.echo(f"HDF5ValidationSchema error: {str(hdf5_error)}")
                ctx.exit(code=1)
        
        AppendCrate(cratePath=rocrate_path, elements=[schema_model])
        click.echo(f"Schema registered with ID: {schema_model.guid}")
        
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        ctx.exit(code=1)
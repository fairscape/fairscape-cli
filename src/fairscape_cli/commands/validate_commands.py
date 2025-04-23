import click
import pathlib
import json
from prettytable import PrettyTable
from pydantic import ValidationError

from fairscape_cli.models.schema.tabular import (
    TabularValidationSchema, HDF5ValidationSchema
)
from fairscape_cli.commands.schema_commands import determine_schema_type

@click.group('validate')
def validate_group():
    """Validate data against schemas or RO-Crate structure."""
    pass

@validate_group.command('schema')
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

# Placeholder for future RO-Crate structural validation
# @validate_group.command('crate')
# @click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
# def validate_crate(ctx, rocrate_path):
#     """Validate the structure and metadata of an RO-Crate."""
#     # Implementation using RO-Crate-py or custom checks
#     click.echo(f"Validating RO-Crate at {rocrate_path} (Not implemented yet)")
#     pass
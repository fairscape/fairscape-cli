import click

from fairscape_cli.validate import validate_json
from fairscape_cli.rocrate import rocrate
from fairscape_cli.schema import schema
#from fairscape_cli.client import client

@click.group()
def cli():
    pass

# Validation Subcommands
cli.add_command(validate_json.validate)

# ROCrate Subcommands
cli.add_command(rocrate.rocrate)

# Schema Subcommands
cli.add_command(schema.schema)

# Fairscape Client Commands
# cli.add_command(client)

if __name__ == "__main__":
    cli()
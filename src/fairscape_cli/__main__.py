import click

from fairscape_cli.rocrate import rocrate
from fairscape_cli.schema import schema
#from fairscape_cli.client import client

@click.group()
def cli():
    """FAIRSCAPE CLI
    A utility for packaging objects and validating metadata for FAIRSCAPE
    """
    pass


# ROCrate Subcommands
cli.add_command(rocrate.rocrate)

# Schema Subcommands
cli.add_command(schema.schema)

# Fairscape Client Commands
# cli.add_command(client)

if __name__ == "__main__":
    cli()
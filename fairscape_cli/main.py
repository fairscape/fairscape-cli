import click

from fairscape_cli.validator import validate
from fairscape_cli.rocrate import rocrate
from fairscape_cli.client import client

@click.group()
def cli():
    pass

# Validation Subcommands
cli.add_command(validate)

# ROCrate Subcommands
cli.add_command(rocrate)

# Fairscape Client Commands
# cli.add_command(client)


if __name__ == "__main__":
    cli()

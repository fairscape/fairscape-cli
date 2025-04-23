import click

# Import command groups from their new locations
from fairscape_cli.commands.rocrate_commands import rocrate_group
from fairscape_cli.commands.import_commands import import_group
from fairscape_cli.commands.build_commands import build_group
from fairscape_cli.commands.publish_commands import publish_group
from fairscape_cli.commands.release_commands import release_group
from fairscape_cli.commands.schema_commands import schema
from fairscape_cli.commands.validate_commands import validate_group

@click.group()
def cli():
    """FAIRSCAPE CLI
    A utility for packaging objects and validating metadata for FAIRSCAPE
    """
    pass

# Add the new top-level command groups
cli.add_command(rocrate_group, name='rocrate')
cli.add_command(import_group, name='import')
cli.add_command(build_group, name='build')
cli.add_command(publish_group, name='publish')
cli.add_command(release_group, name='release')
cli.add_command(schema, name='schema')
cli.add_command(validate_group, name='validate')

if __name__ == "__main__":
    cli()
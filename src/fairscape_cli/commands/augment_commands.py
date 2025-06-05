import click
import pathlib
import json
from typing import List, Optional, Tuple

from fairscape_cli.models.rocrate import (
    UpdateEntitiesInGraph
)


@click.group('augment')
def augment_group():
    """Commands to augment and modify existing RO-Crate metadata."""
    pass


@augment_group.command('update-entities')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--query', 'query_str', required=True, help="MongoDB-style query as a JSON string to select entities.")
@click.option('--update', 'update_str', required=True, help="MongoDB-style update operation as a JSON string.")
@click.pass_context
def update_entities_command(
    ctx,
    rocrate_path: pathlib.Path,
    query_str: str,
    update_str: str
):
    """
    Selects and updates entities within an RO-Crate using MongoDB-like query
    and update operations on the '@graph'.
    """
    try:
        # Validate JSON inputs early
        try:
            query_dict = json.loads(query_str)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in --query string: {e}", err=True)
            ctx.exit(1)

        try:
            update_dict = json.loads(update_str)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in --update string: {e}", err=True)
            ctx.exit(1)

        success, message = UpdateEntitiesInGraph(
            rocrate_path,
            query_dict,
            update_dict
        )

        if success:
            click.echo(message)
        else:
            click.echo(f"Error: {message}", err=True)
            ctx.exit(1)

    except Exception as e:
        # Catch any other unexpected errors from the operation
        click.echo(f"An unexpected error occurred: {type(e).__name__} - {e}", err=True)
        ctx.exit(1)

# Remember to add 'augment_group' to your main CLI in __main__.py

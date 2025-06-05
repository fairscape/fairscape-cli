import click
import pathlib
import json
from fairscape_cli.models.rocrate import (
UpdateEntitiesInGraph
)
from fairscape_cli.entailments.inverse import augment_rocrate_with_inverses, EVI_NAMESPACE

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
        click.echo(f"An unexpected error occurred: {type(e).__name__} - {e}", err=True)
        ctx.exit(1)

@augment_group.command('link-inverses')
@click.argument(
    'rocrate-path',
    type=click.Path(path_type=pathlib.Path, exists=True, file_okay=True, dir_okay=True)
)
@click.option(
    '--ontology-path',
    type=click.Path(path_type=pathlib.Path, dir_okay=False),
    default=None,
    help="Path to the OWL ontology file. Defaults to evi.xml in the entailments folder."
)
@click.option(
    '--namespace',
    default=EVI_NAMESPACE,
    show_default=True,
    help="The primary namespace URI used for property keys in JSON."
)
@click.pass_context
def link_inverses_command(
    ctx,
    rocrate_path: pathlib.Path,
    ontology_path: pathlib.Path,
    namespace: str
):
    """
    Augments an RO-Crate by finding owl:inverseOf properties defined in the
    ontology and ensuring both sides of the relationship are present in the
    RO-Crate's JSON-LD metadata.
    """
    if ontology_path is None:
        current_file = pathlib.Path(__file__)
        package_root = current_file.parent.parent
        default_ontology_path = package_root / "entailments" / "evi.xml"
        
        if not default_ontology_path.exists():
            click.echo(f"Error: Default ontology file not found at {default_ontology_path}", err=True)
            click.echo("Please specify --ontology-path explicitly.", err=True)
            ctx.exit(1)
        
        ontology_path = default_ontology_path
    elif not ontology_path.exists():
        click.echo(f"Error: Specified ontology file does not exist: {ontology_path}", err=True)
        ctx.exit(1)
    
    click.echo(f"Augmenting RO-Crate at: {rocrate_path}")
    click.echo(f"Using ontology: {ontology_path}")
    click.echo(f"Primary JSON property namespace: {namespace}")
    
    success = augment_rocrate_with_inverses(
        rocrate_path=rocrate_path,
        ontology_path=ontology_path,
        default_namespace_prefix=namespace
    )
    
    if success:
        pass
    else:
        click.echo("Augmentation failed. See messages above for details.", err=True)
        ctx.exit(1)
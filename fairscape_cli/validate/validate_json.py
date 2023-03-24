from fairscape_cli.models import (
    Dataset,
    Computation,
    Software
)
import click
from pydantic import ValidationError


def validate_model(path: str):
    json_path = Path(path)
    
    with open(json_path, "r") as json_file:
        metadata = json.load(json_file)
        instance_model = model(**metadata)
        return instance_model


@click.group('validate')
def validate():
    pass

@validate.command('software')
@click.argument("json_file", type=click.Path(exists=True))
def software(json_file: click.Path):
    try:
        software_model = validate_model(json_file, Software)

    except (ValidationError, ValueError) as e: 
        raise click.ClickException(
            message=e
        )
 


@validate.command('dataset')
@click.argument("json_file", type=click.Path(exists=True))
def dataset(json_file: click.Path): 
    try:
        dataset_model = validate_model(json_file, Dataset)

    except (ValidationError, ValueError) as e: 
        raise click.ClickException(
            message=e
        )
 

@validate.command('computation')
@click.argument("json_file", type=click.Path(exists=True))
def computation(json_file: click.Path):
    try:
        computation_model = validate_model(json_file, Computation)

    except (ValidationError, ValueError) as e: 
        raise click.ClickException(
            message=e
        )
 




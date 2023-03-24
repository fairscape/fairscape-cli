import typer
from pathlib import Path
import json
from fairscape_cli.apps.models.dataset import Dataset
from fairscape_cli.apps.models.software import Software
from fairscape_cli.apps.models.computation import Computation
from fairscape_cli.apps.utils import is_path_valid
from pydantic import ValidationError

app = typer.Typer()

def validate_model(path: str, model):
    json_path = Path(path)
    
    if is_path_valid(path=json_path) == False:
        print(f"Invalid Path: {json_path}")
        typer.Exit(code=1)
    else:
        with open(json_path, "r") as json_file:
            metadata = json.load(json_file)
            instance_model = model(**metadata)


@app.command("json")
def validate_json_document(
    passed_path: str = typer.Argument(
        ..., 
        help="Path to the metadata in JSON/JSON-LD format"
        )
    ):

    json_path = Path(passed_path)

    if is_path_valid(path=json_path):
        with open(json_path, "r") as json_file:
            try:
                data = json.load(json_file)
            # print(json.dumps(data, indent=2))
            except json.decoder.JSONDecodeError as e:
                typer.secho(e, fg=typer.colors.BRIGHT_RED)


@app.command("dataset")
def validate_dataset_metadata(
    path: str = typer.Argument(
        ..., 
        help="Path to the Dataset metadata in JSON/JSON-LD format"
        )
    ):
    
    try:
        validate_model(path, Dataset)

    except ValidationError as e:
        typer.secho(e, fg=typer.colors.BRIGHT_RED)
        typer.Exit(code=1)

    except ValueError as e:
        typer.secho(e, fg=typer.colors.BRIGHT_RED)
        typer.Exit(code=1)

@app.command("software")
def validate_software_metadata(
    path: str = typer.Argument(
        ..., 
        help="Path to the Software metadata in JSON/JSON-LD format"
        )
    ):

    try:
        validate_model(path, Software)

    except ValidationError as e:
        typer.secho("ERROR")
        typer.secho(e, fg=typer.colors.BRIGHT_RED)
        typer.Exit(code=1)

    except ValueError as e:

        typer.secho("ERROR")
        typer.secho(e, fg=typer.colors.BRIGHT_RED)
        typer.Exit(code=1)


@app.command("computation")
def validate_computation_metadata(
    path: str = typer.Argument(
        ..., 
        help="Path to the Computation metadata in JSON/JSON-LD format"
        )
    ):

    try:
        validate_model(path, Computation)

    except ValidationError as e:
        typer.secho(e, fg=typer.colors.BRIGHT_RED)
        typer.Exit(code=1)

    except ValueError as e:
        typer.secho(e, fg=typer.colors.BRIGHT_RED)
        typer.Exit(code=1)



if __name__ == "__main__":
    app()

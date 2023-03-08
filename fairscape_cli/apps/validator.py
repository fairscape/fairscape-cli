import typer
from pathlib import Path
import json
from fairscape_cli.apps.models.dataset import Dataset
from fairscape_cli.apps.models.software import Software
from fairscape_cli.apps.models.computation import Computation
from fairscape_cli.apps.utils import is_path_valid
from pydantic import ValidationError

app = typer.Typer()


@app.command("json")
def validate_json_document(
    path: str = typer.Argument(
        ..., 
        help="Path to the metadata in JSON/JSON-LD format"
        )
    ):

    json_path = Path(path)

    if is_path_valid(path=json_path):
        try:
            json_file = open(json_path)
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

    json_path = Path(path)

    if is_path_valid(path=json_path):
        try:
            json_metadata = open(json_path)
            metadata = json.load(json_metadata)
            try:
                dataset = Dataset(**metadata)
            except ValidationError as e:
                typer.secho(e, fg=typer.colors.BRIGHT_RED)
        except ValueError as e:
            typer.secho(e, fg=typer.colors.BRIGHT_RED)


@app.command("software")
def validate_software_metadata(
    path: str = typer.Argument(
        ..., 
        help="Path to the Software metadata in JSON/JSON-LD format"
        )
    ):

    json_path = Path(path)

    if is_path_valid(path=json_path):
        try:
            json_file = open(json_path)
            metadata = json.load(json_file)
            try:
                software = Software(**metadata)
            except ValidationError as e:
                typer.secho(e, fg=typer.colors.BRIGHT_RED)
        except ValueError as e:
            typer.secho(e, fg=typer.colors.BRIGHT_RED)


@app.command("computation")
def validate_computation_metadata(
    path: str = typer.Argument(
        ..., 
        help="Path to the Computation metadata in JSON/JSON-LD format"
        )
    ):

    json_path = Path(path)

    if is_path_valid(path=json_path):
        try:
            json_file = open(json_path)
            metadata = json.load(json_file)
            try:
                computation = Computation(**metadata)
            except ValidationError as e:
                typer.secho(e, fg=typer.colors.BRIGHT_RED)
        except ValueError as e:
            typer.secho(e, fg=typer.colors.BRIGHT_RED)


if __name__ == "__main__":
    app()

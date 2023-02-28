import typer
from pathlib import Path
import json
from apps.models.dataset import Dataset
from apps.models.software import Software
from apps.models.computation import Computation
from pydantic import ValidationError
from apps.utils import is_path_valid

app = typer.Typer()


@app.command("json")
def validate_json_document(path: Path = typer.Argument(..., help="Path to the metadata in JSON/JSON-LD format")):

    if is_path_valid(path=path):
        try:
            file = open(path)
            data = json.load(file)
            # print(json.dumps(data, indent=2))
        except json.decoder.JSONDecodeError as e:
            typer.secho(e, fg=typer.colors.BRIGHT_RED)


@app.command("dataset")
def validate_dataset_metadata(path: Path = typer.Argument(..., help="Path to the Dataset metadata in JSON/JSON-LD "
                                                                    "format")):
    if is_path_valid(path=path):
        try:
            file = open(path)
            metadata = json.load(file)
            try:
                dataset = Dataset(**metadata)
            except ValidationError as e:
                typer.secho(e, fg=typer.colors.BRIGHT_RED)
        except ValueError as e:
            typer.secho(e, fg=typer.colors.BRIGHT_RED)


@app.command("software")
def validate_software_metadata(path: Path = typer.Argument(..., help="Path to the Software metadata in JSON/JSON-LD "
                                                                     "format")):
    if is_path_valid(path=path):
        try:
            file = open(path)
            metadata = json.load(file)
            try:
                software = Software(**metadata)
            except ValidationError as e:
                typer.secho(e, fg=typer.colors.BRIGHT_RED)
        except ValueError as e:
            typer.secho(e, fg=typer.colors.BRIGHT_RED)


@app.command("computation")
def validate_computation_metadata(path: Path = typer.Argument(..., help="Path to the Computation metadata in "
                                                                        "JSON/JSON-LD format")):
    if is_path_valid(path=path):
        try:
            file = open(path)
            metadata = json.load(file)
            try:
                computation = Computation(**metadata)
            except ValidationError as e:
                typer.secho(e, fg=typer.colors.BRIGHT_RED)
        except ValueError as e:
            typer.secho(e, fg=typer.colors.BRIGHT_RED)


if __name__ == "__main__":
    app()

import typer
from pathlib import Path
import json
from apps.models.dataset import Dataset
from apps.models.software import Software
from apps.models.computation import Computation
from pydantic import ValidationError
from apps.utils import *

app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command("json")
def validate_json_document(path: Path = typer.Argument(..., help="Local file path in JSON format")):

    if valid_path(path=path):
        if valid_file_format(path):
            message_success = "Successfully validated JSON document "
            message_failure = "Failed to validate JSON document "
            try:
                file = open(path)
                data = json.load(file)
                # print(json.dumps(data, indent=2))
                typer.secho(f"{message_success} {path}", fg=typer.colors.GREEN)
            except json.decoder.JSONDecodeError as e:
                typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
                typer.secho(e, fg=typer.colors.BRIGHT_RED)
            except TypeError as e:
                typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
                typer.secho(e, fg=typer.colors.BRIGHT_RED)


@app.command("dataset")
def validate_dataset_metadata(path: Path = typer.Argument(..., help="Path to the Dataset metadata")):
    message_success = "Successfully validated dataset metadata "
    message_failure = "Failed to validate dataset metadata "
    if valid_path(path=path):
        try:
            file = open(path)
            metadata = json.load(file)
            try:
                dataset = Dataset(**metadata)
                typer.secho(f"{message_success} {path}", fg=typer.colors.GREEN)
            except ValidationError as e:
                typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
                typer.secho(e, fg=typer.colors.BRIGHT_RED)
        except ValueError as e:
            typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
            typer.secho(e, fg=typer.colors.BRIGHT_RED)


@app.command("software")
def validate_software_metadata(path: Path = typer.Argument(..., help="Path to the Software metadata")):
    message_success = "Successfully validated software metadata "
    message_failure = "Failed to validate software metadata "
    if valid_path(path=path):
        try:
            file = open(path)
            metadata = json.load(file)
            try:
                software = Software(**metadata)
                typer.secho(f"{message_success} {path}", fg=typer.colors.GREEN)
            except ValidationError as e:
                typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
                typer.secho(e, fg=typer.colors.BRIGHT_RED)
        except ValueError as e:
            typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
            typer.secho(e, fg=typer.colors.BRIGHT_RED)


@app.command("computation")
def validate_computation_metadata(path: Path = typer.Argument(..., help="Path to the Computation metadata")):
    message_success = "Successfully validated computation metadata "
    message_failure = "Failed to validate computation metadata "
    if valid_path(path=path):
        try:
            file = open(path)
            metadata = json.load(file)
            try:
                computation = Computation(**metadata)
                typer.secho(f"{message_success} {path}", fg=typer.colors.GREEN)
            except ValidationError as e:
                typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
                typer.secho(e, fg=typer.colors.BRIGHT_RED)
        except ValueError as e:
            typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
            typer.secho(e, fg=typer.colors.BRIGHT_RED)


if __name__ == "__main__":
    app()

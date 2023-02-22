import typer
import json
from pathlib import Path
from typing import Optional

rocrate_app = typer.Typer(pretty_exceptions_show_locals=False)

@rocrate_app.command()
def create(name: str, path: str):
    print(f"creating ro crate {name} at path {path}")


@rocrate_app.command()
def describe(path: str):
    pass


@rocrate_app.command()
def zip(path: str):
    pass


@rocrate_app.command()
def hash(path: str):
    pass


@rocrate_app.command()
def validate_json(path: Path = typer.Argument(..., help="Metadata file path"),
             json_type: bool = typer.Option(False, help="Document of type json"),
             dataset_type: bool = typer.Option(False, help="Document of type dataset"),
             software_type: bool = typer.Option(False, help="Document of type software"),
             computation_type: bool = typer.Option(False, help="Document of type computation")):
    if path is None:
        print('No metadata path')
        raise typer.Abort()
    if path.is_file():
        content = path.read_text();
        print(f"File content: {content}")

        try:
            file_metadata = open(path)
            json.load(file_metadata)
        except ValueError as e:
            raise e
    elif path.is_dir():
        print("Expecting file but got a directory. Aborting...")
        typer.Abort()
    elif not path.exists():
        print(f"Unable to find any metadata file at the path: \"{path}\"")





@rocrate_app.command()
def delete(
    path: str, 
    force: bool = typer.Option(..., prompt="Confirm to delete RO crate")
):
    if force:
        print(f"deleting ro crate: {path}")
    else:
        print("cancelling deletion")


@rocrate_app.command()
def publish(path: str):
    pass


@rocrate_app.command()
def add_dataset():
    pass


@rocrate_app.command()
def add_software():
    pass


@rocrate_app.command()
def computation():
    pass


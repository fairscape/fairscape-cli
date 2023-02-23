import typer
from pathlib import Path
import json
from apps.models.dataset import Dataset
from apps.models.software import Software

app = typer.Typer()


@app.command("json")
def validate_json(path: Path = typer.Argument(..., help="Path to the metadata in JSON/JSON-LD format")):
    if path.is_file():
        # content = path.read_text();
        # print(f"File content: {content}")
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


@app.command("dataset")
def validate_dataset(path: Path):
    pass


@app.command("software")
def validate_software(path: Path):
    pass


@app.command("computation")
def validate_computation(path: Path):
    pass


if __name__ == "__main__":
    app()
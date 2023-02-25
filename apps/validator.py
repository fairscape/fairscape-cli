import typer
from pathlib import Path
import json
from apps.models.dataset import Dataset
from apps.models.software import Software
from pydantic import ValidationError
from pyld import jsonld

app = typer.Typer()


@app.command("json")
def validate_json(path: Path = typer.Argument(..., help="Path to the metadata in JSON/JSON-LD format")):

    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}


    if path.is_file():
        # content = path.read_text();
        # print(f"File content: {content}")
        file_extensions = [".json", ".jsonld"]
        # abort if correct file format is not submitted
        if path.suffix not in file_extensions:
            print(f"Only {file_extensions} files are allowed")
            typer.Abort()
        else:
            try:
                metadata_file = open(path)
                data = json.load(metadata_file)
                print(json.dumps(data, indent=2))
                #flattened = jsonld.flatten(data)
                #print(json.dumps(flattened, indent=2))
                #compacted = jsonld.compact(data, context)
                #print(json.dumps(compacted, indent=2))

                #expanded = jsonld.expand(compacted)
                #print(json.dumps(expanded, indent=2))
            except json.decoder.JSONDecodeError as e:
                print(e)
    elif path.is_dir():
        print("Expecting file but got a directory. Aborting...")
        typer.Abort()
    elif not path.exists():
        print(f"Unable to find any metadata file at the path: \"{path}\"")


@app.command("dataset")
def validate_dataset(path: Path = typer.Argument(..., help="Path to the Dataset metadata in JSON/JSON-LD format")):
    if path.is_file():
        # content = path.read_text();
        # print(f"File content: {content}")
        file_extensions = [".json", ".jsonld"]
        # abort if correct file format is not submitted
        if not path.suffix in file_extensions:
            print(f"Only {file_extensions} file types are allowed. Please try again.")
            typer.Abort()
        else:
            try:
                dataset_file = open(path)
                dataset_metadata = json.load(dataset_file)
                dataset = Dataset(**dataset_metadata)
            except ValueError as e:
                raise e
    elif path.is_dir():
        print("Expecting file but got a directory. Aborting...")
        typer.Abort()
    elif not path.exists():
        print(f"Unable to find any metadata file at the path: \"{path}\"")


@app.command("software")
def validate_software(path: Path = typer.Argument(..., help="Path to the Software metadata in JSON/JSON-LD format")):
    if path.is_file():
        # content = path.read_text();
        # print(f"File content: {content}")
        file_extensions = [".json", ".jsonld"]
        # abort if correct file format is not submitted
        if not path.suffix in file_extensions:
            print(f"Only {file_extensions} file types are allowed. Please try again.")
            typer.Abort()
        else:
            try:
                software_file = open(path)
                software_metadata = json.load(software_file)
                try:
                    software = Software(**software_metadata)
                except ValidationError as e:
                    print(e)
            except ValueError as e:
                raise e
    elif path.is_dir():
        print("Expecting file but got a directory. Aborting...")
        typer.Abort()
    elif not path.exists():
        print(f"Unable to find any metadata file at the path: \"{path}\"")


@app.command("computation")
def validate_computation(path: Path):
    pass


if __name__ == "__main__":
    app()

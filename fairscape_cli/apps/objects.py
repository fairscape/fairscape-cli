import typer
from pathlib import Path
from pydantic import ValidationError
from fairscape_cli.apps.models import (
    Dataset,
    Software,
    Computation
)
import shutil

app = typer.Typer()


@app.command("dataset")
def add_dataset(
    guid: str = typer.Option(...),
    name: str = typer.Option(...),
    author: str = typer.Option(...),
    description: str = typer.Option(...),
    datePublished: str = typer.Option(...),
    version: str = typer.Option(...),
    associatedPublication: str = typer.Option(...),
    additionalDocumentation: Optional[List[str]] = typer.Option([]),
    dataFormat: str = typer.Option(...),
    generatedBy: Optional[List[str]] = typer.Option([]),
    derivedFrom: Optional[List[str]] = typer.Option([]),
    usedBy: Optional[List[str]] = typer.Option([]),
    sourcePath: Path = typer.Option(...),
    destinationPath: Path = typer.Option(...)
):
    
    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if !Path("ro-crate-metadata.json").exists():
        typer.secho("ro-crate-metadata.json not found")
        typer.secho("execute rocrate add commands from within the rocrate directory")
        typer.Exit()

    # TODO check that destination path is in the rocrate

    # check if the source file exists 
    if !sourcePath.exists():
        typer.secho(f"sourcePath: {sourcePath} Doesn't Exist")
        typer.Exit() 

    # copy the file into the destinationPath
    shutil.copy(sourcePath, destinationPath)
         

    # initilize the model with the required properties
    try:
        dataset_model = Dataset(   
            **{
            "@id": guid,
            "@type": "https://w3id.org/EVI#Dataset",
            "author": author,
            "description": description,
            "datePublished": datePublished,
            "version": version,
            "associatedPublication": associatedPublication,
            "additionalDocumentation": additionalDocumentation,
            "format": dataFormat,
            "generatedBy": generatedBy,
            "derivedFrom": derivedFrom,
            "usedBy": usedBy,
            "contentUrl": "file://" + destinationPath
            }
        )

    except ValidationError as e:
        typer.secho("Dataset Validation Error")
        typer.secho(e)
        typer.Exit()

    # TODO add to cache

    # open the ro-crate-metadata.json
    with open("ro-crate-metadata.json", "r") as rocrate_metadata_file:
        rocrate_metadata = json.load(rocrate_metadata_file)

    # TODO check if the file is redundant
 
    # add to the @graph
    rocrate_metadata['@graph'].append(dataset_model.dict(by_alias=True))
    
    # overwrite the ro-crate-metadata.json file
    with open("ro-crate-metadata.json", "w") as f:
        json.dump(rocrate_metadata, f, indent=2)

    typer.secho("Added Dataset")
    typer.secho(
        json.dumps(dataset_model.json(by_alias=True), indent=2)
    )


@app.command("software")
def add_software(
    guid: str = typer.Option(...),
    name: str = typer.Option(...),
    author: str = typer.Option(...),
    version: str = typer.Option(...),
    description: str = typer.Option(...),
    associatedPublication: str = typer.Option(...),
    additionalDocumentation: List[str] = typer.Option([]),
    format: str = typer.Option(...),
    usedByComputation: Optional[List[str]] = typer.Option([]),
    sourcePath: Path = typer.Option(...),
    destinationPath: Path = typer.Option(...)
):

    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if !Path("ro-crate-metadata.json").exists():
        typer.secho("ro-crate-metadata.json not found")
        typer.secho("execute rocrate add commands from within the rocrate directory")
        typer.Exit()

    # TODO check that destination path is in the rocrate

    # check if the source file exists 
    if !sourcePath.exists():
        typer.secho(f"sourcePath: {sourcePath} Doesn't Exist")
        typer.Exit() 

    # copy the file into the destinationPath
    shutil.copy(sourcePath, destinationPath)


    # initilize the model with the required properties
    try:
        software_model = Software(   
            **{
            "@id": guid,
            "@type": "https://w3id.org/EVI#Software",
            "name": name,
            "author": author,
            "dateModified": dateModified,
            "description": description,
            "version": version,
            "associatedPublication": associatedPublication,
            "additionalDocumentation": additionalDocumentation,
            "format": dataFormat,
            "usedByComputation": usedByComputation,
            "contentUrl": "file://" + destinationPath
            }
        )

    except ValidationError as e:
        typer.secho("Software Metadata Validation Error")
        typer.secho(e)
        typer.Exit()

    # TODO add to cache

    # open the ro-crate-metadata.json
    with open("ro-crate-metadata.json", "r") as rocrate_metadata_file:
        rocrate_metadata = json.load(rocrate_metadata_file)

    # TODO check if the file is redundant
 
    # add to the @graph
    rocrate_metadata['@graph'].append(software_model.dict(by_alias=True))
    
    # overwrite the ro-crate-metadata.json file
    with open("ro-crate-metadata.json", "w") as f:
        json.dump(rocrate_metadata, f, indent=2)

    typer.secho("Added software")
    typer.secho(
        json.dumps(software_model.json(by_alias=True), indent=2)
    )




@app.command("computation")
def add_computation(
    guid: str = typer.Option(...),
    name: str = typer.Option(...),
    runBy: str = typer.Option(...),
    description: str = typer.Option(...),
    associatedPublication: Optional[str] = typer.Option(""),
    additionalDocumentation: Optional[str] = typer.Option(""),
    usedSoftware: str = typer.Option(...),
    usedDataset: str = typer.Option(...),
    calledBy: Optional[str] = typer.Option(""),
    generated: str = typer.Option(...)

):

    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if !Path("ro-crate-metadata.json").exists():
        typer.secho("ro-crate-metadata.json not found")
        typer.secho("execute rocrate add commands from within the rocrate directory")
        typer.Exit()


    # initilize the model with the required properties
    try:
        computation_model = Computation(   
            **{
            "@id": guid,
            "@type": "https://w3id.org/EVI#Computation",
            "name": name,
            "runBy": runBy,
            "description": description,
            "associatedPublication": associatedPublication,
            "additionalDocumentation": additionalDocumentation,
            "usedSoftware": usedSoftware,
            "usedDataset": usedDataset,
            "generated": str,
            }
        )

    except ValidationError as e:
        typer.secho("Computation Metadata Validation Error")
        typer.secho(e)
        typer.Exit()


    # open the ro-crate-metadata.json
    with open("ro-crate-metadata.json", "r") as rocrate_metadata_file:
        rocrate_metadata = json.load(rocrate_metadata_file)

    # TODO check if the file is redundant
 
    # add to the @graph
    rocrate_metadata['@graph'].append(computation_model.dict(by_alias=True))
    
    # overwrite the ro-crate-metadata.json file
    with open("ro-crate-metadata.json", "w") as f:
        json.dump(rocrate_metadata, f, indent=2)

    typer.secho("Added Computation")
    typer.secho(
        json.dumps(computation_model.json(by_alias=True), indent=2)
    )



if __name__ == "__main__":
    app()

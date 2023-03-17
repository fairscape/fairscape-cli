import typer
from pathlib import Path
from typing import Optional, List
from pydantic import ValidationError
from fairscape_cli.apps.models import (
    Dataset,
    Software,
    Computation
)
import json
import shutil

app = typer.Typer()


@app.command("dataset")
def add_dataset(
    rocrate_path: Path = typer.Option(...),
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
    
    metadata_path = rocrate_path / "ro-crate-metadata.json"
    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if metadata_path.exists() != True:
        typer.secho(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        typer.Exit()

    # TODO check that destination path is in the rocrate

    # check if the source file exists 
    if sourcePath.exists() != True:
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
            "name": name,
            "description": description,
            "datePublished": datePublished,
            "version": version,
            "associatedPublication": associatedPublication,
            "additionalDocumentation": additionalDocumentation,
            "format": dataFormat,
            "generatedBy": generatedBy,
            "derivedFrom": derivedFrom,
            "usedBy": usedBy,
            "contentUrl": "file://" + str(destinationPath)
            }
        )

        # open the ro-crate-metadata.json
        with metadata_path.open("r") as rocrate_metadata_file:
            rocrate_metadata = json.load(rocrate_metadata_file)

        # TODO check if the file is redundant
     
        # add to the @graph
        rocrate_metadata['@graph'].append(dataset_model.dict(by_alias=True))
        
        # overwrite the ro-crate-metadata.json file
        with metadata_path.open("w") as f:
            json.dump(rocrate_metadata, f, indent=2)

        typer.secho("Added Dataset")
        typer.secho(
            json.dumps(dataset_model.json(by_alias=True), indent=2)
        )


    except ValidationError as e:
        typer.secho("Dataset Validation Error")
        typer.secho(e)
        typer.Exit()

    # TODO add to cache



@app.command("software")
def add_software(
    rocrate_path: Path = typer.Option(...),
    guid: str = typer.Option(...),
    name: str = typer.Option(...),
    author: str = typer.Option(...),
    version: str = typer.Option(...),
    description: str = typer.Option(...),
    associatedPublication: str = typer.Option(...),
    additionalDocumentation: List[str] = typer.Option([]),
    fileFormat: str = typer.Option(...),
    usedByComputation: Optional[List[str]] = typer.Option([]),
    sourcePath: Path = typer.Option(...),
    destinationPath: Path = typer.Option(...)
):


    metadata_path = rocrate_path / "ro-crate-metadata.json"
    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if metadata_path.exists() != True:
        typer.secho(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        typer.Exit()

    # TODO check that destination path is in the rocrate

    # check if the source file exists 
    if sourcePath.exists() != True:
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
            "format": fileFormat,
            "usedByComputation": usedByComputation,
            "contentUrl": "file://" + str(destinationPath)
            }
        )

        # open the ro-crate-metadata.json
        with metadata_path.open("r") as rocrate_metadata_file:
            rocrate_metadata = json.load(rocrate_metadata_file)

        # TODO check if the file is redundant
     
        # add to the @graph
        rocrate_metadata['@graph'].append(software_model.dict(by_alias=True))
        
        # overwrite the ro-crate-metadata.json file
        with metadata_path.open("w") as f:
            json.dump(rocrate_metadata, f, indent=2)

        typer.secho("Added Software")
        typer.secho(
            json.dumps(software_model.json(by_alias=True), indent=2)
        )


    except ValidationError as e:
        typer.secho("Software Validation Error")
        typer.secho(e)
        typer.Exit()





@app.command("computation")
def add_computation(
    rocrate_path: Path = typer.Option(...),
    guid: str = typer.Option(...),
    name: str = typer.Option(...),
    run_by: str = typer.Option(...),
    date_created: str = typer.Option(...),
    description: str = typer.Option(...),
    associatedPublication: Optional[str] = typer.Option(""),
    additionalDocumentation: Optional[str] = typer.Option(""),
    usedSoftware: List[str] = typer.Option(...),
    usedDataset: List[str] = typer.Option(...),
    calledBy: Optional[str] = typer.Option(""),
    generated: List[str] = typer.Option(...)
):

    metadata_path = rocrate_path / "ro-crate-metadata.json"
    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if metadata_path.exists() != True:
        typer.secho(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        typer.Exit()

    # initilize the model with the required properties
    try:
        computation_model = Computation(   
            **{
            "@id": guid,
            "@type": "https://w3id.org/EVI#Computation",
            "name": name,
            "runBy": run_by,
            "dateCreated": date_created,
            "description": description,
            "associatedPublication": associatedPublication,
            "additionalDocumentation": additionalDocumentation,
            "usedSoftware": usedSoftware,
            "usedDataset": usedDataset,
            "generated": generated,
            }
        )

        # open the ro-crate-metadata.json
        with metadata_path.open("r") as rocrate_metadata_file:
            rocrate_metadata = json.load(rocrate_metadata_file)

        # TODO check if the file is redundant
     
        # add to the @graph
        graph_metadata = rocrate_metadata.get('@graph', [])
        graph_metadata.append(computation_model.dict(by_alias=True))
        rocrate_metadata['@graph'] = graph_metadata
        
        # overwrite the ro-crate-metadata.json file
        with metadata_path.open("w") as rocrate_metadata_file:
            json.dump(rocrate_metadata, rocrate_metadata_file, indent=2)

        typer.secho("Added Computation")
        typer.secho(
            json.dumps(computation_model.json(by_alias=True), indent=2)
        )


    except ValidationError as e:
        typer.secho("Computation Validation Error")
        typer.secho(e)
        typer.Exit()




if __name__ == "__main__":
    app()

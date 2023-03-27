import typer
from pathlib import Path
import fairscape_cli.apps.objects
import shutil
import json

app = typer.Typer()
# subcommand
app.add_typer(fairscape_cli.apps.objects.app, name="add")


@app.command("create")
def create_crate(
    guid: str = typer.Option(...),
    name: str = typer.Option(...),
    organization_id: str = typer.Option(...),
    project_id: str = typer.Option(...),
    path: Path = typer.Option(...)
):

    
    # create a empty folder at the specified path
    try:
        path.mkdir(exist_ok=False)
    
    except FileExistsError:
        typer.secho("Path Already Exists")
        typer.Exit()

    # initilize ro-crate-metadata.json
    ro_crate_metadata_path = path / 'ro-crate-metadata.json'
    ro_crate_metadata_ark = guid + "/ro-crate-metadata.json"

    rocrate_metadata = {
        "@id": guid,
        "@context": {
            "EVI": "https://w3id.org/EVI#",
            "@vocab": "https://schema.org/"
        },
        "@type": "Dataset",
        "name": name,
        "isPartOf": [
            {
                "@id": organization_id,
                "@type": "Organization"
            },
            {
                "@id": project_id,
                "@type": "Project"
            }
        ],
        "@graph": [
            {
                "@id": ro_crate_metadata_ark,
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": guid},
                "isPartOf": {"@id": guid},
                "contentUrl": 'file://' + str(ro_crate_metadata_path),
            }
        ]  
    }


    with ro_crate_metadata_path.open(mode="w") as metadata_file:
        json.dump(rocrate_metadata, metadata_file, indent=2)
    
    typer.secho(f"Created RO Crate at {path}")

    # TODO add metadata to cache




@app.command("hash")
def compute_hash(rocrate_path: Path = typer.Option(...)):
    
    # look at the rocrate path
    pathlib.ls(ro_crate_path)

    # read in the ro-crate-metadata.json
    ro_crate_metadata_path = rocrate_path / 'ro-crate-metadata.json'
    with open(ro_crate_metadata_path, 'r') as ro_crate_metadata:
        metadata = json.load(ro_crate_metadata)

    # TODO validation step here

    # for everything in the ro-crate-metadata.json @graph

    metadata_graph = metadata.get("@graph", [])

    hash_metadata = {}

    for content in metadata_graph:
        
        if content.get("@type") == "Dataset":
            # look at the contentUrl
        
            # compute hash
            sha256_sum = 0
            hash_metadata[content['@id']] = sha256_sum

            continue

        if content.get("@type") == "Computation":
            pass

        if content.get("@type") == "Software":
            # if there is a local file uri then hash it
            pass 

        


@app.command("package")
def package_rocrate(
    input_path: Path = typer.Option(...),
    output_path: Path = typer.Option(...)
    ):

    # check that there is an ro crate at the input directory
    
    shutil.make_archive(output_filename, 'gzip', input_path)
    # zip up the entire folder
    


@app.command()
def delete(
    path: str,
    force: bool = typer.Option(..., prompt="Confirm to delete RO crate")
):
    if force:
        print(f"deleting ro crate: {path}")
    else:
        print("cancelling deletion")


if __name__ == "__main__":
    app()

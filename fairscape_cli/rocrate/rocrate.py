import click

# RO Crate 

@click.group('rocrate')
def rocrate():
    pass

# RO Crate Subcommands

@rocrate.command('hash')
def hash():
    pass

@rocrate.command('validate')
def validate():
    pass

@rocrate.command('zip')
def zip():
    pass

@rocrate.command('create')
@click.option()
def create(
    guid: str,
    name: str,
    organization_id: str,
    project_id: str,
    path: Path, 
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




# RO Crate add subcommands

@rocrate.group('add')
def add():
    pass

@add.command('software')
def software():
    pass

@add.command('dataset')
def dataset():
    pass

@add.command('computation')
def computation():
    pass


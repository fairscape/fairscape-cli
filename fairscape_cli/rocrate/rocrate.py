import click
import pathlib

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
@click.option('-g', '--guid', required=True, type=str)
@click.option('-n', '--name', required=True, type=str)
@click.option('-org', '--organization-guid', required=True, type=str)
@click.option('-proj', '--project-guid', required=True, type=str)
@click.argument('path', type=click.Path(exists=False, path_type=pathlib.Path))
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
        click.echo("ERROR: ROCrate Path Already Exists")
        click.Abort()

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
   
    click.echo(f"Created RO Crate at {path}")

    # TODO add metadata to cache


# RO Crate add subcommands

@rocrate.group('add')
def add():
    pass

@add.command('software')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=True)
@click.option('--name', required=True)
@click.option('--author', required=True)
@click.option('--version', required=True)
@click.option('--description', required=True)
@click.option('--file-format', required=True)
@click.option('--source-path', required=True)
@click.option('--destination-path', required=True)
@click.option('--date-modified', requred=False)
@click.option('--used-by-computation', required=False)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
def software(
    rocrate_path: Path,
    guid: str,
    name: str,
    author: str,
    version: str,
    description: str, 
    file_format: str,
    source_path: str,
    destination_path: str,
    date_modified: str,
    used_by_computation: Optional[List[str]],
    associated_publication: Optional[str],
    additional_documentation: Optional[str],
):

    metadata_path = rocrate_path / "ro-crate-metadata.json"

    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    # TODO check that destination path is in the rocrate

    # check if the source file exists 

    source_filepath = Path(source_path)
    if source_filpath.exists() != True:
        click.echo(f"sourcePath: {source_path} Doesn't Exist")
        click.Abort() 

    # copy the file into the destinationPath
    shutil.copy(Path(source_path), Path(destination_path)


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

            "dateModified": date_modified,
            "description": description,
            "version": version,
            "associatedPublication": associated_publication,
            "additionalDocumentation": additional_documentation,
            "format": file_format,
            "usedByComputation": used_by_computation,
            "contentUrl": "file://" + str(destination_path)
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

        click.echo("Added Software")
        click.echo(
            json.dumps(software_model.json(by_alias=True), indent=2)
        )

    except ValidationError as e:
        click.echo("Software Validation Error")
        click.echo(e)
        click.Abort()


@add.command('dataset')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=True)
@click.option('--name', required=True)
@click.option('--author', required=True)
@click.option('--version', required=True)
@click.option('--datePublished', required=True)
@click.option('--version', required=True)
@click.option('--description', required=True)
@click.option('--data-format', required=True)
@click.option('--source-filepath', required=True)
@click.option('--destination-filepath', required=True)
@click.option('--used-by', required=False)
@click.option('--derived-from', required=False)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
@add.command('dataset')
@click.option('rocrate')
def dataset(
    rocrate_path: Path,
    guid: str,
    name: str,
    author: str,
    description: str,
    datePublished: str,
    version: str,
    associated_publication: str,
    additional_documentation: Optional[List[str]],
    data_format: str,
    generated_by: Optional[List[str]],
    derived_from: Optional[List[str]],
    used_by: Optional[List[str]],
    source_filepath: str,
    destination_filepath: str
):


    metadata_path = rocrate_path / "ro-crate-metadata.json"
    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file

    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    # TODO check that destination path is in the rocrate
    destination_path = Path(destination_filepath)

    # check if the source file exists 
    source_path = Path(source_filepath) 
    if source_path.exists() != True:
        click.echo(f"sourcePath: {sourcePath} Doesn't Exist")
        clic.Abort()

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
            "datePublished": date_published,
            "version": version,
            "associatedPublication": associated_publication,
            "additionalDocumentation": additional_documentation,
            "format": data_format,
            "generatedBy": generated_by,
            "derivedFrom": derived_from,
            "usedBy": used_by,
            "contentUrl": "file://" + str(destination_path)
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

        click.echo("Added Software")
        click.echo(
            json.dumps(software_model.json(by_alias=True), indent=2)
        )

    except ValidationError as e:
        click.echo("Dataset Validation Error")
        click.echo(e)
        click.Abort()

    # TODO add to cache


@add.command('computation')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=True)
@click.option('--name', required=True)
@click.option('--run-by', required=True)
@click.option('--called-by', required=True)
@click.option('--date-created', required=True)
@click.option('--version', required=True)
@click.option('--description', required=True)
@click.option('--used-software', required=True)
@click.option('--used-dataset', required=True)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
def computation(
    rocrate_path: Path,
    guid: str,
    name: str,
    run_by: str,
    date_created: str,
    description: str,
    used_software: List[str],
    used_dataset: List[str],
    called_by: Optional[str],
    generated: List[str] 
    associated_publication: Optional[str],
    additional_documentation: Optional[str]
):

    metadata_path = rocrate_path / "ro-crate-metadata.json"
    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

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



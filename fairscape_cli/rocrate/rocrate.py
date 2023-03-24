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
<<<<<<< HEAD
        click.echo("ERROR: ROCrate Path Already Exists")
        click.Abort()
=======
        typer.secho("Path Already Exists")
        typer.Exit()
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f

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
    
<<<<<<< HEAD
    click.echo(f"Created RO Crate at {path}")
=======
    typer.secho(f"Created RO Crate at {path}")
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f

    # TODO add metadata to cache




<<<<<<< HEAD
##########################
# RO Crate add subcommands
##########################
def add_element_ro_crate():
    pass
=======
# RO Crate add subcommands
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f

@rocrate.group('add')
def add():
    pass

@add.command('software')
<<<<<<< HEAD
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
=======
def software(
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
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f

    # TODO check that destination path is in the rocrate

    # check if the source file exists 
<<<<<<< HEAD
    source_filepath = Path(source_path)
    if source_filpath.exists() != True:
        click.echo(f"sourcePath: {source_path} Doesn't Exist")
        click.Abort() 

    # copy the file into the destinationPath
    shutil.copy(Path(source_path), Path(destination_path)
=======
    if sourcePath.exists() != True:
        typer.secho(f"sourcePath: {sourcePath} Doesn't Exist")
        typer.Exit() 

    # copy the file into the destinationPath
    shutil.copy(sourcePath, destinationPath)
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f
         

    # initilize the model with the required properties
    try:
        software_model = Software(   
            **{
            "@id": guid,
            "@type": "https://w3id.org/EVI#Software",
            "name": name,
            "author": author,
<<<<<<< HEAD
            "dateModified": date_modified,
            "description": description,
            "version": version,
            "associatedPublication": associated_publication,
            "additionalDocumentation": additional_documentation,
            "format": file_format,
            "usedByComputation": used_by_computation,
            "contentUrl": "file://" + str(destination_path)
=======
            "dateModified": dateModified,
            "description": description,
            "version": version,
            "associatedPublication": associatedPublication,
            "additionalDocumentation": additionalDocumentation,
            "format": fileFormat,
            "usedByComputation": usedByComputation,
            "contentUrl": "file://" + str(destinationPath)
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f
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

<<<<<<< HEAD
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
=======
        typer.secho("Added Software")
        typer.secho(
            json.dumps(software_model.json(by_alias=True), indent=2)
        )


    except ValidationError as e:
        typer.secho("Software Validation Error")
        typer.secho(e)
        typer.Exit()

@add.command('dataset')
@click.option('rocrate')
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f
def dataset(
    rocrate_path: Path,
    guid: str,
    name: str,
    author: str,
<<<<<<< HEAD
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
=======
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
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f
):


    metadata_path = rocrate_path / "ro-crate-metadata.json"
    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file

    if metadata_path.exists() != True:
<<<<<<< HEAD
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    # TODO check that destination path is in the rocrate
    destination_path = Path(destination_filepath)

    # check if the source file exists 
    source_path = Path(source_filepath) 
    if source_path.exists() != True:
        click.echo(f"sourcePath: {sourcePath} Doesn't Exist")
        clic.Abort()
=======
        typer.secho(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        typer.Exit()

    # TODO check that destination path is in the rocrate

    # check if the source file exists 
    if sourcePath.exists() != True:
        typer.secho(f"sourcePath: {sourcePath} Doesn't Exist")
        typer.Exit() 
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f

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
<<<<<<< HEAD
            "datePublished": date_published,
            "version": version,
            "associatedPublication": associated_publication,
            "additionalDocumentation": additional_documentation,
            "format": data_format,
            "generatedBy": generated_by,
            "derivedFrom": derived_from,
            "usedBy": used_by,
            "contentUrl": "file://" + str(destination_path)
=======
            "datePublished": datePublished,
            "version": version,
            "associatedPublication": associatedPublication,
            "additionalDocumentation": additionalDocumentation,
            "format": dataFormat,
            "generatedBy": generatedBy,
            "derivedFrom": derivedFrom,
            "usedBy": usedBy,
            "contentUrl": "file://" + str(destinationPath)
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f
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

<<<<<<< HEAD
        click.echo("Added Software")
        click.echo(
            json.dumps(software_model.json(by_alias=True), indent=2)
        )

    except ValidationError as e:
        click.echo("Dataset Validation Error")
        click.echo(e)
        click.Abort()

=======
        typer.secho("Added Dataset")
        typer.secho(
            json.dumps(dataset_model.json(by_alias=True), indent=2)
        )


    except ValidationError as e:
        typer.secho("Dataset Validation Error")
        typer.secho(e)
        typer.Exit()
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f

    # TODO add to cache


@add.command('computation')
<<<<<<< HEAD
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
    additional_documentation: Optional[str],
=======
def computation():
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
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f
):

    metadata_path = rocrate_path / "ro-crate-metadata.json"
    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if metadata_path.exists() != True:
<<<<<<< HEAD
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()
=======
        typer.secho(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        typer.Exit()
>>>>>>> 1485a85a0b25f8bf5bfa8104d0733c3789646e0f

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



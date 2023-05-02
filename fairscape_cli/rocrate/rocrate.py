import click
import pathlib
import shutil
import json
from pydantic import ValidationError

from fairscape_cli.models import (
    Dataset,
    Software,
    Computation
)

from fairscape_cli.rocrate.utils import (
    generate_id,
    inside_crate 
)

from typing import (
    List,
    Optional,
    Union
)
 

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
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--name', required=True, type=str, prompt = "ROCrate Name (e.g. B2AI_ROCRATE)")
@click.option('--organization-name', required=True, type=str, prompt = "Organization Name")
@click.option('--project-name', required=True, type=str, prompt = "Project Name")
@click.argument('crate-path', type=click.Path(exists=False, path_type=pathlib.Path))
def create(
    guid: str,
    name: str,
    organization_name: str,
    project_name: str,
    crate_path: pathlib.Path, 
): 
    '''
    '''


    organization_guid = f"ark:/{organization_name.replace(' ', '_')}"
    project_guid = organization_guid + f"/{project_name.replace(' ', '_')}"

    if guid == "":
        guid = project_guid + f"/{name.replace(' ', '_')}"

    # create a empty folder at the specified path
    try:
        crate_path.mkdir(exist_ok=False)
    
    except FileExistsError:
        click.echo("ERROR: ROCrate Path Already Exists")
        click.Abort()

    # initilize ro-crate-metadata.json
    ro_crate_metadata_path = crate_path / 'ro-crate-metadata.json'
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
                "@id": organization_guid,
                "@type": "Organization",
                "name": organization_name
            },
            {
                "@id": project_guid,
                "@type": "Project",
                "name": project_name
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
    
    click.echo(f"Created RO Crate at {crate_path}")
    click.echo(json.dumps(rocrate_metadata, indent=2))

    # TODO add metadata to cache




##########################
# RO Crate add subcommands
##########################

def add_element_ro_crate(element: Union[Dataset,Computation,Software], ro_crate: pathlib.Path):
    pass

# RO Crate add subcommands
@rocrate.group('add')
def add():
    pass


@add.command('software')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--name',    required=True, prompt = "Software Name")
@click.option('--author',  required=True, prompt = "Author Name")
@click.option('--version', required=True, prompt = "Software Version")
@click.option('--description', required = True, prompt = "Software Description")
@click.option('--file-format', required = True, prompt = "File Format of Software")
@click.option('--url',     required = False)
@click.option('--source-filepath', required=False)
@click.option('--destination-filepath', required=False)
@click.option('--date-modified', required=False)
@click.option('--used-by-computation', required=False, multiple=True)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
def software(
    rocrate_path: pathlib.Path,
    guid: str,
    name: str,
    author: str,
    version: str,
    description: str, 
    file_format: str,
    url: str,
    source_filepath: str,
    destination_filepath: str,
    date_modified: str,
    used_by_computation: Optional[List[str]],
    associated_publication: Optional[str],
    additional_documentation: Optional[str]
):


    
    metadata_path = rocrate_path / "ro-crate-metadata.json"

    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    if guid == "":
        guid = generate_id(metadata_path, name, "Software")


    # initilize the model with the required properties
    try:

        # if moving local files
        if source_filepath !=  "" and destination_filepath != "":

            # check if the source file exists 
            source_path = pathlib.Path(source_filepath)
            destination_path = pathlib.Path(destination_filepath)

            if source_path.exists() != True:
                click.echo(f"sourcePath: {source_path} Doesn't Exist")
                click.Abort() 
            
            # TODO check that destination path is in the rocrate

            software_model = Software(   
                **{
                "@id": guid,
                "@type": "https://w3id.org/EVI#Software",
                "url": url,
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

            # copy the file into the destinationPath
            shutil.copy(source_path, destination_path)

        else:
            software_model = Software(   
                **{
                "@id": guid,
                "@type": "https://w3id.org/EVI#Software",
                "url": url,
                "name": name,
                "author": author,
                "dateModified": date_modified,
                "description": description,
                "version": version,
                "associatedPublication": associated_publication,
                "additionalDocumentation": additional_documentation,
                "format": file_format,
                "usedByComputation": used_by_computation
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
            json_object = json.dumps(rocrate_metadata, indent=2)
            f.write(json_object)

        click.echo(guid)


    except ValidationError as e:
        click.echo("Software Validation Error")
        click.echo(e)
        click.Abort()


    # TODO add to cache


@add.command('dataset')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=False, default="", type=str)
@click.option('--name', required=True, prompt="Dataset Name")
@click.option('--url', required=False)
@click.option('--author', required=True, prompt="Dataset Author")
@click.option('--version', required=True, prompt="Dataset Version")
@click.option('--date-published', required=True, prompt="Date Published")
@click.option('--description', required=True, prompt="Dataset Description")
@click.option('--data-format', required=True, prompt="Data Format i.e. (csv, tsv)")
@click.option('--source-filepath', required=False)
@click.option('--destination-filepath', required=False)
@click.option('--used-by', required=False, multiple=True)
@click.option('--derived-from', required=False, multiple=True)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
def dataset(
    rocrate_path: pathlib.Path,
    guid: str,
    name: str,
    url: str,
    author: str,
    description: str,
    date_published: str,
    version: str,
    associated_publication: Optional[str],
    additional_documentation: Optional[List[str]],
    data_format: str,
    source_filepath: str,
    destination_filepath: str,
    derived_from: Optional[List[str]],
    used_by: Optional[List[str]],
):


    metadata_path = rocrate_path / "ro-crate-metadata.json"
    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file

    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    if guid == "":
        guid = generate_id(metadata_path, name, "Dataset")


    
    # initilize the model with the required properties
    try:

        if destination_filepath != "" and source_filepath != "":
            

            # TODO check that destination path is in the rocrate
            destination_path = pathlib.Path(destination_filepath)
            source_path = pathlib.Path(source_filepath) 

            # check if the source file exists 
            if source_path.exists() != True:
                click.echo(f"sourcePath: {sourcePath} Doesn't Exist")
                clic.Abort()

            dataset_model = Dataset(   
                **{
                "@id": guid,
                "@type": "https://w3id.org/EVI#Dataset",
                "url": url,
                "author": author,
                "name": name,
                "description": description,
                "datePublished": date_published,
                "version": version,
                "associatedPublication": associated_publication,
                "additionalDocumentation": additional_documentation,
                "format": data_format,
                "derivedFrom": derived_from,
                "usedBy": used_by,
                "contentUrl": "file://" + str(destination_path)
                }
            )

            # copy the file into the destinationPath
            shutil.copy(source_path, destination_path)

        else:
            dataset_model = Dataset(   
                **{
                "@id": guid,
                "@type": "https://w3id.org/EVI#Dataset",
                "url": url,
                "author": author,
                "name": name,
                "description": description,
                "datePublished": date_published,
                "version": version,
                "associatedPublication": associated_publication,
                "additionalDocumentation": additional_documentation,
                "format": data_format,
                "derivedFrom": derived_from,
                "usedBy": used_by
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

        click.echo(guid)

    except ValidationError as e:
        click.echo("Software Validation Error")
        click.echo(e)
        click.Abort()
    

    # TODO add to cache
    


@add.command('computation')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=False, default="", type=str, show_default=False)
@click.option('--name', required=True, prompt="Computation Name")
@click.option('--run-by', required=True, prompt="Computation Run By")
@click.option('--command', required=False, prompt="Command")
@click.option('--date-created', required=True, prompt="Date Created")
@click.option('--description', required=True, prompt="Computation Description")
@click.option('--used-software', required=False, multiple=True)
@click.option('--used-dataset', required=False, multiple=True)
@click.option('--generated', required=False, multiple=True)
def computation(
    rocrate_path: pathlib.Path,
    guid: str,
    name: str,
    run_by: str,
    command: Optional[Union[str, List[str]]],
    date_created: str,
    description: str,
    used_software,
    used_dataset,
    generated
):

    metadata_path = rocrate_path / "ro-crate-metadata.json"
    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    if guid == "":
        guid = generate_id(metadata_path, name, "Computation")

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
            "usedSoftware": used_software,
            "usedDataset": used_dataset,
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

        click.echo(guid)
        #click.echo("Added Computation")
        #click.echo(
        #    json.dumps(computation_model.dict(by_alias=True), indent=2)
        #)


    except ValidationError as e:
        click.echo("Computation Validation Error")
        click.echo(e)
        click.Abort()


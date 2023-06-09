import click
import pathlib
import shutil
import json
from pydantic import ValidationError

from fairscape_cli.models import (
    Dataset,
    Software,
    Computation,
    DatasetContainer,
    ROCrate
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

@rocrate.command('init')
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--name', required=True, type=str, prompt = "ROCrate Name (e.g. B2AI_ROCRATE)")
@click.option('--organization-name', required=True, type=str, prompt = "Organization Name")
@click.option('--project-name', required=True, type=str, prompt = "Project Name")
def init(
    guid: str,
    name: str,
    organization_name: str,
    project_name: str
):

    passed_crate =ROCrate(
        guid=guid,
        name=name,
        organizationName = organization_name,
        projectName = project_name,
        path = pathlib.Path.cwd(), 
        metadataGraph = []
    )

    try:
        passed_crate.initCrate()
    except Exception as e:
        click.echo(f"ERROR: {str(e)}")
    

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
    '''Create an ROCrate in a new path specified by the crate-path argument
    '''
    
    organization_guid = f"ark:/{organization_name.replace(' ', '_')}"
    project_guid = organization_guid + f"/{project_name.replace(' ', '_')}"

    if guid != "":
        crate_guid = guid
    else:
        crate_guid = project_guid + f"/{name.replace(' ', '_')}"

    passed_crate = ROCrate(
        guid=crate_guid,
        name=name,
        organizationName = organization_name,
        projectName = project_name,
        path = crate_path, 
        metadataGraph = []
    )
    
    passed_crate.createCrateFolder()
    passed_crate.initCrate()

    click.echo(crate_guid)




##########################
# RO Crate add subcommands
##########################

def add_element_ro_crate(
    element: Union[Dataset,Computation,Software], 
    ro_crate: pathlib.Path
    ):
    pass


@rocrate.group('register')
def register():
    pass

@register.command('software')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--name',    required=True, prompt = "Software Name")
@click.option('--author',  required=True, prompt = "Author Name")
@click.option('--version', required=True, prompt = "Software Version")
@click.option('--description', required = True, prompt = "Software Description")
@click.option('--file-format', required = True, prompt = "File Format of Software")
@click.option('--url',     required = False)
@click.option('--date-modified', required=False)
@click.option('--filepath', required=False)
@click.option('--used-by-computation', required=False, multiple=True)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
def registerSoftware(
    rocrate_path: pathlib.Path,
    guid: str,
    name: str,
    author: str,
    version: str,
    description: str, 
    file_format: str,
    url: str,
    date_modified: str,
    filepath: str,
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

    crate = ROCrate(path=metadata_path)


    software_metadata = {
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
            # sanitize new line characters for multiple inputs
            "usedByComputation": [
                computation.strip("\n") for computation in used_by_computation
            ],
        }

    if filepath != "" and filepath is not None:
            software_metadata["contentUrl"] = f"file://{str(filepath)}" 
    else:
        # if filepath is null and url is null
        # raise an error
        if url == "" or url is None:
            click.echo("Software Validation Error: url and filepath cannot both be null")
            click.Abort()

    try:
        software_model = Software(**software_metadata)

    except ValidationError as e:
        click.echo("Software Validation Error")
        click.echo(e)
        click.Abort()
        
    crate.registerSoftware(software_model)
 
    click.echo(guid)



@register.command('dataset')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=False, default="", type=str)
@click.option('--name', required=True, prompt="Dataset Name")
@click.option('--url', required=False)
@click.option('--author', required=True, prompt="Dataset Author")
@click.option('--version', required=True, prompt="Dataset Version")
@click.option('--date-published', required=True, prompt="Date Published")
@click.option('--description', required=True, prompt="Dataset Description")
@click.option('--data-format', required=True, prompt="Data Format i.e. (csv, tsv)")
@click.option('--filepath', required=True)
@click.option('--used-by', required=False, multiple=True)
@click.option('--derived-from', required=False, multiple=True)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
def registerDataset(
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
    filepath: str,
    derived_from: Optional[List[str]],
    used_by: Optional[List[str]],
):
    
    metadata_path = rocrate_path / "ro-crate-metadata.json"

    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    crate = ROCrate(path=metadata_path)

    dataset_metadata = {
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

            # sanitize input lists of newline breaks
            "derivedFrom": [
                derived.strip("\n") for derived in derived_from
            ],
            "usedBy": [
                used.strip("\n") for used in used_by 
            ],
            }

    if filepath != "" and filepath is not None:
        dataset_metadata["contentUrl"] = f"file://{str(filepath)}" 


    try:
        dataset_model = Dataset(**dataset_metadata)

    except ValidationError as e:
        click.echo("Dataset Validation Error")
        click.echo(e)
        click.Abort()
    
    crate.registerDataset(dataset_model)
 
    click.echo(guid)


@register.command('computation')
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

    
    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    metadata_path = rocrate_path / "ro-crate-metadata.json"
    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    crate = ROCrate(path=metadata_path)

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
            # sanitize input lists of newline breaks
            "usedSoftware": [
                software.strip("\n") for software in used_software
            ],
            "usedDataset": [
                dataset.strip("\n") for dataset in used_dataset 
            ],
            "generated": [
                output.strip("\n") for output in generated
            ],
            }
        )
    except ValidationError as e:
        click.echo("Computation Validation Error")
        click.echo(e)
        click.Abort()

    crate.registerComputation(computation_model)
    
    click.echo(guid)
        #click.echo("Added Computation")
        #click.echo(
        #    json.dumps(computation_model.dict(by_alias=True), indent=2)
        #)



@register.command('dataset-container')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=False, default="", type=str, show_default=False)
@click.option('--name', required=True, prompt="DatasetContainer Name")
@click.option('--description', required=True)
@click.option('--has-part', required=False, multiple=True)
@click.option('--is-part-of', required=False, multiple=True)
def registerDatasetContainer(
    rocrate_path, 
    guid, 
    name, 
    description, 
    has_part, 
    is_part_of
):
    '''Add a DatasetContainer to the ROCrate.

    A Dataset Container is used for grouping sets of datasets. Only Datasets may be added to the dataset container hasPart property.
    '''
   
    # check that crate exists 
    metadata_path = rocrate_path / "ro-crate-metadata.json"
    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    crate = ROCrate(path=metadata_path)

    if guid == "":
        guid = generate_id(metadata_path, name, "Dataset")

    # validate the provided metadata
    try: 
        dscontainer = DatasetContainer(**{
            "guid": guid,
            "name": name,
            "description": description,
            "hasPart": has_part,
            "isPartOf": is_part_of
        })

        crate.registerObject(dscontainer) 
        click.echo(guid)

    except ValidationError as e:
        click.echo("DatasetContainer Validation Error")
        click.echo(e)
        click.Abort()

    


###############################################################################
#                             Dataset Container Commands                      #
###############################################################################

@rocrate.group('dataset-container')
def datasetContainer():
    pass

@datasetContainer.command('pop')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--dataset-container', required=True)
@click.option('--dataset-guid', required=True, multiple=True)
def popDatasetContainer(rocrate_path, dataset_container, dataset_guid):
    """ Add dataset elements to the specified dataset container
    """
    # check that crate exists 
    metadata_path = rocrate_path / "ro-crate-metadata.json"
    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    crate = ROCrate(path=metadata_path)

    # TODO check that dataset container is guid

    # TODO check that dataset guid is guid

    try:
        crate.popDatasetContainer(dataset_container, dataset_guid)

    except Exception as e:
        click.echo("Error poping element from DatasetContainer")
        click.Abort()


@datasetContainer.command('push')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--dataset-container', required=True)
@click.option('--dataset-guid', required=True, multiple=True)
def pushDatasetContainer(rocrate_path, dataset_container, dataset_guid):
    """ Add dataset elements to the specified dataset container
    """

    # check that crate exists 
    metadata_path = rocrate_path / "ro-crate-metadata.json"
    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    crate = ROCrate(path=metadata_path)

    # TODO check that dataset container is guid

    # TODO check that dataset guid is guid

    try:
        crate.pushDatasetContainer(dataset_container, dataset_guid)

    except Exception as e:
        click.echo("Error pushing element to DatasetContainer")
        click.Abort()

    


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
@click.option('--source-filepath', required=True)
@click.option('--destination-filepath', required=True)
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

    source_path = pathlib.Path(source_filepath)
    destination_path = pathlib.Path(destination_filepath)
    
    metadata_path = rocrate_path / "ro-crate-metadata.json"

    # check if you are in the rocrate path
    # ro-crate-metadata.json should be a local file
    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    if guid == "":
        guid = generate_id(metadata_path, name, "Software")

    
    crate = ROCrate(path=metadata_path)


    try:
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
            # sanitize multiple inputs
            "usedByComputation": [
                computation.strip("\n") for computation in used_by_computation
            ],
            "contentUrl": "file://" + str(destination_path)
            }
        )

    except ValidationError as e:
        click.echo("Software Validation Error")
        click.echo(e)
        click.Abort()

    crate.registerSoftware(software_model)

    try:
        crate.copyObject(source_filepath, destination_filepath)
    except:
        click.echo("Failed to Copy Software")
        click.echo(e)
        click.Abort()

    click.echo(guid)

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

    source_path = pathlib.Path(source_filepath)
    destination_path = pathlib.Path(destination_filepath)

    if metadata_path.exists() != True:
        click.echo(f"Cannot Find RO-Crate Metadata: {metadata_path}")
        click.Abort()

    if guid == "":
        guid = generate_id(metadata_path, name, "Dataset")


    crate = ROCrate(path=metadata_path)
    
    try:
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
            "derivedFrom": [
                derived.strip("\n") for derived in derived_from
            ],
            "usedBy": [
                used.strip("\n") for used in used_by 
            ],
            "contentUrl": "file://" + str(destination_path)
            }
        )

    except ValidationError as e:
        click.echo("Software Validation Error")
        click.echo(e)
        click.Abort()

    crate.registerDataset(dataset_model)
    crate.copyObject(source_filepath, destination_filepath)

    click.echo(guid) 

    # TODO add to cache
    





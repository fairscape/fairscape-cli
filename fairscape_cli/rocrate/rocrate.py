import click
import pathlib
import shutil
import json
from pydantic import ValidationError
from datetime import datetime

from fairscape_cli.models import (
    Dataset,
    GenerateDataset,
    Software,
    GenerateSoftware,
    Computation,
    GenerateComputation,
    ROCrate,
    ReadROCrateMetadata,
    BagIt
)

from typing import (
    List,
    Optional,
    Union
)



# Click Commands
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
@click.option('--name', required=True, type=str) # prompt= "ROCrate Name (e.g. B2AI_ROCRATE)")
@click.option('--organization-name', required=True, type=str) #prompt = "Organization Name")
@click.option('--project-name', required=True, type=str) # prompt = "Project Name")
@click.option('--description', required=True, type=str)
@click.option('--keywords', required=True, multiple=True, type=str)
def init(
    guid,
    name,
    organization_name,
    project_name,
    description,
    keywords
):
    passed_crate = ROCrate(
        guid=guid,
        name=name,
        organizationName = organization_name,
        projectName = project_name,
        description = description,
        keywords = keywords,
        path = pathlib.Path.cwd(), 
        metadataGraph = []
    )

    try:
        passed_crate.initCrate()
        click.echo(passed_crate.guid)
    except Exception as e:
        click.echo(f"ERROR: {str(e)}")
    

@rocrate.command('create')
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--name', required=True, type=str)  #prompt="ROCrate Name (e.g. B2AI_ROCRATE)")
@click.option('--organization-name', required=True, type=str) #prompt= "Organization Name")
@click.option('--project-name', required=True, type=str) #, prompt= "Project Name")
@click.option('--description', required=True, type=str)
@click.option('--keywords', required=True, multiple=True, type=str)
@click.argument('rocrate-path', type=click.Path(exists=False, path_type=pathlib.Path))
def create(
    guid,
    name,
    organization_name,
    project_name,
    description,
    keywords,
    rocrate_path, 
): 
    '''Create an ROCrate in a new path specified by the rocrate-path argument
    '''
    
    passed_crate = ROCrate(
        guid=guid,
        name=name,
        organizationName = organization_name,
        projectName = project_name,
        description = description,
        keywords = keywords,
        path = rocrate_path, 
        metadataGraph = []
    )
    
    passed_crate.createCrateFolder()
    passed_crate.initCrate()

    click.echo(passed_crate.guid)




##########################
# RO Crate register subcommands
##########################
@rocrate.group('register')
def register():
    pass

@register.command('software')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--name',    required=True) # , prompt = "Software Name")
@click.option('--author',  required=True) # , prompt = "Author Name")
@click.option('--version', required=True) #, prompt = "Software Version")
@click.option('--description', required = True) #, prompt = "Software Description")
@click.option('--keywords', required=True, multiple=True)
@click.option('--file-format', required = True) # , prompt = "File Format of Software")
@click.option('--url', required = False)
@click.option('--date-modified', required=False)
@click.option('--filepath', required=False)
@click.option('--used-by-computation', required=False, multiple=True)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
def registerSoftware(
    rocrate_path: pathlib.Path,
    guid,
    name,
    author,
    version,
    description, 
    keywords,
    file_format,
    url,
    date_modified,
    filepath,
    used_by_computation,
    associated_publication,
    additional_documentation
    ):
    
    try:
        crateInstance = ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        click.Abort()
    
    try:
        software_instance = GenerateSoftware(
                guid=guid,
                url= url,
                name=name,
                version=version,
                keywords=keywords,
                file_format=file_format,
                description=description,
                author= author,
                associated_publication=associated_publication,
                additional_documentation=additional_documentation,
                date_modified=date_modified,
                used_by_computation=used_by_computation,
                filepath=filepath,
                crate_path =rocrate_path 
        )
    
        crateInstance.registerSoftware(software_instance)
        click.echo(guid)

    except ValidationError as e:
        click.echo("Software Validation Error")
        click.echo(e)
        click.Abort()
        


@register.command('dataset')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=False, default="", type=str)
@click.option('--name', required=True) #, prompt="Dataset Name")
@click.option('--url', required=False)
@click.option('--author', required=True) #, prompt="Dataset Author")
@click.option('--version', required=True) #, prompt="Dataset Version")
@click.option('--date-published', required=True) #, prompt="Date Published")
@click.option('--description', required=True) #, prompt="Dataset Description")
@click.option('--keywords', required=True, multiple=True)
@click.option('--data-format', required=True) # , prompt="Data Format i.e. (csv, tsv)")
@click.option('--filepath', required=True)
@click.option('--used-by', required=False, multiple=True)
@click.option('--derived-from', required=False, multiple=True)
@click.option('--schema', required=False, type=str)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
def registerDataset(
    rocrate_path: pathlib.Path,
    guid: str,
    name: str,
    url: str,
    author: str, 
    version: str,
    date_published: str,
    description: str,
    keywords: List[str],
    data_format: str,
    filepath: str,
    used_by: Optional[List[str]],
    derived_from: Optional[List[str]],
    schema: str,
    associated_publication: Optional[str],
    additional_documentation: Optional[List[str]],
):
    
    try:
        crate_instance = ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        click.Abort()
    
    try:
        dataset_instance = GenerateDataset(
            guid=guid,
            url=url,
            author=author,
            name=name,
            description=description,
            keywords=keywords,
            datePublished=date_published,
            version=version,
            associatedPublication=associated_publication,
            additionalDocumentation=additional_documentation,
            format=data_format,
            schema=schema,
            derivedFrom=derived_from,
            usedBy=used_by,
            cratePath=rocrate_path
        )

    except ValidationError as e:
        click.echo("Dataset Validation Error")
        click.echo(e)
        click.Abort()
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        click.Abort()
    
    crate_instance.registerDataset(dataset_instance)
 
    click.echo(dataset_instance.guid)


@register.command('computation')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=False, default="", type=str, show_default=False)
@click.option('--name', required=True) #, prompt="Computation Name")
@click.option('--run-by', required=True) #, prompt="Computation Run By")
@click.option('--command', required=False) #, prompt="Enter the command", prompt_required=False)
@click.option('--date-created', required=True) #, prompt="Date Created")
@click.option('--description', required=True) #, prompt="Computation Description")
@click.option('--keywords', required=True, multiple=True)
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
    keywords: List[str],
    used_software,
    used_dataset,
    generated
):

    try:
        crateInstance = ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        click.Abort()


    try:
        computationModel = GenerateComputation(
            name=name,
            run_by=run_by,
            command= command,
            dateCreated= date_created,
            description= description,
            keywords= keywords,
            usedSoftware= used_software,
            usedDataset= used_dataset,
            generated= generated
        )

        crateInstance.registerComputation(computationModel)
        click.echo(computationModel.guid)

    except ValidationError as e:
        click.echo("Computation Validation Error")
        click.echo(e)
        click.Abort()



# RO Crate add subcommands
@rocrate.group('add')
def add():
    pass


@add.command('software')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--name',    required=True) #, prompt = "Software Name")
@click.option('--author',  required=True) #, prompt = "Author Name")
@click.option('--version', required=True) #, prompt = "Software Version")
@click.option('--description', required = True) #, prompt = "Software Description")
@click.option('--keywords', required=True, multiple=True)
@click.option('--file-format', required = True) #, prompt = "File Format of Software")
@click.option('--url',     required = False)
@click.option('--source-filepath', required=True)
@click.option('--destination-filepath', required=True)
@click.option('--date-modified', required=True)
@click.option('--used-by-computation', required=False, multiple=True)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
def software(
    rocrate_path,
    guid,
    name,
    author,
    version,
    description, 
    keywords,
    file_format,
    url,
    source_filepath,
    destination_filepath,
    date_modified,
    used_by_computation,
    associated_publication,
    additional_documentation
):
 
    try:
        crateInstance = ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        click.Abort()

    

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
            "keywords": keywords,
            "version": version,
            "associatedPublication": associated_publication,
            "additionalDocumentation": additional_documentation,
            "format": file_format,
            # sanitize multiple inputs
            "usedByComputation": [
                computation.strip("\n") for computation in used_by_computation
            ],
            "contentUrl": "file://" + str(pathlib.Path(destination_filepath))
            }
        )
        crateInstance.registerSoftware(software_model)

    except ValidationError as e:
        click.echo("Software Validation Error")
        click.echo(e)
        click.Abort()


    try:
        crateInstance.copyObject(source_filepath, destination_filepath)

    except Exception as e:
        click.echo("Failed to Copy Software")
        click.echo(e)
        click.Abort()

    click.echo(software_model.guid)

    # TODO add to cache


@add.command('dataset')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', required=False, default="", type=str)
@click.option('--name', required=True) #, prompt="Dataset Name")
@click.option('--url', required=False)
@click.option('--author', required=True) #, prompt="Dataset Author")
@click.option('--version', required=True) #, prompt="Dataset Version")
@click.option('--date-published', required=True) #, prompt="Date Published")
@click.option('--description', required=True) #, prompt="Dataset Description")
@click.option('--keywords', required=True, multiple=True)
@click.option('--data-format', required=True) #, prompt="Data Format i.e. (csv, tsv)")
@click.option('--source-filepath', required=True)
@click.option('--destination-filepath', required=True)
@click.option('--used-by', required=False, multiple=True)
@click.option('--derived-from', required=False, multiple=True)
@click.option('--schema', required=False, type=str)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
def dataset(
    rocrate_path: pathlib.Path,
    guid: str,
    name: str,
    url: str,
    author: str,
    version: str,
    date_published: str,
    description: str,
    keywords: List[str],
    data_format: str,
    source_filepath: str,
    destination_filepath: str,
    used_by: Optional[List[str]],
    derived_from: Optional[List[str]],
    schema: str,
    associated_publication: Optional[str],
    additional_documentation: Optional[List[str]],
):

    try:
        crateInstance = ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        click.Abort()

    
    try:
        dataset_model = Dataset.model_validate({
            "@id": guid,
            "@type": "https://w3id.org/EVI#Dataset",
            "url": url,
            "author": author,
            "name": name,
            "description": description,
            "keywords": keywords,
            "datePublished": date_published,
            "version": version,
            "associatedPublication": associated_publication,
            "additionalDocumentation": additional_documentation,
            "format": data_format,
            "schema": schema,
            "derivedFrom": [
                derived.strip("\n") for derived in derived_from
            ],
            "usedBy": [
                used.strip("\n") for used in used_by 
            ],
            "schema": schema,
            "contentUrl": "file://" + str(destination_filepath)
            })

        crateInstance.registerDataset(dataset_model)
        crateInstance.copyObject(source_filepath, destination_filepath)

    except ValidationError as e:
        click.echo("Software Validation Error")
        click.echo(e)
        click.Abort()


    click.echo(guid) 

    # TODO add to cache
    



@rocrate.group('package')
def package():
    pass

@package.command('bagit')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.argument('bagit-path', type=click.Path(exists=False, path_type=pathlib.Path))
@click.option('--Source-Organization', required=True) #, prompt="Source-Organization")
@click.option('--Organization-Address', required=True) #, prompt="Organization-Address")
@click.option('--Contact-Name', required=True) #, prompt="Contact-Name")
@click.option('--Contact-Phone', required=True) #, prompt="Contact-Phone")
@click.option('--Contact-Email', required=True) #, prompt="Contact-Email")
@click.option('--External-Description', required=True) #, prompt="External-Description")
#@click.option('--Bagging-Date', required=False)
#@click.option('--External-Identifier', required=False, prompt="External-Identifier")
#@click.option('--Payload-Oxum', required=False, prompt="Payload-Oxum")
#@click.option('--Bag-Group-Identifier', required=False, prompt="Bag-Group-Identifier")
#@click.option('--Bag-Count', required=False, prompt="Bag-Count")
#@click.option('--Internal-Sender-Identifier', required=False, prompt="Internal-Sender-Identifier")
@click.option('--Internal-Sender-Description', required=False, prompt="Internal-Sender-Description")
def bagit(
    rocrate_path: pathlib.Path,
    bagit_path: pathlib.Path,
    source_organization: str,
    organization_address: str,
    contact_name: str,
    contact_phone: str,
    contact_email: str,
    external_description: str
):
    bagit = BagIt(
        **{    
            "rocrate_path": rocrate_path,
            "bagit_path": bagit_path,
            "source_organization": source_organization,
            "organization_address": organization_address,
            "contact_name": contact_name,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "external_description": external_description,
            "bagging_date": datetime.now().strftime("%m/%d/%Y")
        }
    )
    
    
    
    click.echo(click.style("BagIt path", fg="green") + f": {bagit_path}")

    bagit.create_bagit_directory()
    
    # Create bag.txt
    bagit.create_bagit_declaration()
    click.echo(click.style("Bag Declaration", fg="green") + f": {bagit_path}/bag.txt")
    
    # Populate /data/ directory 
    bagit.create_payload_directory()
    click.echo(click.style("Payload Directory", fg="green") + f": {bagit_path}/data/")


    # Create bag-info.txt
    bagit.create_bagit_metadata()
    click.echo(click.style("Bag Metadata", fg="green") + f": {bagit_path}/bag-info.txt")
    
    # Create manifest-sha256.txt
    bagit.create_payload_manifest_sha256()
    click.echo(click.style("Payload Manifest", fg="green") + f": {bagit_path}/manifest-sha256.txt")
    # Create tagmanifest-sha256.txt
    bagit.create_tag_manifest_sha256()
    click.echo(click.style("Tag Manifest", fg="green") + f": {bagit_path}/tagmanifest-sha256.txt")
    
    # Create manifest-sha512.txt
    bagit.create_payload_manifest_sha512()
    click.echo(click.style("Payload Manifest", fg="green") + f": {bagit_path}/manifest-sha512.txt")
    # Create tagmanifest-sha512.txt
    bagit.create_tag_manifest_sha512()
    click.echo(click.style("Tag Manifest", fg="green") + f": {bagit_path}/tagmanifest-sha512.txt")
    
    # Create manifest-md5.txt
    bagit.create_payload_manifest_md5()
    click.echo(click.style("Payload Manifest", fg="green") + f": {bagit_path}/manifest-md5.txt")
    # Create tagmanifest-md5.txt
    bagit.create_tag_manifest_md5()
    click.echo(click.style("Tag Manifest", fg="green") + f": {bagit_path}/tagmanifest-md5.txt")

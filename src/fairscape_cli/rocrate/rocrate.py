import click
import pathlib
import shutil
import json
from pydantic import ValidationError
from datetime import datetime

from fairscape_cli.config import (
    NAAN
)
from fairscape_cli.models.utils import (
    FileNotInCrateException, 
    GenerateDatetimeSquid
)
from fairscape_cli.models import (
    Dataset,
    GenerateDataset,
    Software,
    GenerateSoftware,
    Computation,
    GenerateComputation,
    GenerateROCrate,
    ROCrate,
    ReadROCrateMetadata,
    AppendCrate,
    CopyToROCrate,
    BagIt,
    generateSummaryStatsElements
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
    """Invoke operations on Research Object Crate (RO-CRate).
    """
    pass


@rocrate.command('init')
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--name', required=True, type=str) 
@click.option('--organization-name', required=True, type=str) 
@click.option('--project-name', required=True, type=str) 
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
    """ Initalize a rocrate in the current working directory by instantiating a ro-crate-metadata.json file.
    """
    
    passed_crate = GenerateROCrate(
        guid=guid,
        name=name,
        organizationName = organization_name,
        projectName = project_name,
        description = description,
        keywords = keywords,
        path = pathlib.Path.cwd(), 
    )

    click.echo(passed_crate.guid)
    

@rocrate.command('create')
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--name', required=True, type=str)
@click.option('--organization-name', required=True, type=str) 
@click.option('--project-name', required=True, type=str) 
@click.option('--description', required=True, type=str)
@click.option('--keywords', required=True, multiple=True, type=str)
@click.argument('rocrate-path', type=click.Path(exists=False, path_type=pathlib.Path))
def create(
    rocrate_path, 
    guid,
    name,
    organization_name,
    project_name,
    description,
    keywords
): 
    '''Create an ROCrate in a new path specified by the rocrate-path argument
    '''

    passed_crate = GenerateROCrate(
        guid=guid,
        name=name,
        organizationName = organization_name,
        projectName = project_name,
        description = description,
        keywords = keywords,
        path = rocrate_path
    )
    
    click.echo(passed_crate.guid)




##########################
# RO Crate register subcommands
##########################
@rocrate.group('register')
def register():
    """ Add a metadata record to the RO-Crate for a Dataset, Software, or Computation
    """
    pass

@register.command('software')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None)
@click.option('--name',    required=True) 
@click.option('--author',  required=True) 
@click.option('--version', required=True) 
@click.option('--description', required = True)
@click.option('--keywords', required=True, multiple=True)
@click.option('--file-format', required = True) 
@click.option('--url', required = False)
@click.option('--date-modified', required=False)
@click.option('--filepath', required=False)
@click.option('--used-by-computation', required=False, multiple=True)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
@click.pass_context
def registerSoftware(
    ctx,
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
    """Register a Software metadata record to the specified ROCrate
    """    
    try:
        crateInstance = ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {str(exc)}")
        ctx.exit(code=1)
    
    try:
        software_instance = GenerateSoftware(
                guid= guid,
                url= url,
                name=name,
                version=version,
                keywords=keywords,
                fileFormat=file_format,
                description=description,
                author= author,
                associatedPublication=associated_publication,
                additionalDocumentation=additional_documentation,
                dateModified=date_modified,
                usedByComputation=used_by_computation,
                filepath=filepath,
                cratePath =rocrate_path 
        )
    
        AppendCrate(cratePath = rocrate_path, elements=[software_instance])
        click.echo(software_instance.guid)

    except FileNotInCrateException as e:
        click.echo(f"ERROR: {str(e)}")
        ctx.exit(code=1)

    except ValidationError as e:
        click.echo("ERROR: Software Validation Failure")
        click.echo(e)
        ctx.exit(code=1)
        
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        ctx.exit(code=1)


@register.command('dataset')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None)
@click.option('--name', required=True)
@click.option('--url', required=False)
@click.option('--author', required=True) 
@click.option('--version', required=True) 
@click.option('--date-published', required=True)
@click.option('--description', required=True)
@click.option('--keywords', required=True, multiple=True)
@click.option('--data-format', required=True) 
@click.option('--filepath', required=True)
@click.option('--summary-statistics-filepath', required=False, type=click.Path(exists=True))
@click.option('--used-by', required=False, multiple=True)
@click.option('--derived-from', required=False, multiple=True)
@click.option('--generated-by', required=False, multiple=True)
@click.option('--schema', required=False, type=str)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
@click.pass_context
def registerDataset(
    ctx,
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
    summary_statistics_filepath: Optional[str],
    used_by: Optional[List[str]],
    derived_from: Optional[List[str]],
    generated_by: Optional[List[str]],
    schema: str,
    associated_publication: Optional[str],
    additional_documentation: Optional[List[str]],
):
    """Register Dataset object metadata with the specified RO-Crate"""    
    try:
        crate_instance = ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {str(exc)}")
        ctx.exit(code=1)
    
    try:
        # Generate main dataset GUID
        sq_dataset = GenerateDatetimeSquid()
        dataset_guid = guid if guid else f"ark:{NAAN}/dataset-{name.lower().replace(' ', '-')}-{sq_dataset}"

        summary_stats_guid = None
        elements = []
        
        # Handle summary statistics if provided
        if summary_statistics_filepath:
            summary_stats_guid, summary_stats_instance, computation_instance = generateSummaryStatsElements(
                name=name,
                author=author,
                keywords=keywords,
                date_published=date_published,
                version=version,
                associated_publication=associated_publication,
                additional_documentation=additional_documentation,
                schema=schema,
                dataset_guid=dataset_guid,
                summary_statistics_filepath=summary_statistics_filepath,
                crate_path=rocrate_path
            )
            elements.extend([computation_instance, summary_stats_instance])

        # Generate main dataset
        dataset_instance = GenerateDataset(
            guid=dataset_guid,
            url=url,
            author=author,
            name=name,
            description=description,
            keywords=keywords,
            datePublished=date_published,
            version=version,
            associatedPublication=associated_publication,
            additionalDocumentation=additional_documentation,
            dataFormat=data_format,
            schema=schema,
            derivedFrom=derived_from,
            generatedBy=generated_by,
            usedBy=used_by,
            filepath=filepath,
            cratePath=rocrate_path,
            summary_stats_guid=summary_stats_guid
        )
        
        elements.insert(0, dataset_instance)
        AppendCrate(cratePath=rocrate_path, elements=elements)
        click.echo(dataset_instance.guid)
    
    except FileNotInCrateException as e:
        click.echo(f"ERROR: {str(e)}")
        ctx.exit(code=1)

    except ValidationError as e:
        click.echo("Dataset Validation Error")
        click.echo(e)
        ctx.exit(code=1)

    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        ctx.exit(code=1)
 

@register.command('computation')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None)
@click.option('--name', required=True) 
@click.option('--run-by', required=True) 
@click.option('--command', required=False) 
@click.option('--date-created', required=True) 
@click.option('--description', required=True) 
@click.option('--keywords', required=True, multiple=True)
@click.option('--used-software', required=False, multiple=True)
@click.option('--used-dataset', required=False, multiple=True)
@click.option('--generated', required=False, multiple=True)
@click.pass_context
def computation(
    ctx,
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
    """Register a Computation with the specified RO-Crate
    """
    try:
        crateInstance = ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {str(exc)}")
        ctx.exit(code=1)


    try:
        computationInstance = GenerateComputation(
            guid=guid,
            name=name,
            runBy=run_by,
            command= command,
            dateCreated= date_created,
            description= description,
            keywords= keywords,
            usedSoftware= used_software,
            usedDataset= used_dataset,
            generated= generated
        )

        AppendCrate(cratePath=rocrate_path, elements=[computationInstance])
        click.echo(computationInstance.guid)

    except ValidationError as e:
        click.echo("Computation Validation Error")
        click.echo(e)
        ctx.exit(code=1)



# RO Crate add subcommands
@rocrate.group('add')
def add():
    """Add (transfer) object to RO-Crate and register object metadata.""" 
    pass


@add.command('software')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None)
@click.option('--name',    required=True) 
@click.option('--author',  required=True) 
@click.option('--version', required=True) 
@click.option('--description', required = True) 
@click.option('--keywords', required=True, multiple=True)
@click.option('--file-format', required = True)
@click.option('--url',     required = False)
@click.option('--source-filepath', required=True)
@click.option('--destination-filepath', required=True)
@click.option('--date-modified', required=True)
@click.option('--used-by-computation', required=False, multiple=True)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
@click.pass_context
def software(
    ctx,
    rocrate_path: pathlib.Path,
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
    """Add a Software and its corresponding metadata.
    """
    try:
        crateInstance = ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {str(exc)}")
        ctx.exit(code=1)

    
    try:
        CopyToROCrate(source_filepath, destination_filepath)

        software_instance = GenerateSoftware(
                guid=guid,
                url= url,
                name=name,
                version=version,
                keywords=keywords,
                fileFormat=file_format,
                description=description,
                author= author,
                associatedPublication=associated_publication,
                additionalDocumentation=additional_documentation,
                dateModified=date_modified,
                usedByComputation=used_by_computation,
                filepath=destination_filepath,
                cratePath =rocrate_path 
        )
    
        AppendCrate(cratePath = rocrate_path, elements=[software_instance])
        # copy file to rocrate
        click.echo(software_instance.guid)

    except ValidationError as e:
        click.echo("Software Validation Error")
        click.echo(e)
        ctx.exit(code=1)

    # TODO add to cache


@add.command('dataset')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None)
@click.option('--name', required=True) 
@click.option('--url', required=False)
@click.option('--author', required=True)
@click.option('--version', required=True) 
@click.option('--date-published', required=True) 
@click.option('--description', required=True) 
@click.option('--keywords', required=True, multiple=True)
@click.option('--data-format', required=True) 
@click.option('--source-filepath', required=True)
@click.option('--destination-filepath', required=True)
@click.option('--summary-statistics-source', required=False, type=click.Path(exists=True))
@click.option('--summary-statistics-destination', required=False, type=click.Path())
@click.option('--used-by', required=False, multiple=True)
@click.option('--derived-from', required=False, multiple=True)
@click.option('--generated-by', required=False, multiple=True)
@click.option('--schema', required=False, type=str)
@click.option('--associated-publication', required=False)
@click.option('--additional-documentation', required=False)
@click.pass_context
def dataset(
    ctx,
    rocrate_path: pathlib.Path,
    guid,
    name,
    url,
    author,
    version,
    date_published,
    description,
    keywords,
    data_format,
    source_filepath,
    destination_filepath,
    summary_statistics_source,
    summary_statistics_destination,
    used_by,
    derived_from,
    generated_by,
    schema,
    associated_publication,
    additional_documentation,
):
    """Add a Dataset file and its metadata to the RO-Crate."""
    try:
        crateInstance = ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {str(exc)}")
        ctx.exit(code=1)

    try:
        # Copy main dataset file
        CopyToROCrate(source_filepath, destination_filepath)
        
        # Generate main dataset GUID
        sq_dataset = GenerateDatetimeSquid()
        dataset_guid = guid if guid else f"ark:{NAAN}/dataset-{name.lower().replace(' ', '-')}-{sq_dataset}"

        summary_stats_guid = None
        elements = []
        
        # Handle summary statistics if provided
        if summary_statistics_source and summary_statistics_destination:
            # Copy summary statistics file
            CopyToROCrate(summary_statistics_source, summary_statistics_destination)
            
            # Generate summary statistics elements
            summary_stats_guid, summary_stats_instance, computation_instance = generateSummaryStatsElements(
                name=name,
                author=author,
                keywords=keywords,
                date_published=date_published,
                version=version,
                associated_publication=associated_publication,
                additional_documentation=additional_documentation,
                schema=schema,
                dataset_guid=dataset_guid,
                summary_statistics_filepath=summary_statistics_destination,
                crate_path=rocrate_path
            )
            elements.extend([computation_instance, summary_stats_instance])

        # Generate main dataset
        dataset_instance = GenerateDataset(
            guid=dataset_guid,
            url=url,
            author=author,
            name=name,
            description=description,
            keywords=keywords,
            datePublished=date_published,
            version=version,
            associatedPublication=associated_publication,
            additionalDocumentation=additional_documentation,
            dataFormat=data_format,
            schema=schema,
            derivedFrom=derived_from,
            generatedBy=generated_by,
            usedBy=used_by,
            filepath=destination_filepath,
            cratePath=rocrate_path,
            summary_stats_guid=summary_stats_guid
        )
        
        elements.insert(0, dataset_instance)
        AppendCrate(cratePath=rocrate_path, elements=elements)
        click.echo(dataset_instance.guid)

    except ValidationError as e:
        click.echo("Dataset Validation Error")
        click.echo(e)
        ctx.exit(code=1)

    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        ctx.exit(code=1)

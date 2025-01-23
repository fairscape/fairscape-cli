import click
import pathlib
import shutil
import json
from datetime import datetime
from typing import List, Optional, Union

from pydantic import ValidationError

from fairscape_cli.config import NAAN
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
from fairscape_cli.models.utils import (
    FileNotInCrateException,
    getDirectoryContents,
    getEntityFromCrate,
    run_command
)
from fairscape_cli.models import (
    # Core models
    Dataset,
    Software,
    Computation,
    ROCrate,
    ROCrateMetadata,
    BagIt,
    
    # Generator functions
    GenerateDataset,
    GenerateSoftware,
    GenerateComputation,
    GenerateROCrate,
    
    # RO Crate operations
    ReadROCrateMetadata,
    AppendCrate,
    CopyToROCrate,
    UpdateCrate,
    
    # Additional utilities
    generateSummaryStatsElements,
    registerOutputs
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
@click.option('--license', required=False, type=str, default="https://creativecommons.org/licenses/by/4.0/")
@click.option('--date-published', required=False, type=str)
def init(
   guid,
   name, 
   organization_name,
   project_name,
   description,
   keywords,
   license,
   date_published
):
   """ Initialize a rocrate in the current working directory by instantiating a ro-crate-metadata.json file.
   """
   passed_crate = GenerateROCrate(
       guid=guid,
       name=name,
       organizationName=organization_name,
       projectName=project_name,
       description=description,
       keywords=keywords,
       license=license,
       datePublished=date_published,
       path=pathlib.Path.cwd(),
   )
   click.echo(passed_crate.get("@id"))

@rocrate.command('create')
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--name', required=True, type=str)
@click.option('--organization-name', required=True, type=str)
@click.option('--project-name', required=True, type=str)
@click.option('--description', required=True, type=str)
@click.option('--keywords', required=True, multiple=True, type=str)
@click.option('--license', required=False, type=str, default="https://creativecommons.org/licenses/by/4.0/")
@click.option('--date-published', required=False, type=str)
@click.argument('rocrate-path', type=click.Path(exists=False, path_type=pathlib.Path))
def create(
   rocrate_path,
   guid,
   name,
   organization_name,
   project_name,
   description,
   keywords,
   license,
   date_published
):
   '''Create an ROCrate in a new path specified by the rocrate-path argument
   '''
   passed_crate = GenerateROCrate(
       guid=guid,
       name=name,
       organizationName=organization_name,
       projectName=project_name,
       description=description,
       keywords=keywords,
       license=license,
       datePublished=date_published,
       path=rocrate_path
   )
   click.echo(passed_crate.get("@id"))




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

@register.command('subrocrate')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.argument('subrocrate-path', type=click.Path(path_type=pathlib.Path))
@click.option('--guid', required=False, type=str, default="", show_default=False)
@click.option('--name', required=True, type=str)
@click.option('--organization-name', required=True, type=str)
@click.option('--project-name', required=True, type=str)
@click.option('--description', required=True, type=str)
@click.option('--keywords', required=True, multiple=True, type=str)
@click.pass_context
def subrocrate(
    ctx,
    rocrate_path: pathlib.Path,
    subrocrate_path: pathlib.Path,
    guid: str,
    name: str,
    organization_name: str,
    project_name: str,
    description: str,
    keywords: List[str]
):
    """Register a new RO-Crate within an existing RO-Crate directory.
    
    ROCRATE_PATH: Path to the parent RO-Crate
    SUBCRATE_PATH: Relative path within the parent RO-Crate where the subcrate should be created
    """
    try:
        # Read parent crate metadata
        parent_crate = ReadROCrateMetadata(rocrate_path)
        
        # Construct full path for subcrate
        full_subcrate_path = rocrate_path / subrocrate_path
        
        # Create subcrate
        subcrate = GenerateROCrate(
            guid=guid,
            name=name,
            organizationName=organization_name,
            projectName=project_name,
            description=description,
            keywords=keywords,
            path=full_subcrate_path
        )
        
        # Update parent crate to include reference to subcrate
        with (rocrate_path / 'ro-crate-metadata.json').open('r+') as f:
            parent_metadata = json.load(f)
            
            root_dataset = parent_metadata['@graph'][1]
            
            if 'hasPart' not in root_dataset:
                root_dataset['hasPart'] = []
            
            subcrate_ref = {
                "@id": subcrate['@id']
            }
            
            if not any(part.get('@id') == subcrate['@id'] for part in root_dataset['hasPart']):
                root_dataset['hasPart'].append(subcrate_ref)
            
            # Validate and write updated parent metadata
            ROCrateMetadata(**parent_metadata)
            f.seek(0)
            f.truncate()
            json.dump(parent_metadata, f, indent=2)
        
        click.echo(subcrate['@id'])
        
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
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

#################
# Summary Statistics
#################
@rocrate.command('compute-statistics')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--dataset-id', required=True, help='ID of dataset to compute statistics for')
@click.option('--software-id', required=True, help='ID of software to run')
@click.option('--command', required=True, help='Python command to execute (e.g. python)')
@click.pass_context
def compute_statistics(
    ctx,
    rocrate_path: pathlib.Path,
    dataset_id: str,
    software_id: str,
    command: str
):
    """Compute statistics for a dataset using specified software"""
    crate_instance = ReadROCrateMetadata(rocrate_path)
    initial_files = getDirectoryContents(rocrate_path)
    
    # Get original dataset info
    dataset_info = getEntityFromCrate(crate_instance, dataset_id)
    software_info = getEntityFromCrate(crate_instance, software_id)
    if not dataset_info or not software_info:
        raise ValueError(f"Dataset or software not found in crate")

    # Get original dataset author
    original_author = dataset_info.get("author", "Unknown")
    dataset_path = dataset_info.get("contentUrl", "").replace("file:///", "")
    software_path = software_info.get("contentUrl", "").replace("file:///", "")
    
    if not dataset_path or not software_path:
        raise ValueError("Dataset or software path not found")

    full_command = f"{command} {software_path} {dataset_path} {rocrate_path}"
    success, stdout, stderr = run_command(full_command)
    if not success:
        raise RuntimeError(f"Command failed: {stderr}")

    final_files = getDirectoryContents(rocrate_path)
    new_files = final_files - initial_files
    if not new_files:
        raise RuntimeError("No output files generated")

    computation_instance = GenerateComputation(
        guid=None,
        name=f"Statistics Computation for {dataset_id}",
        runBy="Fairscape-CLI",
        command=full_command,
        dateCreated=datetime.now().isoformat(),
        description=f"Generated statistics\nstdout:\n{stdout}\nstderr:\n{stderr}",
        keywords=["statistics"],
        usedSoftware=[software_id],
        usedDataset=[dataset_id],
        generated=[]
    )

    output_instances = registerOutputs(
        new_files=new_files,
        computation_id=computation_instance.guid,
        dataset_id=dataset_id,
        author=original_author
    )
    
    stats_output = [out.guid for out in output_instances]
    computation_instance.generated = stats_output

    if stats_output:
        # Update the original dataset metadata
        dataset_info["hasSummaryStatistics"] = stats_output
        # Generate a new Dataset instance with updated metadata
        updated_dataset = Dataset.model_validate(dataset_info)
        
        # Update the dataset in the crate and append new elements
        UpdateCrate(cratePath=rocrate_path, element=updated_dataset)
        AppendCrate(
            cratePath=rocrate_path,
            elements=[computation_instance] + output_instances
        )

    click.echo(computation_instance.guid)
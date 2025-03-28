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
    
    ROCrate,
    
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
    
    #Pep
    PEPtoROCrateMapper,
    
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
@click.option('--author', required=False, type=str, default="Unknown")
@click.option('--version', required=False, type=str, default="1.0")
@click.option('--associated-publication', required=False, type=str)
@click.option('--conditions-of-access', required=False, type=str)
@click.option('--copyright-notice', required=False, type=str)
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
def init(
    guid,
    name, 
    organization_name,
    project_name,
    description,
    keywords,
    license,
    date_published,
    author,
    version,
    associated_publication,
    conditions_of_access,
    copyright_notice,
    custom_properties
):
    """ Initialize a rocrate in the current working directory by instantiating a ro-crate-metadata.json file.
    """
    params = {
        "guid": guid,
        "name": name,
        "organizationName": organization_name,
        "projectName": project_name,
        "description": description,
        "keywords": keywords,
        "license": license,
        "datePublished": date_published,
        "author": author,
        "version": version,
        "associatedPublication": associated_publication,
        "conditionsOfAccess": conditions_of_access,
        "copyrightNotice": copyright_notice,
        "path": pathlib.Path.cwd()
    }
    
    # Process custom properties if provided
    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict):
                raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except json.JSONDecodeError:
            click.echo("ERROR: Invalid JSON in custom-properties")
            return
            
    passed_crate = GenerateROCrate(**params)
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
@click.option('--author', required=False, type=str, default="Unknown")
@click.option('--version', required=False, type=str, default="1.0")
@click.option('--associated-publication', required=False, type=str)
@click.option('--conditions-of-access', required=False, type=str)
@click.option('--copyright-notice', required=False, type=str)
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
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
    date_published,
    author,
    version,
    associated_publication,
    conditions_of_access,
    copyright_notice,
    custom_properties
):
    '''Create an ROCrate in a new path specified by the rocrate-path argument
    '''
    params = {
        "guid": guid,
        "name": name,
        "organizationName": organization_name,
        "projectName": project_name,
        "description": description,
        "keywords": keywords,
        "license": license,
        "datePublished": date_published,
        "author": author, 
        "version": version,
        "associatedPublication": associated_publication,
        "conditionsOfAccess": conditions_of_access,
        "copyrightNotice": copyright_notice,
        "path": rocrate_path
    }
    
    # Process custom properties if provided
    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict):
                raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except json.JSONDecodeError:
            click.echo("ERROR: Invalid JSON in custom-properties")
            return
            
    passed_crate = GenerateROCrate(**params)
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
@click.option('--guid', type=str, required=False, default=None, help='Identifier for the software (generated if not provided)')
@click.option('--name', required=True, help='Name of the software')
@click.option('--author', required=True, help='Author of the software') 
@click.option('--version', required=True, help='Version of the software') 
@click.option('--description', required=True, help='Description of the software')
@click.option('--keywords', required=True, multiple=True, help='Keywords for the software')
@click.option('--file-format', required=True, help='Format of the software (e.g., py, js)')
@click.option('--url', required=False, help='URL reference for the software')
@click.option('--date-modified', required=False, help='Last modification date of the software (ISO format)')
@click.option('--filepath', required=False, help='Path to the software file')
@click.option('--used-by-computation', required=False, multiple=True, help='Identifiers of computations that use this software')
@click.option('--associated-publication', required=False, help='Associated publication identifier')
@click.option('--additional-documentation', required=False, help='Additional documentation')
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
@click.pass_context
def registerSoftware(
    ctx,
    rocrate_path: pathlib.Path,
    guid: str,
    name: str,
    author: str, 
    version: str,
    description: str,
    keywords: List[str],
    file_format: str,
    url: Optional[str] = None,
    date_modified: Optional[str] = None,
    filepath: Optional[str] = None,
    used_by_computation: Optional[List[str]] = None,
    associated_publication: Optional[str] = None,
    additional_documentation: Optional[str] = None,
    custom_properties: Optional[str] = None,
):
    """Register a Software metadata record to the specified ROCrate
    
    This command registers software with the specified RO-Crate. It provides
    common options directly, but also supports custom properties through the
    --custom-properties option.
    
    Examples:
        fairscape rocrate register software ./my-crate --name "Analysis Script" --author "John Doe" ...
        
        # With custom properties:
        fairscape rocrate register software ./my-crate --name "Analysis Script" ... --custom-properties '{"license": "MIT", "programmingLanguage": "Python"}'
    """
    
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {str(exc)}")
        ctx.exit(code=1)
    
    try:
        custom_props = {}
        if custom_properties:
            try:
                custom_props = json.loads(custom_properties)
                if not isinstance(custom_props, dict):
                    raise ValueError("Custom properties must be a JSON object")
            except json.JSONDecodeError:
                click.echo("ERROR: Invalid JSON in custom-properties")
                ctx.exit(code=1)
        
        params = {
            "guid": guid,
            "name": name,
            "author": author,
            "description": description,
            "keywords": keywords,
            "version": version,
            "fileFormat": file_format,
            "filepath": filepath,
            "cratePath": rocrate_path,
        }
        
        if url:
            params["url"] = url
        if date_modified:
            params["dateModified"] = date_modified
        if used_by_computation:
            params["usedByComputation"] = used_by_computation
        if associated_publication:
            params["associatedPublication"] = associated_publication
        if additional_documentation:
            params["additionalDocumentation"] = additional_documentation
        
        params.update(custom_props)
        
        software_instance = GenerateSoftware(**params)
    
        AppendCrate(cratePath=rocrate_path, elements=[software_instance])
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
@click.option('--guid', type=str, required=False, default=None, help='Identifier for the dataset (generated if not provided)')
@click.option('--name', required=True, help='Name of the dataset')
@click.option('--author', required=True, help='Author of the dataset') 
@click.option('--version', required=True, help='Version of the dataset') 
@click.option('--description', required=True, help='Description of the dataset')
@click.option('--keywords', required=True, multiple=True, help='Keywords for the dataset')
@click.option('--data-format', required=True, help='Format of the dataset (e.g., csv, json)')
@click.option('--filepath', required=True, help='Path to the dataset file')
@click.option('--url', required=False, help='URL reference for the dataset')
@click.option('--date-published', required=False, help='Publication date of the dataset (ISO format)')
@click.option('--schema', required=False, help='Schema identifier for the dataset')
@click.option('--used-by', required=False, multiple=True, help='Identifiers of computations that use this dataset')
@click.option('--derived-from', required=False, multiple=True, help='Identifiers of datasets this one is derived from')
@click.option('--generated-by', required=False, multiple=True, help='Identifiers of computations that generated this dataset')
@click.option('--summary-statistics-filepath', required=False, type=click.Path(exists=True), help='Path to summary statistics file')
@click.option('--associated-publication', required=False, help='Associated publication identifier')
@click.option('--additional-documentation', required=False, help='Additional documentation')
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
@click.pass_context
def registerDataset(
    ctx,
    rocrate_path: pathlib.Path,
    guid: str,
    name: str,
    author: str, 
    version: str,
    description: str,
    keywords: List[str],
    data_format: str,
    filepath: str,
    url: Optional[str] = None,
    date_published: Optional[str] = None,
    schema: Optional[str] = None,
    used_by: Optional[List[str]] = None,
    derived_from: Optional[List[str]] = None,
    generated_by: Optional[List[str]] = None,
    summary_statistics_filepath: Optional[str] = None,
    associated_publication: Optional[str] = None,
    additional_documentation: Optional[str] = None,
    custom_properties: Optional[str] = None,
):
    """Register Dataset object metadata with the specified RO-Crate.
    
    This command registers a dataset with the specified RO-Crate. It provides
    common options directly, but also supports custom properties through the
    --custom-properties option.
    
    Examples:
        fairscape rocrate register dataset ./my-crate --name "My Dataset" --author "John Doe" ...
        
        # With custom properties:
        fairscape rocrate register dataset ./my-crate --name "My Dataset" ... --custom-properties '{"publisher": "Acme Corp", "license": "CC-BY-4.0"}'
    """
    
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {str(exc)}")
        ctx.exit(code=1)
    
    try:
        custom_props = {}
        if custom_properties:
            try:
                custom_props = json.loads(custom_properties)
                if not isinstance(custom_props, dict):
                    raise ValueError("Custom properties must be a JSON object")
            except json.JSONDecodeError:
                click.echo("ERROR: Invalid JSON in custom-properties")
                ctx.exit(code=1)
        
        params = {
            "guid": guid,
            "name": name,
            "author": author,
            "description": description,
            "keywords": keywords,
            "version": version,
            "format": data_format,
            "filepath": filepath,
            "cratePath": rocrate_path,
        }
        
        if url:
            params["url"] = url
        if date_published:
            params["datePublished"] = date_published
        if schema:
            params["schema"] = schema
        if used_by:
            params["usedBy"] = used_by
        if derived_from:
            params["derivedFrom"] = derived_from
        if generated_by:
            params["generatedBy"] = generated_by
        if associated_publication:
            params["associatedPublication"] = associated_publication
        if additional_documentation:
            params["additionalDocumentation"] = additional_documentation
        
        params.update(custom_props)
        
        summary_stats_guid = None
        elements = []
        
        if summary_statistics_filepath:
            summary_stats_guid, summary_stats_instance, computation_instance = generateSummaryStatsElements(
                name=name,
                author=author,
                keywords=keywords,
                date_published=date_published or "",
                version=version,
                associated_publication=associated_publication,
                additional_documentation=additional_documentation,
                schema=schema,
                dataset_guid=guid or "",
                summary_statistics_filepath=summary_statistics_filepath,
                crate_path=rocrate_path
            )
            elements.extend([computation_instance, summary_stats_instance])
            params["summary_stats_guid"] = summary_stats_guid

        dataset_instance = GenerateDataset(**params)
        
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
@click.option('--guid', type=str, required=False, default=None, help='Identifier for the computation (generated if not provided)')
@click.option('--name', required=True, help='Name of the computation')
@click.option('--run-by', required=True, help='Person or entity that ran the computation')
@click.option('--command', required=False, help='Command used to run the computation')
@click.option('--date-created', required=True, help='Date the computation was run (ISO format)')
@click.option('--description', required=True, help='Description of the computation')
@click.option('--keywords', required=True, multiple=True, help='Keywords for the computation')
@click.option('--used-software', required=False, multiple=True, help='Software identifiers used by this computation')
@click.option('--used-dataset', required=False, multiple=True, help='Dataset identifiers used by this computation')
@click.option('--generated', required=False, multiple=True, help='Dataset identifiers generated by this computation')
@click.option('--associated-publication', required=False, help='Associated publication identifier')
@click.option('--additional-documentation', required=False, help='Additional documentation')
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
@click.pass_context
def computation(
    ctx,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: str,
    run_by: str,
    command: Optional[Union[str, List[str]]],
    date_created: str,
    description: str,
    keywords: List[str],
    used_software: Optional[List[str]],
    used_dataset: Optional[List[str]],
    generated: Optional[List[str]],
    associated_publication: Optional[str] = None,
    additional_documentation: Optional[str] = None,
    custom_properties: Optional[str] = None,
):
    """Register a Computation with the specified RO-Crate
    
    This command registers a computation with the specified RO-Crate. It provides
    common options directly, but also supports custom properties through the
    --custom-properties option.
    
    Examples:
        fairscape rocrate register computation ./my-crate --name "Data Analysis" --run-by "John Doe" ...
        
        # With custom properties:
        fairscape rocrate register computation ./my-crate --name "Data Analysis" ... --custom-properties '{"environment": "Docker", "computingResource": "HPC"}'
    """
    try:
        crateInstance = ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {str(exc)}")
        ctx.exit(code=1)

    try:
        custom_props = {}
        if custom_properties:
            try:
                custom_props = json.loads(custom_properties)
                if not isinstance(custom_props, dict):
                    raise ValueError("Custom properties must be a JSON object")
            except json.JSONDecodeError:
                click.echo("ERROR: Invalid JSON in custom-properties")
                ctx.exit(code=1)
        
        params = {
            "guid": guid,
            "name": name,
            "runBy": run_by,
            "command": command,
            "dateCreated": date_created,
            "description": description,
            "keywords": keywords,
            "usedSoftware": used_software or [],
            "usedDataset": used_dataset or [],
            "generated": generated or []
        }
        
        if associated_publication:
            params["associatedPublication"] = associated_publication
        if additional_documentation:
            params["additionalDocumentation"] = additional_documentation
            
        params.update(custom_props)
        
        computationInstance = GenerateComputation(**params)

        AppendCrate(cratePath=rocrate_path, elements=[computationInstance])
        click.echo(computationInstance.guid)

    except ValidationError as e:
        click.echo("Computation Validation Error")
        click.echo(e)
        ctx.exit(code=1)
        
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
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
@click.option('--author', required=False, type=str, default="Unknown")
@click.option('--version', required=False, type=str, default="1.0")
@click.option('--license', required=False, type=str, default="https://creativecommons.org/licenses/by/4.0/")
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
    keywords: List[str],
    author: str,
    version: str,
    license: str
):
    """Register a new RO-Crate within an existing RO-Crate directory.
    
    ROCRATE_PATH: Path to the parent RO-Crate
    SUBCRATE_PATH: Relative path within the parent RO-Crate where the subcrate should be created
    """
    try:
        metadata = ReadROCrateMetadata(rocrate_path)
        root_metadata = metadata['@graph'][1]
        
        parent_author = root_metadata.get('author', author or "Unknown")
        parent_version = root_metadata.get('version', version or "1.0")
        parent_license = root_metadata.get('license', license)
        
        parent_crate = ROCrate(
            guid=root_metadata['@id'],
            metadataType=root_metadata.get('@type', ["Dataset", "https://w3id.org/EVI#ROCrate"]),
            name=root_metadata['name'],
            description=root_metadata['description'],
            keywords=root_metadata['keywords'],
            author=parent_author,
            version=parent_version,
            license=parent_license,
            isPartOf=root_metadata.get('isPartOf', []),
            hasPart=root_metadata.get('hasPart', []),
            path=rocrate_path
        )
        
        subcrate_id = parent_crate.create_subcrate(
            subcrate_path=subrocrate_path,
            guid=guid,
            name=name,
            description=description,
            keywords=keywords,
            organization_name=organization_name,
            project_name=project_name,
            author=author or parent_author,
            version=version or parent_version,
            license=license or parent_license
        )
        
        click.echo(subcrate_id)
        
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
    
@rocrate.command('from-pep')
@click.argument('pep-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--output-path', required=False, type=click.Path(path_type=pathlib.Path), help='Path for RO-Crate (defaults to PEP directory)')
@click.option('--name', required=False, type=str, help='Name for the RO-Crate (overrides PEP metadata)')
@click.option('--description', required=False, type=str, help='Description (overrides PEP metadata)')
@click.option('--author', required=False, type=str, help='Author (overrides PEP metadata)')
@click.option('--organization-name', required=False, type=str, help='Organization name')
@click.option('--project-name', required=False, type=str, help='Project name')
@click.option('--keywords', required=False, multiple=True, type=str, help='Keywords (overrides PEP metadata)')
@click.option('--license', required=False, type=str, default="https://creativecommons.org/licenses/by/4.0/", help='License URL')
@click.option('--date-published', required=False, type=str, help='Publication date')
@click.option('--version', required=False, type=str, default="1.0", help='Version string')
@click.pass_context
def from_pep(
    ctx,
    pep_path: pathlib.Path,
    output_path: Optional[pathlib.Path],
    name: Optional[str],
    description: Optional[str],
    author: Optional[str],
    organization_name: Optional[str],
    project_name: Optional[str],
    keywords: Optional[List[str]],
    license: Optional[str],
    date_published: Optional[str],
    version: str
):
    """Convert a Portable Encapsulated Project (PEP) to an RO-Crate.
    
    PEP-PATH: Path to the PEP directory or config file
    """
    try:
        
        
        mapper = PEPtoROCrateMapper(pep_path)
        rocrate_id = mapper.create_rocrate(
            output_path=output_path,
            name=name,
            description=description,
            author=author,
            organization_name=organization_name,
            project_name=project_name,
            keywords=keywords,
            license=license,
            date_published=date_published,
            version=version
        )
        click.echo(rocrate_id)
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        ctx.exit(code=1)
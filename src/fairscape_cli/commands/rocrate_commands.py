import click
import pathlib
import json
from typing import List, Optional, Union
from pydantic import ValidationError
from datetime import datetime 


from fairscape_cli.models.rocrate import (
    GenerateROCrate, ReadROCrateMetadata, AppendCrate, CopyToROCrate, ROCrate
)
from fairscape_cli.models.dataset import GenerateDataset
from fairscape_cli.models.software import GenerateSoftware
from fairscape_cli.models.computation import GenerateComputation
from fairscape_cli.models.sample import GenerateSample
from fairscape_cli.models.instrument import GenerateInstrument
from fairscape_cli.models.experiment import GenerateExperiment

from fairscape_cli.models.utils import FileNotInCrateException
from fairscape_cli.config import NAAN
from fairscape_cli.models import generateSummaryStatsElements 
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid 


@click.group('rocrate')
def rocrate_group():
    """Core operations for local RO-Crate manipulation."""
    pass

@rocrate_group.command('init')
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
    guid, name, organization_name, project_name, description, keywords, license,
    date_published, author, version, associated_publication, conditions_of_access,
    copyright_notice, custom_properties
):
    """Initialize an RO-Crate in the current working directory."""
    params = {
        "guid": guid, "name": name, "organizationName": organization_name,
        "projectName": project_name, "description": description, "keywords": list(keywords),
        "license": license, "datePublished": date_published, "author": author,
        "version": version, "associatedPublication": associated_publication,
        "conditionsOfAccess": conditions_of_access, "copyrightNotice": copyright_notice,
        "path": pathlib.Path.cwd()
    }
    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict): raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            return

    # Filter None values before passing
    filtered_params = {k: v for k, v in params.items() if v is not None}
    passed_crate = GenerateROCrate(**filtered_params)
    click.echo(passed_crate.get("@id"))


@rocrate_group.command('create')
@click.argument('rocrate-path', type=click.Path(exists=False, path_type=pathlib.Path))
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
def create(
    rocrate_path, guid, name, organization_name, project_name, description, keywords,
    license, date_published, author, version, associated_publication,
    conditions_of_access, copyright_notice, custom_properties
):
    """Create an RO-Crate in the specified path."""
    params = {
        "guid": guid, "name": name, "organizationName": organization_name,
        "projectName": project_name, "description": description, "keywords": list(keywords),
        "license": license, "datePublished": date_published, "author": author,
        "version": version, "associatedPublication": associated_publication,
        "conditionsOfAccess": conditions_of_access, "copyrightNotice": copyright_notice,
        "path": rocrate_path
    }
    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict): raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            return

    # Filter None values before passing
    filtered_params = {k: v for k, v in params.items() if v is not None}
    passed_crate = GenerateROCrate(**filtered_params)
    click.echo(passed_crate.get("@id"))


@rocrate_group.group('register')
def register():
    """Add a metadata record to the RO-Crate for a Dataset, Software, or Computation (metadata only)."""
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

#File location options. If more than one is provided, the file_path is defaulted to.
@click.option('--filepath', required=False, help='Path to the software file (relative to crate root)')
@click.option('--content-url', required=False, help='Url to the software file (if hosted externally)')
@click.option('--embargoed', required=False, type=bool, default=False)

@click.option('--used-by-computation', required=False, multiple=True, help='Identifiers of computations that use this software')
@click.option('--associated-publication', required=False, help='Associated publication identifier')
@click.option('--additional-documentation', required=False, help='Additional documentation')
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties.')
@click.pass_context
def registerSoftware(
    ctx,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: str,
    author: str,
    version: str,
    description: str,
    keywords: List[str],
    file_format: Optional[str],
    url: Optional[str],
    date_modified: Optional[str],
    filepath: Optional[str],
    content_url: Optional[str],
    embargoed: bool,
    used_by_computation: Optional[List[str]],
    associated_publication: Optional[str],
    additional_documentation: Optional[str],
    custom_properties: Optional[str],
):
    """Register Software metadata with the specified RO-Crate."""
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {exc}", err=True)
        ctx.exit(code=1)
    
    #Logic to determine the file_path/location
    if not filepath and not content_url and not embargoed:
        click.echo("ERROR: Either 'filepath', 'content-url', or 'embargoed' must be provided for software registration.", err=True)
        ctx.exit(code=1)
    if not filepath and not content_url and embargoed:
        filepath = "Embargoed"
    if not filepath and content_url:
        filepath = content_url

    params = {
        "guid": guid, "name": name, "author": author, "version": version,
        "description": description, "keywords": list(keywords), "fileFormat": file_format,
        "url": url, "dateModified": date_modified, "filepath": filepath,
        "usedByComputation": list(used_by_computation) if used_by_computation else [],
        "associatedPublication": associated_publication,
        "additionalDocumentation": additional_documentation,
        "cratePath": rocrate_path
    }

    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict): raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            ctx.exit(code=1)

    # Filter None values before passing
    filtered_params = {k: v for k, v in params.items() if v is not None}

    try:
        software_instance = GenerateSoftware(**filtered_params)
        AppendCrate(cratePath=rocrate_path, elements=[software_instance])
        click.echo(software_instance.guid)
    except FileNotInCrateException as e:
        click.echo(f"ERROR: {e}", err=True)
        ctx.exit(code=1)
    except ValidationError as e:
        click.echo(f"ERROR: Software Validation Failure\n{e}", err=True)
        ctx.exit(code=1)
    except Exception as exc:
        click.echo(f"ERROR: {exc}", err=True)
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
@click.option('--filepath', required=False, help='Path to the dataset file')
@click.option('--content-url', required=False, help='Url to the software file (if hosted externally)')
@click.option('--embargoed', required=False, type=bool, default=False)
@click.option('--url', required=False, help='URL reference for the dataset')
@click.option('--date-published', required=True, help='Publication date of the dataset (ISO format)')
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
    filepath: Optional[str],
    content_url: Optional[str],
    embargoed: bool,
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
        
    #Logic to determine the file_path/location
    if not filepath and not content_url and not embargoed:
        click.echo("ERROR: Either 'filepath', 'content-url', or 'embargoed' must be provided for dataset registration.", err=True)
        ctx.exit(code=1)
    if not filepath and not content_url and embargoed:
        filepath = "Embargoed"
    if not filepath and content_url:
        filepath = content_url
    
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
@click.option('--command', required=False, help='Command used to run the computation (string or JSON list)')
@click.option('--date-created', required=True, help='Date the computation was run (ISO format)')
@click.option('--description', required=True, help='Description of the computation')
@click.option('--keywords', required=True, multiple=True, help='Keywords for the computation')
@click.option('--used-software', required=False, multiple=True, help='Software identifiers used by this computation')
@click.option('--used-dataset', required=False, multiple=True, help='Dataset identifiers used by this computation')
@click.option('--generated', required=False, multiple=True, help='Dataset/Software identifiers generated by this computation')
@click.option('--associated-publication', required=False, help='Associated publication identifier')
@click.option('--additional-documentation', required=False, help='Additional documentation')
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties.')
@click.pass_context
def computation( 
    ctx,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: str,
    run_by: str,
    command: Optional[str],
    date_created: str,
    description: str,
    keywords: List[str],
    used_software: Optional[List[str]],
    used_dataset: Optional[List[str]],
    generated: Optional[List[str]],
    associated_publication: Optional[str],
    additional_documentation: Optional[str],
    custom_properties: Optional[str],
):
    """Register Computation metadata with the specified RO-Crate."""
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {exc}", err=True)
        ctx.exit(code=1)

    params = {
        "guid": guid, "name": name, "runBy": run_by, "command": command,
        "dateCreated": date_created, "description": description, "keywords": list(keywords),
        "usedSoftware": list(used_software) if used_software else [],
        "usedDataset": list(used_dataset) if used_dataset else [],
        "generated": list(generated) if generated else [],
        "associatedPublication": associated_publication,
        "additionalDocumentation": additional_documentation
    }

    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict): raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            ctx.exit(code=1)

    # Filter None values before passing
    filtered_params = {k: v for k, v in params.items() if v is not None}

    try:
        computationInstance = GenerateComputation(**filtered_params)
        AppendCrate(cratePath=rocrate_path, elements=[computationInstance])
        click.echo(computationInstance.guid)
    except ValidationError as e:
        click.echo(f"ERROR: Computation Validation Failure\n{e}", err=True)
        ctx.exit(code=1)
    except Exception as exc:
        click.echo(f"ERROR: {exc}", err=True)
        ctx.exit(code=1)

@register.command('sample')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None, help='Identifier for the sample (generated if not provided)')
@click.option('--name', required=True, help='Name of the sample')
@click.option('--author', required=True, help='Author or creator of the sample')
@click.option('--description', required=True, help='Description of the sample')
@click.option('--keywords', required=True, multiple=True, help='Keywords for the sample')
@click.option('--filepath', required=False, help='Path to the sample documentation file')
@click.option('--cell-line-reference', required=False, help='Reference to the cell line used')
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
@click.pass_context
def registerSample(
    ctx,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: str,
    author: str,
    description: str,
    keywords: List[str],
    filepath: Optional[str],
    cell_line_reference: Optional[str],
    custom_properties: Optional[str],
):
    """Register Sample metadata with the specified RO-Crate."""
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {exc}", err=True)
        ctx.exit(code=1)

    params = {
        "guid": guid, "name": name, "author": author, "description": description,
        "keywords": list(keywords), "filepath": filepath, "cellLineReference": cell_line_reference,
        "cratePath": rocrate_path
    }

    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict): raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            ctx.exit(code=1)

    # Filter None values before passing
    filtered_params = {k: v for k, v in params.items() if v is not None}

    try:
        sample_instance = GenerateSample(**filtered_params)
        AppendCrate(cratePath=rocrate_path, elements=[sample_instance])
        click.echo(sample_instance.guid)
    except ValidationError as e:
        click.echo(f"ERROR: Sample Validation Failure\n{e}", err=True)
        ctx.exit(code=1)
    except Exception as exc:
        click.echo(f"ERROR: {exc}", err=True)
        ctx.exit(code=1)


@register.command('instrument')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None, help='Identifier for the instrument (generated if not provided)')
@click.option('--name', required=True, help='Name of the instrument')
@click.option('--manufacturer', required=True, help='Manufacturer of the instrument')
@click.option('--model', required=True, help='Model number/name of the instrument')
@click.option('--description', required=True, help='Description of the instrument')
@click.option('--filepath', required=False, help='Path to instrument documentation file')
@click.option('--used-by-experiment', required=False, multiple=True, help='Identifiers of experiments using this instrument')
@click.option('--associated-publication', required=False, help='Associated publication identifier')
@click.option('--additional-documentation', required=False, help='Additional documentation')
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
@click.pass_context
def registerInstrument(
    ctx,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: str,
    manufacturer: str,
    model: str,
    description: str,
    filepath: Optional[str],
    used_by_experiment: Optional[List[str]],
    associated_publication: Optional[str],
    additional_documentation: Optional[str],
    custom_properties: Optional[str],
):
    """Register Instrument metadata with the specified RO-Crate."""
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {exc}", err=True)
        ctx.exit(code=1)

    params = {
        "guid": guid, "name": name, "manufacturer": manufacturer, "model": model,
        "description": description, "filepath": filepath,
        "usedByExperiment": list(used_by_experiment) if used_by_experiment else [],
        "associatedPublication": associated_publication,
        "additionalDocumentation": additional_documentation,
        "cratePath": rocrate_path
    }

    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict): raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            ctx.exit(code=1)

    # Filter None values before passing
    filtered_params = {k: v for k, v in params.items() if v is not None}

    try:
        instrument_instance = GenerateInstrument(**filtered_params)
        AppendCrate(cratePath=rocrate_path, elements=[instrument_instance])
        click.echo(instrument_instance.guid)
    except ValidationError as e:
        click.echo(f"ERROR: Instrument Validation Failure\n{e}", err=True)
        ctx.exit(code=1)
    except Exception as exc:
        click.echo(f"ERROR: {exc}", err=True)
        ctx.exit(code=1)


@register.command('experiment')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None, help='Identifier for the experiment (generated if not provided)')
@click.option('--name', required=True, help='Name of the experiment')
@click.option('--experiment-type', required=True, help='Type of experiment conducted')
@click.option('--run-by', required=True, help='Person or entity that ran the experiment')
@click.option('--description', required=True, help='Description of the experiment')
@click.option('--date-performed', required=True, help='Date the experiment was performed (ISO format)')
@click.option('--used-instrument', required=False, multiple=True, help='Instrument identifiers used in this experiment')
@click.option('--used-sample', required=False, multiple=True, help='Sample identifiers used in this experiment')
@click.option('--used-treatment', required=False, multiple=True, help='Treatment identifiers used in this experiment')
@click.option('--used-stain', required=False, multiple=True, help='Stain identifiers used in this experiment')
@click.option('--generated', required=False, multiple=True, help='Identifiers of entities generated by this experiment')
@click.option('--protocol', required=False, help='Protocol identifier or description')
@click.option('--associated-publication', required=False, help='Associated publication identifier')
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
@click.pass_context
def registerExperiment(
    ctx,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: str,
    experiment_type: str,
    run_by: str,
    description: str,
    date_performed: str,
    used_instrument: Optional[List[str]],
    used_sample: Optional[List[str]],
    used_treatment: Optional[List[str]],
    used_stain: Optional[List[str]],
    generated: Optional[List[str]],
    protocol: Optional[str],
    associated_publication: Optional[str],
    custom_properties: Optional[str],
):
    """Register Experiment metadata with the specified RO-Crate."""
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {exc}", err=True)
        ctx.exit(code=1)

    params = {
        "guid": guid, "name": name, "experimentType": experiment_type, "runBy": run_by,
        "description": description, "datePerformed": date_performed,
        "usedInstrument": list(used_instrument) if used_instrument else [],
        "usedSample": list(used_sample) if used_sample else [],
        "usedTreatment": list(used_treatment) if used_treatment else [],
        "usedStain": list(used_stain) if used_stain else [],
        "generated": list(generated) if generated else [],
        "protocol": protocol,
        "associatedPublication": associated_publication,
    }

    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict): raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            ctx.exit(code=1)

    # Filter None values before passing
    filtered_params = {k: v for k, v in params.items() if v is not None}

    try:
        experiment_instance = GenerateExperiment(**filtered_params)
        AppendCrate(cratePath=rocrate_path, elements=[experiment_instance])
        click.echo(experiment_instance.guid)
    except ValidationError as e:
        click.echo(f"ERROR: Experiment Validation Failure\n{e}", err=True)
        ctx.exit(code=1)
    except Exception as exc:
        click.echo(f"ERROR: {exc}", err=True)
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
        root_metadata = metadata['@graph'][1].model_dump(by_alias=True)
        
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

@rocrate_group.group('add')
def add():
    """Add a file to the RO-Crate and register its metadata."""
    pass

@add.command('software')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None, help='Identifier for the software (generated if not provided)')
@click.option('--name',    required=True, help='Name of the software')
@click.option('--author',  required=True, help='Author of the software')
@click.option('--version', required=True, help='Version of the software')
@click.option('--description', required = True, help='Description of the software')
@click.option('--keywords', required=True, multiple=True, help='Keywords for the software')
@click.option('--file-format', required = True, help='Format of the software (e.g., py, js)')
@click.option('--url',     required = False, help='URL reference for the software')
@click.option('--source-filepath', required=True, type=click.Path(exists=True, path_type=pathlib.Path), help='Path to the source software file on your local filesystem')
@click.option('--destination-filepath', required=True, type=click.Path(path_type=pathlib.Path), help='Desired path for the software file relative to the RO-Crate root')
@click.option('--date-modified', required=False, help='Last modification date of the software (ISO format)')
@click.option('--used-by-computation', required=False, multiple=True, help='Identifiers of computations that use this software')
@click.option('--associated-publication', required=False, help='Associated publication identifier')
@click.option('--additional-documentation', required=False, help='Additional documentation')
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties.')
@click.pass_context
def addSoftware(
    ctx,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: str,
    author: str,
    version: str,
    description: str,
    keywords: List[str],
    file_format: str,
    url: Optional[str],
    source_filepath: pathlib.Path,
    destination_filepath: pathlib.Path,
    date_modified: Optional[str],
    used_by_computation: Optional[List[str]],
    associated_publication: Optional[str],
    additional_documentation: Optional[str],
    custom_properties: Optional[str],
):
    """Copy a Software file into the RO-Crate and register its metadata."""
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {str(exc)}", err=True)
        ctx.exit(code=1)

    if destination_filepath.is_absolute():
        click.echo(f"ERROR: --destination-filepath must be a relative path within the RO-Crate: {destination_filepath}", err=True)
        ctx.exit(code=1)

    try:
        CopyToROCrate(source_filepath, destination_filepath)
    except Exception as exc:
        click.echo(f"ERROR copying file to RO-Crate: {str(exc)}", err=True)
        ctx.exit(code=1)

    params = {
        "guid": guid,
        "name": name,
        "author": author,
        "version": version,
        "description": description,
        "keywords": list(keywords), 
        "fileFormat": file_format,
        "url": url, 
        "dateModified": date_modified, 
        "filepath": str(destination_filepath), 
        "usedByComputation": list(used_by_computation) if used_by_computation else [],
        "associatedPublication": associated_publication, 
        "additionalDocumentation": additional_documentation, 
        "cratePath": rocrate_path 
    }

    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict): raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            ctx.exit(code=1)

    filtered_params = {k: v for k, v in params.items() if v is not None}

    try:
        software_instance = GenerateSoftware(**filtered_params)
        AppendCrate(cratePath=rocrate_path, elements=[software_instance])
        click.echo(software_instance.guid)

    except ValidationError as e:
        click.echo("Software Validation Error", err=True)
        click.echo(e, err=True)
        ctx.exit(code=1)
    except FileNotInCrateException as e:
        click.echo(f"ERROR: File not found in crate after copying? {str(e)}", err=True)
        ctx.exit(code=1)
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}", err=True)
        ctx.exit(code=1)


@add.command('dataset')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None, help='Identifier for the dataset (generated if not provided)')
@click.option('--name', required=True, help='Name of the dataset')
@click.option('--author', required=True, help='Author of the dataset')
@click.option('--version', required=False, default="1.0", help='Version of the dataset')
@click.option('--description', required=True, help='Description of the dataset')
@click.option('--keywords', required=True, multiple=True, help='Keywords for the dataset')
@click.option('--data-format', required=True, help='Format of the dataset (e.g., csv, json)')
@click.option('--source-filepath', required=True, type=click.Path(exists=True, path_type=pathlib.Path), help='Path to the source dataset file on your local filesystem')
@click.option('--destination-filepath', required=True, type=click.Path(path_type=pathlib.Path), help='Desired path for the dataset file relative to the RO-Crate root')
@click.option('--url', required=False, help='URL reference for the dataset')
@click.option('--date-published', required=False, help='Publication date of the dataset (ISO format)') 
@click.option('--schema', required=False, help='Schema identifier for the dataset')
@click.option('--used-by', required=False, multiple=True, help='Identifiers of computations that use this dataset')
@click.option('--derived-from', required=False, multiple=True, help='Identifiers of datasets this one is derived from')
@click.option('--generated-by', required=False, multiple=True, help='Identifiers of computations that generated this dataset')
@click.option('--summary-statistics-source', required=False, type=click.Path(exists=True, path_type=pathlib.Path), help='Path to the source summary statistics file on your local filesystem')
@click.option('--summary-statistics-destination', required=False, type=click.Path(path_type=pathlib.Path), help='Desired path for the summary statistics file relative to the RO-Crate root')
@click.option('--associated-publication', required=False, help='Associated publication identifier')
@click.option('--additional-documentation', required=False, help='Additional documentation')
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
@click.pass_context
def addDataset(
    ctx,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: str,
    author: str,
    version: str,
    description: str,
    keywords: List[str],
    data_format: str,
    source_filepath: pathlib.Path,
    destination_filepath: pathlib.Path,
    url: Optional[str] = None,
    date_published: Optional[str] = None,
    schema: Optional[str] = None,
    used_by: Optional[List[str]] = None,
    derived_from: Optional[List[str]] = None,
    generated_by: Optional[List[str]] = None,
    summary_statistics_source: Optional[pathlib.Path] = None,
    summary_statistics_destination: Optional[pathlib.Path] = None,
    associated_publication: Optional[str] = None,
    additional_documentation: Optional[str] = None,
    custom_properties: Optional[str] = None,
):
    """Copy a Dataset file into the RO-Crate and register its metadata.

    Copies the dataset file from SOURCE_FILEPATH to DESTINATION_FILEPATH
    within the RO-Crate and registers its metadata. Optionally copies
    a summary statistics file and registers associated metadata (Computation
    and another Dataset).

    Examples:
        fairscape rocrate add dataset ./my-crate --name "My Data" --author "J. Doe" ... --source-filepath /local/data.csv --destination-filepath data/data.csv

        # With summary statistics:
        fairscape rocrate add dataset ./my-crate --name "My Data" ... --source-filepath /local/data.csv --destination-filepath data/data.csv --summary-statistics-source /local/data_summary.json --summary-statistics-destination data/data_summary.json
    """

    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {str(exc)}", err=True)
        ctx.exit(code=1)

    if destination_filepath.is_absolute():
        click.echo(f"ERROR: --destination-filepath must be a relative path within the RO-Crate: {destination_filepath}", err=True)
        ctx.exit(code=1)

    if summary_statistics_destination and summary_statistics_destination.is_absolute():
         click.echo(f"ERROR: --summary-statistics-destination must be a relative path within the RO-Crate: {summary_statistics_destination}", err=True)
         ctx.exit(code=1)

    try:
        CopyToROCrate(source_filepath, destination_filepath)

        elements_to_append = []
        summary_stats_guid = None

        if summary_statistics_source and summary_statistics_destination:
            try:
                copied_summary_stats_filepath = CopyToROCrate(summary_statistics_source, summary_statistics_destination)
                click.echo(f"Copied '{summary_statistics_source}' to '{copied_summary_stats_filepath}' inside the crate.")

                summary_stats_guid, summary_stats_instance, computation_instance = generateSummaryStatsElements(
                    name=name, 
                    author=author,
                    keywords=list(keywords),
                    date_published=date_published, 
                    version=version, 
                    associated_publication=associated_publication,
                    additional_documentation=additional_documentation, 
                    schema=schema, 
                    dataset_guid=guid, 
                    summary_statistics_filepath=str(summary_statistics_destination), 
                    crate_path=rocrate_path
                )
                elements_to_append.extend([computation_instance, summary_stats_instance])

            except Exception as exc:
                 click.echo(f"ERROR handling summary statistics files: {str(exc)}", err=True)
                 ctx.exit(code=1)


        params = {
            "guid": guid, 
            "name": name,
            "author": author,
            "description": description,
            "keywords": list(keywords), 
            "version": version, 
            "format": data_format,
            "filepath": str(destination_filepath), 
            "cratePath": rocrate_path, 
            "url": url, 
            "datePublished": date_published, 
            "schema": schema, 
            "usedBy": list(used_by) if used_by else [], 
            "derivedFrom": list(derived_from) if derived_from else [], 
            "generatedBy": list(generated_by) if generated_by else [], 
            "associatedPublication": associated_publication, 
            "additionalDocumentation": additional_documentation, 
        }

        if summary_stats_guid:
            params["summary_stats_guid"] = summary_stats_guid


        if custom_properties:
            try:
                custom_props = json.loads(custom_properties)
                if not isinstance(custom_props, dict): raise ValueError("Custom properties must be a JSON object")
                params.update(custom_props)
            except Exception as e:
                click.echo(f"ERROR processing custom properties: {e}", err=True)
                ctx.exit(code=1)

        # Filter None values before passing
        filtered_params = {k: v for k, v in params.items() if v is not None}

        dataset_instance = GenerateDataset(**filtered_params)
        elements_to_append.insert(0, dataset_instance)
        AppendCrate(cratePath=rocrate_path, elements=elements_to_append)

        click.echo(dataset_instance.guid)

    except ValidationError as e:
        click.echo("Dataset Validation Error", err=True)
        click.echo(e, err=True)
        ctx.exit(code=1)
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}", err=True)
        ctx.exit(code=1)

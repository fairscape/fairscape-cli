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
@click.option('--filepath', required=False, help='Path to the software file (relative to crate root)')
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
    file_format: str,
    url: Optional[str],
    date_modified: Optional[str],
    filepath: Optional[str],
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
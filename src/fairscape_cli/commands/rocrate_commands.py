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
from fairscape_cli.models.biochem_entity import GenerateBioChemEntity
from fairscape_cli.models.MLModel import GenerateModel
from fairscape_cli.utils.huggingface_utils import fetch_huggingface_model_metadata

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
@click.option('--maintenance-plan', required=False, type=str, help="RAI: Versioning, maintainers, and deprecation policies.")
@click.option('--intended-use', required=False, type=str, help="RAI: Recommended dataset uses (e.g., training, validation).")
@click.option('--limitations', required=False, type=str, help="RAI: Known limitations and non-recommended uses.")
@click.option('--potential-sources-of-bias', required=False, type=str, help="RAI: Description of known biases in the dataset.")
@click.option('--prohibited-uses', required=False, type=str, help="Prohibited uses of the release (appended to Limitations).")
@click.option('--rai-data-collection', required=False, type=str, help="RAI: Description of the data collection process.")
@click.option('--rai-data-collection-type', required=False, multiple=True, type=str, help="RAI: Type of data collection (e.g., 'Web Scraping', 'Surveys').")
@click.option('--rai-missing-data-desc', required=False, type=str, help="RAI: Description of missing data in the dataset.")
@click.option('--rai-raw-data-source', required=False, type=str, help="RAI: Description of the raw data source.")
@click.option('--rai-collection-start-date', required=False, type=str, help="RAI: Start date of the data collection process (ISO format).")
@click.option('--rai-collection-end-date', required=False, type=str, help="RAI: End date of the data collection process (ISO format).")
@click.option('--rai-imputation-protocol', required=False, type=str, help="RAI: Description of the data imputation process.")
@click.option('--rai-manipulation-protocol', required=False, type=str, help="RAI: Description of the data manipulation process.")
@click.option('--rai-preprocessing-protocol', required=False, multiple=True, type=str, help="RAI: Steps taken to preprocess the data for ML use.")
@click.option('--rai-annotation-protocol', required=False, type=str, help="RAI: Description of the annotation process (e.g., workforce, tasks).")
@click.option('--rai-annotation-platform', required=False, multiple=True, type=str, help="RAI: Platform or tool used for human annotation.")
@click.option('--rai-annotation-analysis', required=False, multiple=True, type=str, help="RAI: Analysis of annotations (e.g., disagreement resolution).")
@click.option('--rai-sensitive-info', required=False, multiple=True, type=str, help="RAI: Description of any personal or sensitive information.")
@click.option('--rai-social-impact', required=False, type=str, help="RAI: Discussion of the dataset's potential social impact.")
@click.option('--rai-annotations-per-item', required=False, type=str, help="RAI: Number of human labels per dataset item.")
@click.option('--rai-annotator-demographics', required=False, multiple=True, type=str, help="RAI: Demographic specifications about the annotators.")
@click.option('--rai-machine-annotation-tools', required=False, multiple=True, type=str, help="RAI: Software used for automated data annotation.")
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
def init(
    guid, name, organization_name, project_name, description, keywords, license,
    date_published, author, version, associated_publication, conditions_of_access,
    copyright_notice, maintenance_plan, intended_use, limitations, potential_sources_of_bias,
    prohibited_uses, rai_data_collection, rai_data_collection_type, rai_missing_data_desc,
    rai_raw_data_source, rai_collection_start_date, rai_collection_end_date,
    rai_imputation_protocol, rai_manipulation_protocol, rai_preprocessing_protocol,
    rai_annotation_protocol, rai_annotation_platform, rai_annotation_analysis,
    rai_sensitive_info, rai_social_impact, rai_annotations_per_item,
    rai_annotator_demographics, rai_machine_annotation_tools, custom_properties
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
    
    rai_properties = {}
    if limitations:
        limitations_text = limitations
        if prohibited_uses:
            limitations_text += f"\n\nProhibited Uses: {prohibited_uses}"
        rai_properties["rai:dataLimitations"] = limitations_text
    if potential_sources_of_bias:
        rai_properties["rai:dataBiases"] = potential_sources_of_bias
    if intended_use:
        rai_properties["rai:dataUseCases"] = intended_use
    if maintenance_plan:
        rai_properties["rai:dataReleaseMaintenancePlan"] = maintenance_plan
    if rai_data_collection:
        rai_properties["rai:dataCollection"] = rai_data_collection
    if rai_data_collection_type:
        rai_properties["rai:dataCollectionType"] = list(rai_data_collection_type)
    if rai_missing_data_desc:
        rai_properties["rai:dataCollectionMissingData"] = rai_missing_data_desc
    if rai_raw_data_source:
        rai_properties["rai:dataCollectionRawData"] = rai_raw_data_source
    if rai_imputation_protocol:
        rai_properties["rai:dataImputationProtocol"] = rai_imputation_protocol
    if rai_manipulation_protocol:
        rai_properties["rai:dataManipulationProtocol"] = rai_manipulation_protocol
    if rai_preprocessing_protocol:
        rai_properties["rai:dataPreprocessingProtocol"] = list(rai_preprocessing_protocol)
    if rai_annotation_protocol:
        rai_properties["rai:dataAnnotationProtocol"] = rai_annotation_protocol
    if rai_annotation_platform:
        rai_properties["rai:dataAnnotationPlatform"] = list(rai_annotation_platform)
    if rai_annotation_analysis:
        rai_properties["rai:dataAnnotationAnalysis"] = list(rai_annotation_analysis)
    if rai_sensitive_info:
        rai_properties["rai:personalSensitiveInformation"] = list(rai_sensitive_info)
    if rai_social_impact:
        rai_properties["rai:dataSocialImpact"] = rai_social_impact
    if rai_annotations_per_item:
        rai_properties["rai:annotationsPerItem"] = rai_annotations_per_item
    if rai_annotator_demographics:
        rai_properties["rai:annotatorDemographics"] = list(rai_annotator_demographics)
    if rai_machine_annotation_tools:
        rai_properties["rai:machineAnnotationTools"] = list(rai_machine_annotation_tools)
    
    timeframe = []
    if rai_collection_start_date:
        timeframe.append(rai_collection_start_date)
    if rai_collection_end_date:
        timeframe.append(rai_collection_end_date)
    if timeframe:
        rai_properties["rai:dataCollectionTimeframe"] = timeframe
    
    params.update(rai_properties)
    
    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict): raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            return

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
@click.option('--maintenance-plan', required=False, type=str, help="RAI: Versioning, maintainers, and deprecation policies.")
@click.option('--intended-use', required=False, type=str, help="RAI: Recommended dataset uses (e.g., training, validation).")
@click.option('--limitations', required=False, type=str, help="RAI: Known limitations and non-recommended uses.")
@click.option('--potential-sources-of-bias', required=False, type=str, help="RAI: Description of known biases in the dataset.")
@click.option('--prohibited-uses', required=False, type=str, help="Prohibited uses of the release (appended to Limitations).")
@click.option('--rai-data-collection', required=False, type=str, help="RAI: Description of the data collection process.")
@click.option('--rai-data-collection-type', required=False, multiple=True, type=str, help="RAI: Type of data collection (e.g., 'Web Scraping', 'Surveys').")
@click.option('--rai-missing-data-desc', required=False, type=str, help="RAI: Description of missing data in the dataset.")
@click.option('--rai-raw-data-source', required=False, type=str, help="RAI: Description of the raw data source.")
@click.option('--rai-collection-start-date', required=False, type=str, help="RAI: Start date of the data collection process (ISO format).")
@click.option('--rai-collection-end-date', required=False, type=str, help="RAI: End date of the data collection process (ISO format).")
@click.option('--rai-imputation-protocol', required=False, type=str, help="RAI: Description of the data imputation process.")
@click.option('--rai-manipulation-protocol', required=False, type=str, help="RAI: Description of the data manipulation process.")
@click.option('--rai-preprocessing-protocol', required=False, multiple=True, type=str, help="RAI: Steps taken to preprocess the data for ML use.")
@click.option('--rai-annotation-protocol', required=False, type=str, help="RAI: Description of the annotation process (e.g., workforce, tasks).")
@click.option('--rai-annotation-platform', required=False, multiple=True, type=str, help="RAI: Platform or tool used for human annotation.")
@click.option('--rai-annotation-analysis', required=False, multiple=True, type=str, help="RAI: Analysis of annotations (e.g., disagreement resolution).")
@click.option('--rai-sensitive-info', required=False, multiple=True, type=str, help="RAI: Description of any personal or sensitive information.")
@click.option('--rai-social-impact', required=False, type=str, help="RAI: Discussion of the dataset's potential social impact.")
@click.option('--rai-annotations-per-item', required=False, type=str, help="RAI: Number of human labels per dataset item.")
@click.option('--rai-annotator-demographics', required=False, multiple=True, type=str, help="RAI: Demographic specifications about the annotators.")
@click.option('--rai-machine-annotation-tools', required=False, multiple=True, type=str, help="RAI: Software used for automated data annotation.")
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
def create(
    rocrate_path, guid, name, organization_name, project_name, description, keywords,
    license, date_published, author, version, associated_publication,
    conditions_of_access, copyright_notice, maintenance_plan, intended_use, limitations,
    potential_sources_of_bias, prohibited_uses, rai_data_collection, rai_data_collection_type,
    rai_missing_data_desc, rai_raw_data_source, rai_collection_start_date,
    rai_collection_end_date, rai_imputation_protocol, rai_manipulation_protocol,
    rai_preprocessing_protocol, rai_annotation_protocol, rai_annotation_platform,
    rai_annotation_analysis, rai_sensitive_info, rai_social_impact,
    rai_annotations_per_item, rai_annotator_demographics, rai_machine_annotation_tools,
    custom_properties
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
    
    rai_properties = {}
    if limitations:
        limitations_text = limitations
        if prohibited_uses:
            limitations_text += f"\n\nProhibited Uses: {prohibited_uses}"
        rai_properties["rai:dataLimitations"] = limitations_text
    if potential_sources_of_bias:
        rai_properties["rai:dataBiases"] = potential_sources_of_bias
    if intended_use:
        rai_properties["rai:dataUseCases"] = intended_use
    if maintenance_plan:
        rai_properties["rai:dataReleaseMaintenancePlan"] = maintenance_plan
    if rai_data_collection:
        rai_properties["rai:dataCollection"] = rai_data_collection
    if rai_data_collection_type:
        rai_properties["rai:dataCollectionType"] = list(rai_data_collection_type)
    if rai_missing_data_desc:
        rai_properties["rai:dataCollectionMissingData"] = rai_missing_data_desc
    if rai_raw_data_source:
        rai_properties["rai:dataCollectionRawData"] = rai_raw_data_source
    if rai_imputation_protocol:
        rai_properties["rai:dataImputationProtocol"] = rai_imputation_protocol
    if rai_manipulation_protocol:
        rai_properties["rai:dataManipulationProtocol"] = rai_manipulation_protocol
    if rai_preprocessing_protocol:
        rai_properties["rai:dataPreprocessingProtocol"] = list(rai_preprocessing_protocol)
    if rai_annotation_protocol:
        rai_properties["rai:dataAnnotationProtocol"] = rai_annotation_protocol
    if rai_annotation_platform:
        rai_properties["rai:dataAnnotationPlatform"] = list(rai_annotation_platform)
    if rai_annotation_analysis:
        rai_properties["rai:dataAnnotationAnalysis"] = list(rai_annotation_analysis)
    if rai_sensitive_info:
        rai_properties["rai:personalSensitiveInformation"] = list(rai_sensitive_info)
    if rai_social_impact:
        rai_properties["rai:dataSocialImpact"] = rai_social_impact
    if rai_annotations_per_item:
        rai_properties["rai:annotationsPerItem"] = rai_annotations_per_item
    if rai_annotator_demographics:
        rai_properties["rai:annotatorDemographics"] = list(rai_annotator_demographics)
    if rai_machine_annotation_tools:
        rai_properties["rai:machineAnnotationTools"] = list(rai_machine_annotation_tools)
    
    timeframe = []
    if rai_collection_start_date:
        timeframe.append(rai_collection_start_date)
    if rai_collection_end_date:
        timeframe.append(rai_collection_end_date)
    if timeframe:
        rai_properties["rai:dataCollectionTimeframe"] = timeframe
    
    params.update(rai_properties)
    
    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict): raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            return

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
@click.option('--embargoed', required=False, is_flag=True, default=False)

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
@click.option('--embargoed', required=False, is_flag=True, default=False)
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


@register.command('biochementity')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None, help='Identifier for the sample (generated if not provided)')
@click.option('--name', required=True, help='Name of the sample')
@click.option('--description', required=True, help='Description of the sample')
@click.option('--usedby', required=False, multiple=True, help="Identifiers of Experiments/Samples/Datasets that used this entity")
@click.option('--identifier', required=False, multiple=True, help="Other known identifiers for this biochem entity formatted as '<propertyName>:<propertyValue>' ")
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties to include')
@click.pass_context
def registerBioChemEntity(
    ctx,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: str,
    description: str,
    usedby: Optional[List[str]],
    identifier: Optional[List[str]],
    custom_properties: Optional[str],
):
    """Register BioChemEntity metadata with the specified RO-Crate."""
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {exc}", err=True)
        ctx.exit(code=1)

    params = {
        "guid": guid, "name": name, "description": description,
        "cratePath": rocrate_path
    }

    if usedby:
        params['usedBy'] = list(usedby)
    if identifier:
        params['identifier'] = list(identifier)

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
        bioChemEntityInstance = GenerateBioChemEntity(**filtered_params)
        AppendCrate(cratePath=rocrate_path, elements=[bioChemEntityInstance])
        click.echo(bioChemEntityInstance.guid)
    except ValidationError as e:
        click.echo(f"ERROR: Sample Validation Failure\n{e}", err=True)
        ctx.exit(code=1)
    except Exception as exc:
        click.echo(f"ERROR: {exc}", err=True)
        ctx.exit(code=1)
        
@register.command('model')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None)
@click.option('--name', required=True)
@click.option('--author', required=True)
@click.option('--version', required=True)
@click.option('--description', required=True)
@click.option('--keywords', required=True, multiple=True)
@click.option('--model-type', required=False)
@click.option('--framework', required=False)
@click.option('--model-format', required=False)
@click.option('--training-dataset', required=False, multiple=True)
@click.option('--generated-by', required=False)
@click.option('--filepath', required=False)
@click.option('--content-url', required=False)
@click.option('--embargoed', required=False, is_flag=True, default=False)
@click.option('--parameters', required=False, type=float)
@click.option('--input-size', required=False)
@click.option('--has-bias', required=False)
@click.option('--intended-use-case', required=False)
@click.option('--usage-information', required=False)
@click.option('--base-model', required=False)
@click.option('--associated-publication', required=False)
@click.option('--url', required=False)
@click.option('--license', required=False)
@click.option('--citation', required=False)
@click.option('--custom-properties', required=False, type=str)
@click.pass_context
def registerModel(
    ctx,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: str,
    author: str,
    version: str,
    description: str,
    keywords: List[str],
    model_type: str,
    framework: str,
    model_format: str,
    training_dataset: List[str],
    generated_by: str,
    filepath: Optional[str],
    content_url: Optional[str],
    embargoed: bool,
    parameters: Optional[float],
    input_size: Optional[str],
    has_bias: Optional[str],
    intended_use_case: Optional[str],
    usage_information: Optional[str],
    base_model: Optional[str],
    associated_publication: Optional[str],
    url: Optional[str],
    license: Optional[str],
    citation: Optional[str],
    custom_properties: Optional[str],
):
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {exc}", err=True)
        ctx.exit(code=1)
    
    if not filepath and not content_url and not embargoed:
        click.echo("ERROR: Either 'filepath', 'content-url', or 'embargoed' must be provided for model registration.", err=True)
        ctx.exit(code=1)
    if not filepath and not content_url and embargoed:
        filepath = "Embargoed"
    if not filepath and content_url:
        filepath = content_url
    
    params = {
        "guid": guid,
        "name": name,
        "author": author,
        "version": version,
        "description": description,
        "keywords": list(keywords),
        "modelType": model_type,
        "framework": framework,
        "format": model_format,
        "trainingDataset": list(training_dataset),
        "generatedBy": generated_by,
        "filepath": filepath,
        "cratePath": rocrate_path,
    }
    
    if parameters is not None:
        params["parameters"] = parameters
    if input_size:
        params["inputSize"] = input_size
    if has_bias:
        params["hasBias"] = has_bias
    if intended_use_case:
        params["intendedUseCase"] = intended_use_case
    if usage_information:
        params["usageInformation"] = usage_information
    if base_model:
        params["baseModel"] = base_model
    if associated_publication:
        params["associatedPublication"] = associated_publication
    if url:
        params["url"] = url
    if license:
        params["dataLicense"] = license
    if citation:
        params["citation"] = citation
    
    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict):
                raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            ctx.exit(code=1)
    
    filtered_params = {k: v for k, v in params.items() if v is not None}
    
    try:
        model_instance = GenerateModel(**filtered_params)
        AppendCrate(cratePath=rocrate_path, elements=[model_instance])
        click.echo(model_instance.guid)
    except FileNotInCrateException as e:
        click.echo(f"ERROR: {e}", err=True)
        ctx.exit(code=1)
    except ValidationError as e:
        click.echo(f"ERROR: Model Validation Failure\n{e}", err=True)
        ctx.exit(code=1)
    except Exception as exc:
        click.echo(f"ERROR: {exc}", err=True)
        ctx.exit(code=1)


@register.command('hf')
@click.argument('hf-url', type=str, metavar='HF_URL_OR_REPO_ID')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None, help='Identifier for the model (generated if not provided)')
@click.option('--name', required=False, help='Override model name from HuggingFace')
@click.option('--author', required=False, help='Override author from HuggingFace')
@click.option('--version', required=False, help='Override version (default: 1.0)')
@click.option('--description', required=False, help='Override description from HuggingFace')
@click.option('--keywords', required=False, multiple=True, help='Override/supplement keywords from HuggingFace tags')
@click.option('--model-type', required=False, help='Override model type inferred from tags')
@click.option('--framework', required=False, help='Override framework inferred from tags')
@click.option('--model-format', required=False, help='Override model format inferred from file extension')
@click.option('--training-dataset', required=False, multiple=True, help='Specify training datasets')
@click.option('--generated-by', required=False, help='RO-Crate computation identifier that generated this model')
@click.option('--parameters', required=False, type=float, help='Number of model parameters')
@click.option('--input-size', required=False, help='Model input size')
@click.option('--has-bias', required=False, help='Whether model has bias')
@click.option('--intended-use-case', required=False, help='Intended use case for the model')
@click.option('--usage-information', required=False, help='Usage information')
@click.option('--base-model', required=False, help='Override base model from HuggingFace')
@click.option('--associated-publication', required=False, help='Associated publication identifier')
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties')
@click.pass_context
def registerHuggingFaceModel(
    ctx,
    hf_url: str,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: Optional[str],
    author: Optional[str],
    version: Optional[str],
    description: Optional[str],
    keywords: Optional[List[str]],
    model_type: Optional[str],
    framework: Optional[str],
    model_format: Optional[str],
    training_dataset: Optional[List[str]],
    generated_by: Optional[str],
    parameters: Optional[float],
    input_size: Optional[str],
    has_bias: Optional[str],
    intended_use_case: Optional[str],
    usage_information: Optional[str],
    base_model: Optional[str],
    associated_publication: Optional[str],
    custom_properties: Optional[str],
):
    """Register a model from HuggingFace using its URL or repo_id.

    Fetches model metadata from HuggingFace API and registers it with the RO-Crate.
    All CLI options override values fetched from HuggingFace.

    Examples:
        fairscape rocrate register hf https://huggingface.co/timm/densenet121.tv_in1k ./my-crate
        fairscape rocrate register hf timm/densenet121.tv_in1k ./my-crate
        fairscape rocrate register hf timm/densenet121.tv_in1k ./my-crate --generated-by ark:12345/computation-xyz
    """
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {exc}", err=True)
        ctx.exit(code=1)

    # Fetch metadata from HuggingFace
    try:
        click.echo("Fetching model metadata from HuggingFace...", err=True)
        hf_metadata = fetch_huggingface_model_metadata(hf_url)
    except ImportError as e:
        click.echo(f"ERROR: {e}", err=True)
        click.echo("Install with: pip install huggingface_hub", err=True)
        ctx.exit(code=1)
    except Exception as e:
        click.echo(f"ERROR fetching HuggingFace metadata: {e}", err=True)
        ctx.exit(code=1)
        
    if 'https://' not in  hf_metadata.get('landing_page_url'):
        hf_metadata['landing_page_url'] = "https://huggingface.co/" + hf_metadata.get('landing_page_url')

    # Build params, with CLI options overriding HuggingFace metadata
    params = {
        "guid": guid,
        "name": name or hf_metadata.get('name'),
        "author": author or hf_metadata.get('author', 'Unknown'),
        "version": version or hf_metadata.get('version', '1.0'),
        "description": description or hf_metadata.get('description', ''),
        "keywords": list(keywords) if keywords else hf_metadata.get('keywords', []),
        "modelType": model_type or hf_metadata.get('model_type'),
        "framework": framework or hf_metadata.get('framework'),
        "format": model_format or hf_metadata.get('model_format'),
        "trainingDataset": list(training_dataset) if training_dataset else hf_metadata.get('training_datasets', []),
        "filepath": hf_metadata.get('download_url'),  
        "url": hf_metadata.get('landing_page_url'),   
        "cratePath": rocrate_path,
    }

    # Add optional parameters
    if parameters is not None:
        params["parameters"] = parameters
    if input_size:
        params["inputSize"] = input_size
    bias_value = has_bias or hf_metadata.get('bias')
    if bias_value:
        params["hasBias"] = bias_value
    intended_use_value = intended_use_case or hf_metadata.get('intended_use_case')
    if intended_use_value:
        params["intendedUseCase"] = intended_use_value
    usage_value = usage_information or hf_metadata.get('usage_information')
    if usage_value:
        params["usageInformation"] = usage_value
    if base_model or hf_metadata.get('base_model'):
        params["baseModel"] = base_model or hf_metadata.get('base_model')
    if associated_publication:
        params["associatedPublication"] = associated_publication
    if hf_metadata.get('license'):
        params["license"] = hf_metadata.get('license')
    if hf_metadata.get('README'):
        params["README"] = hf_metadata.get('README')

    # Handle custom properties
    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict):
                raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            ctx.exit(code=1)

    # Filter None values
    filtered_params = {k: v for k, v in params.items() if v is not None}

    # Validate required fields
    if not filtered_params.get('name'):
        click.echo("ERROR: Could not determine model name from HuggingFace. Please specify --name", err=True)
        ctx.exit(code=1)
    if not filtered_params.get('description'):
        click.echo("ERROR: Could not determine model description from HuggingFace. Please specify --description", err=True)
        ctx.exit(code=1)

    # Register the model
    try:
        model_instance = GenerateModel(**filtered_params)
        AppendCrate(cratePath=rocrate_path, elements=[model_instance])
        click.echo(model_instance.guid)
    except ValidationError as e:
        click.echo(f"ERROR: Model Validation Failure\n{e}", err=True)
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

@rocrate_group.command('validate')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--use-official', is_flag=True, help='Use official RO-Crate validator (requires roc-validator package)')
@click.option('--profile', type=str, default=None, help='Profile to validate against (only with --use-official)')
@click.option('--requirement-level', type=click.Choice(['REQUIRED', 'RECOMMENDED', 'OPTIONAL']), default='REQUIRED', help='Requirement level for official validator (default: REQUIRED)')
@click.pass_context
def validate(ctx, rocrate_path, use_official, profile, requirement_level):
    """Validate an RO-Crate against ROCrate v1.2 schema or official RO-Crate validator.

    By default, validates against the built-in ROCrate v1.2 model.
    Use --use-official to validate with the official RO-Crate validator (requires roc-validator package).

    Examples:
        fairscape rocrate validate ./my-crate
        fairscape rocrate validate ./my-crate --use-official
        fairscape rocrate validate ./my-crate --use-official --profile ro-crate
        fairscape rocrate validate ./my-crate --use-official --requirement-level RECOMMENDED
    """

    if use_official:
        # Try to use official RO-Crate validator
        try:
            from rocrate_validator.models import ValidationSettings
            from rocrate_validator import services
        except ImportError:
            click.echo("ERROR: roc-validator package is not installed.", err=True)
            click.echo("Install with: pip install roc-validator", err=True)
            ctx.exit(code=1)

        try:
            # Prepare the path for validation
            crate_uri = str(rocrate_path.absolute())

            # Create validation settings
            settings_params = {
                "data_path": crate_uri,
                "requirement_severity": requirement_level
            }

            if profile:
                settings_params["profile_identifier"] = profile

            validation_settings = ValidationSettings(**settings_params)

            # Run validation
            result = services.validate(validation_settings)

            if result.passed():
                click.echo("✓ Valid (official RO-Crate validator)")
            else:
                click.echo("✗ Validation failed (official RO-Crate validator):")
                for issue in result.get_issues():
                    click.echo(f"  [{issue.severity}] {issue.message}")

                ctx.exit(code=1)

        except Exception as e:
            click.echo(f"ERROR: {e}", err=True)
            ctx.exit(code=1)

    else:
        # Use built-in ROCrate v1.2 validation
        try:
            metadata = ReadROCrateMetadata(rocrate_path)
            click.echo("✓ Valid (ROCrate v1.2 model)")

        except ValidationError as e:
            click.echo(f"✗ Validation failed (ROCrate v1.2 model): {e}", err=True)
            ctx.exit(code=1)
        except FileNotFoundError:
            click.echo(f"✗ ro-crate-metadata.json not found", err=True)
            ctx.exit(code=1)
        except json.JSONDecodeError as e:
            click.echo(f"✗ Invalid JSON: {e}", err=True)
            ctx.exit(code=1)
        except Exception as e:
            click.echo(f"✗ {e}", err=True)
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
        
@add.command('model')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--guid', type=str, required=False, default=None)
@click.option('--name', required=True)
@click.option('--author', required=True)
@click.option('--version', required=True)
@click.option('--description', required=True)
@click.option('--keywords', required=True, multiple=True)
@click.option('--model-type', required=True)
@click.option('--framework', required=True)
@click.option('--model-format', required=True)
@click.option('--training-dataset', required=True, multiple=True)
@click.option('--generated-by', required=True)
@click.option('--source-filepath', required=True, type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--destination-filepath', required=True, type=click.Path(path_type=pathlib.Path))
@click.option('--parameters', required=False, type=float)
@click.option('--input-size', required=False)
@click.option('--has-bias', required=False)
@click.option('--intended-use-case', required=False)
@click.option('--usage-information', required=False)
@click.option('--base-model', required=False)
@click.option('--associated-publication', required=False)
@click.option('--url', required=False)
@click.option('--license', required=False)
@click.option('--citation', required=False)
@click.option('--custom-properties', required=False, type=str)
@click.pass_context
def addModel(
    ctx,
    rocrate_path: pathlib.Path,
    guid: Optional[str],
    name: str,
    author: str,
    version: str,
    description: str,
    keywords: List[str],
    model_type: str,
    framework: str,
    model_format: str,
    training_dataset: List[str],
    generated_by: str,
    source_filepath: pathlib.Path,
    destination_filepath: pathlib.Path,
    parameters: Optional[float],
    input_size: Optional[str],
    has_bias: Optional[str],
    intended_use_case: Optional[str],
    usage_information: Optional[str],
    base_model: Optional[str],
    associated_publication: Optional[str],
    url: Optional[str],
    license: Optional[str],
    citation: Optional[str],
    custom_properties: Optional[str],
):
    try:
        ReadROCrateMetadata(rocrate_path)
    except Exception as exc:
        click.echo(f"ERROR Reading ROCrate: {exc}", err=True)
        ctx.exit(code=1)
    
    if destination_filepath.is_absolute():
        click.echo(f"ERROR: --destination-filepath must be a relative path within the RO-Crate: {destination_filepath}", err=True)
        ctx.exit(code=1)
    
    try:
        CopyToROCrate(source_filepath, destination_filepath)
    except Exception as exc:
        click.echo(f"ERROR copying file to RO-Crate: {exc}", err=True)
        ctx.exit(code=1)
    
    params = {
        "guid": guid,
        "name": name,
        "author": author,
        "version": version,
        "description": description,
        "keywords": list(keywords),
        "modelType": model_type,
        "framework": framework,
        "modelFormat": model_format,
        "trainingDataset": list(training_dataset),
        "generatedBy": generated_by,
        "filepath": str(destination_filepath),
        "cratePath": rocrate_path,
    }
    
    if parameters is not None:
        params["parameters"] = parameters
    if input_size:
        params["inputSize"] = input_size
    if has_bias:
        params["hasBias"] = has_bias
    if intended_use_case:
        params["intendedUseCase"] = intended_use_case
    if usage_information:
        params["usageInformation"] = usage_information
    if base_model:
        params["baseModel"] = base_model
    if associated_publication:
        params["associatedPublication"] = associated_publication
    if url:
        params["url"] = url
    if license:
        params["dataLicense"] = license
    if citation:
        params["citation"] = citation
    
    if custom_properties:
        try:
            custom_props = json.loads(custom_properties)
            if not isinstance(custom_props, dict):
                raise ValueError("Custom properties must be a JSON object")
            params.update(custom_props)
        except Exception as e:
            click.echo(f"ERROR processing custom properties: {e}", err=True)
            ctx.exit(code=1)
    
    filtered_params = {k: v for k, v in params.items() if v is not None}
    
    try:
        model_instance = GenerateModel(**filtered_params)
        AppendCrate(cratePath=rocrate_path, elements=[model_instance])
        click.echo(model_instance.guid)
    except ValidationError as e:
        click.echo(f"ERROR: Model Validation Failure\n{e}", err=True)
        ctx.exit(code=1)
    except FileNotInCrateException as e:
        click.echo(f"ERROR: {e}", err=True)
        ctx.exit(code=1)
    except Exception as exc:
        click.echo(f"ERROR: {exc}", err=True)
        ctx.exit(code=1)

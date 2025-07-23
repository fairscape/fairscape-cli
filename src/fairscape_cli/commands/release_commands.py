import click
import pathlib
import json
from datetime import datetime
from typing import List, Optional, Tuple
import os
from pathlib import Path

from fairscape_cli.models import (
    GenerateROCrate,
    LinkSubcrates,
    collect_subcrate_metadata
)

from fairscape_cli.datasheet_builder.rocrate.datasheet_generator import DatasheetGenerator

@click.group('release_group')
def release_group():
    """Invoke operations on Research Object Crate (RO-CRate).
    """
    pass

@release_group.command('build')
@click.argument('release-directory', type=click.Path(exists=False, path_type=pathlib.Path, file_okay=False, dir_okay=True))
# Standard Crate Properties
@click.option('--guid', required=False, type=str, default="", show_default=False, help="GUID for the parent release RO-Crate (generated if not provided).")
@click.option('--name', required=True, type=str, help="Name for the parent release RO-Crate.")
@click.option('--organization-name', required=True, type=str, help="Organization name associated with the release.")
@click.option('--project-name', required=True, type=str, help="Project name associated with the release.")
@click.option('--description', required=True, type=str, help="Description of the release RO-Crate.")
@click.option('--keywords', required=True, multiple=True, type=str, help="Keywords for the release RO-Crate.")
@click.option('--license', required=False, type=str, default="https://creativecommons.org/licenses/by/4.0/", help="License URL for the release.")
@click.option('--date-published', required=False, type=str, help="Publication date (ISO format, defaults to now).")
@click.option('--author', required=False, type=str, default=None, help="Author(s) of the release.")
@click.option('--version', required=False, type=str, default="1.0", help="Version of the release.")
@click.option('--associated-publication', required=False, multiple=True, type=str, help="Associated publications for the release.")
@click.option('--conditions-of-access', required=False, type=str, help="Conditions of access for the release.")
@click.option('--copyright-notice', required=False, type=str, help="Copyright notice for the release.")
@click.option('--doi', required=False, type=str, help="DOI identifier for the release.")
@click.option('--publisher', required=False, type=str, help="Publisher of the release.")
@click.option('--principal-investigator', required=False, type=str, help="Principal investigator for the release.")
@click.option('--contact-email', required=False, type=str, help="Contact email for the release.")
@click.option('--funder', required=False, type=str, help="Funder of the release.")
@click.option('--usage-info', required=False, type=str, help="Usage information for the release.")
@click.option('--content-size', required=False, type=str, help="Content size of the release.")
@click.option('--citation', required=False, type=str, help="Citation for the release.")
@click.option('--completeness', required=False, type=str, help="Completeness information for the release.")
@click.option('--ethical-review', required=False, type=str, help="Ethical review information.")
@click.option('--human-subject', required=False, type=str, help="Human subject involvement information.")
@click.option('--confidentiality-level', required=False, type=str, help="Confidentiality level for the release.")

# Mapped RAI Properties (were previously generic properties)
@click.option('--maintenance-plan', required=False, type=str, help="RAI: Versioning, maintainers, and deprecation policies.")
@click.option('--intended-use', required=False, type=str, help="RAI: Recommended dataset uses (e.g., training, validation).")
@click.option('--limitations', required=False, type=str, help="RAI: Known limitations and non-recommended uses.")
@click.option('--potential-sources-of-bias', required=False, type=str, help="RAI: Description of known biases in the dataset.")
@click.option('--prohibited-uses', required=False, type=str, help="Prohibited uses of the release (appended to Limitations).")

# New Croissant RAI Properties
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

# Other Properties
@click.option('--additional-properties', required=False, type=str, help="JSON string with additional property values.")
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties for the parent crate.')
@click.pass_context
def build_release(
    ctx,
    release_directory: pathlib.Path,
    guid: str,
    name: str,
    organization_name: str,
    project_name: str,
    description: str,
    keywords: List[str],
    license: str,
    date_published: Optional[str],
    author: Optional[str],
    version: str,
    associated_publication: Optional[List[str]],
    conditions_of_access: Optional[str],
    copyright_notice: Optional[str],
    doi: Optional[str],
    publisher: Optional[str],
    principal_investigator: Optional[str],
    contact_email: Optional[str],
    confidentiality_level: Optional[str],
    citation: Optional[str],
    funder: Optional[str],
    usage_info: Optional[str],
    content_size: Optional[str],
    completeness: Optional[str],
    maintenance_plan: Optional[str],
    intended_use: Optional[str],
    limitations: Optional[str],
    prohibited_uses: Optional[str],
    potential_sources_of_bias: Optional[str],
    human_subject: Optional[str],
    ethical_review: Optional[str],
    rai_data_collection: Optional[str],
    rai_data_collection_type: Optional[Tuple[str]],
    rai_missing_data_desc: Optional[str],
    rai_raw_data_source: Optional[str],
    rai_collection_start_date: Optional[str],
    rai_collection_end_date: Optional[str],
    rai_imputation_protocol: Optional[str],
    rai_manipulation_protocol: Optional[str],
    rai_preprocessing_protocol: Optional[Tuple[str]],
    rai_annotation_protocol: Optional[str],
    rai_annotation_platform: Optional[Tuple[str]],
    rai_annotation_analysis: Optional[Tuple[str]],
    rai_sensitive_info: Optional[Tuple[str]],
    rai_social_impact: Optional[str],
    rai_annotations_per_item: Optional[str],
    rai_annotator_demographics: Optional[Tuple[str]],
    rai_machine_annotation_tools: Optional[Tuple[str]],
    additional_properties: Optional[str],
    custom_properties: Optional[str],
):
    """
    Create a 'release' RO-Crate in RELEASE_DIRECTORY, adding Croissant RAI metadata and linking sub-RO-Crates.
    """
    click.echo(f"Starting release process in: {release_directory.resolve()}")
    
    if not release_directory.exists():
        release_directory.mkdir(parents=True, exist_ok=True)
    
    subcrate_metadata = collect_subcrate_metadata(release_directory)

    if author is None:
        combined_authors = subcrate_metadata['authors']
        if combined_authors:
            author = ", ".join(combined_authors)
        else:
            author = "Unknown"
    
    combined_keywords = list(keywords)
    for keyword in subcrate_metadata['keywords']:
        if keyword not in combined_keywords:
            combined_keywords.append(keyword)

    parent_params = {
        "guid": guid,
        "name": name,
        "organizationName": organization_name,
        "projectName": project_name,
        "description": description,
        "keywords": combined_keywords,
        "license": license,
        "datePublished": date_published or datetime.now().isoformat(),
        "author": author,
        "version": version,
        "associatedPublication": associated_publication if associated_publication else None,
        "conditionsOfAccess": conditions_of_access,
        "copyrightNotice": copyright_notice,
        "path": release_directory
    }
    
    # Add standard optional properties
    if doi: parent_params["identifier"] = doi
    if publisher: parent_params["publisher"] = publisher
    if principal_investigator: parent_params["principalInvestigator"] = principal_investigator
    if contact_email: parent_params["contactEmail"] = contact_email
    if confidentiality_level: parent_params["confidentialityLevel"] = confidentiality_level
    if citation: parent_params["citation"] = citation
    if funder: parent_params["funder"] = funder
    if usage_info: parent_params["usageInfo"] = usage_info
    if content_size: parent_params["contentSize"] = content_size
    if ethical_review: parent_params["ethicalReview"] = ethical_review
    
    # Process RAI and other structured properties
    rai_properties = {}

    # Existing RAI properties
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

    # RAI properties
    if rai_data_collection: rai_properties["rai:dataCollection"] = rai_data_collection
    if rai_data_collection_type: rai_properties["rai:dataCollectionType"] = list(rai_data_collection_type)
    if rai_missing_data_desc: rai_properties["rai:dataCollectionMissingData"] = rai_missing_data_desc
    if rai_raw_data_source: rai_properties["rai:dataCollectionRawData"] = rai_raw_data_source
    if rai_imputation_protocol: rai_properties["rai:dataImputationProtocol"] = rai_imputation_protocol
    if rai_manipulation_protocol: rai_properties["rai:dataManipulationProtocol"] = rai_manipulation_protocol
    if rai_preprocessing_protocol: rai_properties["rai:dataPreprocessingProtocol"] = list(rai_preprocessing_protocol)
    if rai_annotation_protocol: rai_properties["rai:dataAnnotationProtocol"] = rai_annotation_protocol
    if rai_annotation_platform: rai_properties["rai:dataAnnotationPlatform"] = list(rai_annotation_platform)
    if rai_annotation_analysis: rai_properties["rai:dataAnnotationAnalysis"] = list(rai_annotation_analysis)
    if rai_sensitive_info: rai_properties["rai:personalSensitiveInformation"] = list(rai_sensitive_info)
    if rai_social_impact: rai_properties["rai:dataSocialImpact"] = rai_social_impact
    if rai_annotations_per_item: rai_properties["rai:annotationsPerItem"] = rai_annotations_per_item
    if rai_annotator_demographics: rai_properties["rai:annotatorDemographics"] = list(rai_annotator_demographics)
    if rai_machine_annotation_tools: rai_properties["rai:machineAnnotationTools"] = list(rai_machine_annotation_tools)
    
    timeframe = []
    if rai_collection_start_date: timeframe.append(rai_collection_start_date)
    if rai_collection_end_date: timeframe.append(rai_collection_end_date)
    if timeframe: rai_properties["rai:dataCollectionTimeframe"] = timeframe
    
    parent_params.update(rai_properties)
    
    # Process remaining generic properties
    additional_props = []
    if completeness:
        additional_props.append({"@type": "PropertyValue", "name": "Completeness", "value": completeness})
    if human_subject:
        additional_props.append({"@type": "PropertyValue", "name": "Human Subject", "value": human_subject})
    
    if additional_properties:
        try:
            add_props = json.loads(additional_properties)
            if isinstance(add_props, list):
                additional_props.extend(add_props)
            else:
                click.echo("ERROR: additional-properties must be a JSON array")
                ctx.exit(1)
        except json.JSONDecodeError:
            click.echo("ERROR: Invalid JSON in --additional-properties")
            ctx.exit(1)
    
    if additional_props:
        parent_params["additionalProperty"] = additional_props

    if custom_properties:
        try:
            custom_props_dict = json.loads(custom_properties)
            if not isinstance(custom_props_dict, dict):
                raise ValueError("Custom properties must be a JSON object")
            parent_params.update(custom_props_dict)
        except json.JSONDecodeError:
            click.echo("ERROR: Invalid JSON in --custom-properties")
            ctx.exit(1)
        except ValueError as e:
             click.echo(f"ERROR: {e}")
             ctx.exit(1)

    try:
        parent_crate_root_dict = GenerateROCrate(**parent_params)
        parent_crate_guid = parent_crate_root_dict['@id']
        click.echo(f"Initialized parent RO-Crate: {parent_crate_guid}")
    except Exception as e:
        click.echo(f"ERROR: Failed to initialize parent RO-Crate: {e}")
        ctx.exit(1)

    linked_ids = LinkSubcrates(parent_crate_path=release_directory)
    if linked_ids:
        click.echo(f"Successfully linked {len(linked_ids)} sub-crate(s):")
        for sub_id in linked_ids:
            click.echo(f"  - {sub_id}")
    else:
        click.echo("No valid sub-crates were found or linked.")

    click.echo(f"Release process finished successfully for: {parent_crate_guid}")
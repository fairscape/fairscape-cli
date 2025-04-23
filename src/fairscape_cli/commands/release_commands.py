import click
import pathlib
import json
from datetime import datetime
from typing import List, Optional
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
@click.option('--confidentiality-level', required=False, type=str, help="Confidentiality level for the release.")
@click.option('--citation', required=False, type=str, help="Citation for the release.")
@click.option('--funder', required=False, type=str, help="Funder of the release.")
@click.option('--usage-info', required=False, type=str, help="Usage information for the release.")
@click.option('--content-size', required=False, type=str, help="Content size of the release.")
@click.option('--completeness', required=False, type=str, help="Completeness information for the release.")
@click.option('--maintenance-plan', required=False, type=str, help="Maintenance plan for the release.")
@click.option('--intended-use', required=False, type=str, help="Intended use of the release.")
@click.option('--limitations', required=False, type=str, help="Limitations of the release.")
@click.option('--prohibited-uses', required=False, type=str, help="Prohibited uses of the release.")
@click.option('--potential-sources-of-bias', required=False, type=str, help="Prohibited uses of the release.")
@click.option('--human-subject', required=False, type=str, help="Human subject involvement information.")
@click.option('--ethical-review', required=False, type=str, help="Ethical review information.")
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
    additional_properties: Optional[str],
    custom_properties: Optional[str],
):
    """
    Create a 'release' RO-Crate in RELEASE_DIRECTORY, scanning for and linking existing sub-RO-Crates.
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
    
    if doi:
        parent_params["identifier"] = doi
    if publisher:
        parent_params["publisher"] = publisher
    if principal_investigator:
        parent_params["principalInvestigator"] = principal_investigator
    if contact_email:
        parent_params["contactEmail"] = contact_email
    if confidentiality_level:
        parent_params["confidentialityLevel"] = confidentiality_level
    if citation:
        parent_params["citation"] = citation
    if funder:
        parent_params["funder"] = funder
    if usage_info:
        parent_params["usageInfo"] = usage_info
    if content_size:
        parent_params["contentSize"] = content_size
    if ethical_review:
        parent_params["ethicalReview"] = ethical_review
    
    additional_props = []
    if completeness:
        additional_props.append({
            "@type": "PropertyValue",
            "name": "Completeness",
            "value": completeness
        })
    if maintenance_plan:
        additional_props.append({
            "@type": "PropertyValue",
            "name": "Maintenance Plan",
            "value": maintenance_plan
        })
    if intended_use:
        additional_props.append({
            "@type": "PropertyValue",
            "name": "Intended Use",
            "value": intended_use
        })
    if limitations:
        additional_props.append({
            "@type": "PropertyValue",
            "name": "Limitations",
            "value": limitations
        })
    if prohibited_uses:
        additional_props.append({
            "@type": "PropertyValue",
            "name": "Prohibited Uses",
            "value": prohibited_uses
        })
    if potential_sources_of_bias:
        additional_props.append({
            "@type": "PropertyValue",
            "name": "Potential Sources of Bias",
            "value": potential_sources_of_bias
        })
    if human_subject:
        additional_props.append({
            "@type": "PropertyValue",
            "name": "Human Subject",
            "value": human_subject
        })
    
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
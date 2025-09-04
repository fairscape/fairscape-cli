import click
import pathlib
import os
import traceback
from pathlib import Path
import json
from typing import Optional, List
from datetime import datetime

from fairscape_cli.datasheet_builder.rocrate.datasheet_generator import DatasheetGenerator
from fairscape_cli.datasheet_builder.evidence_graph.graph_builder import generate_evidence_graph_from_rocrate
from fairscape_cli.datasheet_builder.evidence_graph.html_builder import generate_evidence_graph_html

from fairscape_cli.models import (
    GenerateROCrate,
    LinkSubcrates,
    collect_subcrate_metadata
)

from fairscape_models.rocrate import ROCrateV1_2
from fairscape_models.conversion.converter import ROCToTargetConverter
from fairscape_models.conversion.mapping.croissant import MAPPING_CONFIGURATION as CROISSANT_MAPPING


@click.group('build')
def build_group():
    """Build derived artifacts from RO-Crates (datasheets, previews, graphs, Croissants)."""
    pass

@build_group.command('release')
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

@build_group.command('datasheet')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--output', required=False, type=click.Path(path_type=pathlib.Path), help="Output HTML file path (defaults to ro-crate-datasheet.html in crate dir).")
@click.option('--template-dir', required=False, type=click.Path(exists=True, path_type=pathlib.Path), help="Custom template directory.")
@click.option('--published', is_flag=True, default=False, help="Indicate if the crate is considered published (may affect template rendering).")
@click.pass_context
def build_datasheet(ctx, rocrate_path, output, template_dir, published):
    """Generate an HTML datasheet for an RO-Crate."""

    if rocrate_path.is_dir():
        metadata_file = rocrate_path / "ro-crate-metadata.json"
        crate_dir = rocrate_path
    elif rocrate_path.name == "ro-crate-metadata.json":
        metadata_file = rocrate_path
        crate_dir = rocrate_path.parent
    else:
        click.echo(f"ERROR: Input path must be an RO-Crate directory or a ro-crate-metadata.json file.", err=True)
        ctx.exit(1)

    if not metadata_file.exists():
        click.echo(f"ERROR: Metadata file not found: {metadata_file}", err=True)
        ctx.exit(1)

    output_path = output if output else crate_dir / "ro-crate-datasheet.html"

    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = Path(os.path.join(package_dir, 'datasheet_builder', 'templates'))

    click.echo(f"Generating datasheet for {metadata_file}")
    click.echo(f"Outputting to: {output_path}")

    try:
        generator = DatasheetGenerator(
            json_path=str(metadata_file),
            template_dir=str(template_dir),
            published=published
        )

        generator.process_subcrates()

        final_output_path = generator.save_datasheet(str(output_path))
        click.echo(f"Datasheet generated successfully: {final_output_path}")
    except Exception as e:
        click.echo(f"Error generating datasheet: {str(e)}", err=True)
        traceback.print_exc()
        ctx.exit(1)

@build_group.command('evidence-graph')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=Path))
@click.argument('ark-id', type=str)
@click.option('--output-file', required=False, type=click.Path(path_type=Path), help="Path to save the JSON evidence graph (defaults to provenance-graph.json in the RO-Crate directory)")
@click.pass_context
def generate_evidence_graph(
    ctx,
    rocrate_path: Path,
    ark_id: str,
    output_file: Optional[Path],
):
    """
    Generate an evidence graph from an RO-Crate for a specific ARK identifier.
    
    ROCRATE_PATH can be either a directory containing ro-crate-metadata.json or the metadata file itself.
    ARK_ID is the ARK identifier for which to build the evidence graph.
    """
    # Determine RO-Crate metadata file path
    if rocrate_path.is_dir():
        metadata_file = rocrate_path / "ro-crate-metadata.json"
        if not metadata_file.exists():
            click.echo(f"ERROR: ro-crate-metadata.json not found in {rocrate_path}")
            ctx.exit(1)
    else:
        metadata_file = rocrate_path
    
    # Determine output paths
    crate_dir = metadata_file.parent
    if not output_file:
        output_file = crate_dir / "provenance-graph.json"
    
    # Generate the evidence graph
    try:
        click.echo(f"Generating evidence graph for {ark_id} from {metadata_file}...")
        evidence_graph = generate_evidence_graph_from_rocrate(
            rocrate_path=metadata_file,
            output_path=output_file,
            node_id=ark_id
        )
        click.echo(f"Evidence graph saved to {output_file}")
        
        try:
            html_output_path = output_file.with_suffix('.html')
            click.echo("Generating visualization...")
            result = generate_evidence_graph_html(str(output_file), str(html_output_path))
            
            if result:
                click.echo(f"Visualization saved to {html_output_path}")
            else:
                click.echo("ERROR: Failed to generate visualization")
        except ImportError:
            click.echo("WARNING: generate_evidence_graph_html module not found, skipping visualization")
            click.echo("To generate visualizations, please install the visualization module.")
        except Exception as e:
            click.echo(f"ERROR generating visualization: {str(e)}")\
                    
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            i = 0
            for entity in metadata.get('@graph', []):
                if i == 1:
                    entity['hasEvidenceGraph'] = {
                        "@id": str(html_output_path)
                    }
                    break
                i += 1
            
            # Write the updated metadata back to the file
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            click.echo(f"Added hasEvidenceGraph reference to {ark_id} in RO-Crate metadata")
        except Exception as e:
            click.echo(f"WARNING: Failed to add hasEvidenceGraph reference: {str(e)}")
            
    except Exception as e:
        click.echo(f"ERROR: {str(e)}")
        ctx.exit(1)
        
@build_group.command('croissant')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--output', required=False, type=click.Path(path_type=pathlib.Path), help="Output Croissant JSON file path (defaults to croissant.json in crate dir).")
@click.pass_context
def build_croissant(ctx, rocrate_path, output):
    """Convert an RO-Crate to Croissant JSON-LD format."""

    if rocrate_path.is_dir():
        metadata_file = rocrate_path / "ro-crate-metadata.json"
        crate_dir = rocrate_path
    elif rocrate_path.name == "ro-crate-metadata.json":
        metadata_file = rocrate_path
        crate_dir = rocrate_path.parent
    else:
        click.echo(f"ERROR: Input path must be an RO-Crate directory or a ro-crate-metadata.json file.", err=True)
        ctx.exit(1)

    if not metadata_file.exists():
        click.echo(f"ERROR: Metadata file not found: {metadata_file}", err=True)
        ctx.exit(1)

    output_path = output if output else crate_dir / "croissant.json"

    click.echo(f"Converting RO-Crate to Croissant: {metadata_file}")
    click.echo(f"Outputting to: {output_path}")

    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        source_crate = ROCrateV1_2(**metadata)
        croissant_converter = ROCToTargetConverter(source_crate, CROISSANT_MAPPING)
        croissant_result = croissant_converter.convert()
        
        with open(output_path, 'w') as f:
            json.dump(croissant_result.model_dump(by_alias=True, exclude_none=True), f, indent=2)
        
        click.echo(f"Croissant conversion completed successfully: {output_path}")
    except Exception as e:
        click.echo(f"ERROR: Failed to convert RO-Crate to Croissant: {e}", err=True)
        traceback.print_exc()
        ctx.exit(1)
        
# Placeholder for explicit preview generation
# @build_group.command('preview')
# @click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
# def build_preview(ctx, rocrate_path):
#     """Generate an HTML preview for a specific RO-Crate."""
#     # Implementation using PreviewGenerator
#     pass
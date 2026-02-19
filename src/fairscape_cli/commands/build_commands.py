import click
import pathlib
import os
import traceback
from pathlib import Path
import json
from typing import Optional, List, Tuple
from datetime import datetime

from fairscape_cli.datasheet_builder.rocrate.datasheet_generator import DatasheetGenerator
from fairscape_cli.datasheet_builder.evidence_graph.graph_builder import generate_evidence_graph_from_rocrate
from fairscape_cli.datasheet_builder.evidence_graph.html_builder import generate_evidence_graph_html
from fairscape_cli.utils.build_utils import (
    process_all_subcrates,
    process_croissant,
    process_datasheet,
    process_preview,
    process_subcrate
)

from fairscape_cli.models import (
    GenerateROCrate,
    LinkSubcrates,
    collect_subcrate_metadata,
    collect_subcrate_aggregated_metrics
)

from fairscape_models.rocrate import ROCrateV1_2, ROCrateMetadataElem
from fairscape_models.conversion.converter import ROCToTargetConverter
from fairscape_models.conversion.mapping.croissant import MAPPING_CONFIGURATION as CROISSANT_MAPPING


@click.group('build')
def build_group():
    """Build derived artifacts from RO-Crates (datasheets, previews, graphs, Croissants)."""
    pass

@build_group.command('release')
@click.argument('release-directory', type=click.Path(exists=False, path_type=pathlib.Path, file_okay=False, dir_okay=True))
# Standard Crate Properties
@click.option('--guid', required=False, type=str, default="", show_default=False, help="GUID for the parent release RO-Crate (generated if not provided).")
@click.option('--name', required=True, type=str, help="Name for the parent release RO-Crate.")
@click.option('--organization-name', required=True, type=str, help="Organization name associated with the release.")
@click.option('--project-name', required=True, type=str, help="Project name associated with the release.")
@click.option('--description', required=True, type=str, help="Description of the release RO-Crate.")
@click.option('--keywords', required=True, multiple=True, type=str, help="Keywords for the release RO-Crate.")
@click.option('--license', required=True, type=str, default="https://creativecommons.org/licenses/by/4.0/", help="License URL for the release.")
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

#AI-Ready and other structured properties
@click.option('--completeness', required=False, type=str, help="Completeness information for the release.")
@click.option('--ethical-review', required=False, type=str, help="Ethical review information.")
@click.option('--human-subject', required=False, type=str, help="Human subject involvement information.")
@click.option('--confidentiality-level', required=False, type=str, help="Confidentiality level for the release.")
@click.option('--data-governance', required=False, type=str, help="Data governance information for the release.")
@click.option('--irb', required=False, type=str, help="IRB number for the release.")
@click.option('--has-summary-stats', required=False, type=str, help="Summary statistics for the release.")

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
@click.option('--rai-machine-annotation-tools', required=False, multiple=True, type=str, help="RAI: Software used for automated data annotation.")

# Other Properties
@click.option('--additional-properties', required=False, type=str, help="JSON string with additional property values.")
@click.option('--custom-properties', required=False, type=str, help='JSON string with additional properties for the parent crate.')
@click.option('--skip-subcrate-processing', is_flag=True, default=False, help="Skip automatic processing of subcrates.")
@click.option('--published', is_flag=True, default=False, help="Are the arks live for the release.")
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
    data_governance: Optional[str],
    irb: Optional[str],
    has_summary_stats: Optional[str],
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
    rai_machine_annotation_tools: Optional[Tuple[str]],
    additional_properties: Optional[str],
    custom_properties: Optional[str],
    skip_subcrate_processing: bool,
    published: bool,
):
    """
    Create a 'release' RO-Crate in RELEASE_DIRECTORY, adding Croissant RAI metadata and linking sub-RO-Crates.
    
    Automatically processes subcrates by:
    - Linking inverse properties
    - Adding inputs/outputs
    - Generating evidence graphs
    - Creating Croissant exports
    
    Also generates a datasheet and Croissant for the release itself.
    """
    click.echo(f"Starting release process in: {release_directory.resolve()}")
    
    if not release_directory.exists():
        release_directory.mkdir(parents=True, exist_ok=True)
    
    if not skip_subcrate_processing:
        click.echo("\n=== Processing subcrates ===")
        subcrate_results = process_all_subcrates(release_directory)
    
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

    # Collect aggregated metrics for AI-Ready scoring
    aggregated_metrics = collect_subcrate_aggregated_metrics(release_directory)

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
    if has_summary_stats: parent_params["hasSummaryStats"] = has_summary_stats
    
    # Process RAI and other structured properties
    rai_properties = {}

    # Existing RAI properties
    if limitations:
        rai_properties["rai:dataLimitations"] = limitations
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
    if prohibited_uses:
        additional_props.append({"@type": "PropertyValue", "name": "Prohibited Uses", "value": prohibited_uses})
    if data_governance:
        additional_props.append({"@type": "PropertyValue", "name": "Data Governance Committee", "value": data_governance})
    if irb:
        additional_props.append({"@type": "PropertyValue", "name": "IRB", "value": irb})
    
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

    # Add aggregated metrics as individual properties (following evi: prefix pattern)
    parent_params["evi:datasetCount"] = aggregated_metrics.dataset_count
    parent_params["evi:computationCount"] = aggregated_metrics.computation_count
    parent_params["evi:softwareCount"] = aggregated_metrics.software_count
    parent_params["evi:schemaCount"] = aggregated_metrics.schema_count
    parent_params["evi:totalContentSizeBytes"] = aggregated_metrics.total_content_size_bytes
    parent_params["evi:entitiesWithSummaryStats"] = aggregated_metrics.entities_with_summary_stats
    parent_params["evi:entitiesWithChecksums"] = aggregated_metrics.entities_with_checksums
    parent_params["evi:totalEntities"] = aggregated_metrics.total_entities
    parent_params["evi:formats"] = sorted(list(aggregated_metrics.formats))

    try:
        click.echo("\n=== Creating release RO-Crate ===")
        parent_crate_root_dict = GenerateROCrate(**parent_params)
        parent_crate_guid = parent_crate_root_dict['@id']
        click.echo(f"Initialized parent RO-Crate: {parent_crate_guid}")

        aiready_warnings = ROCrateMetadataElem.model_validate(parent_crate_root_dict).get_aiready_warnings()
        if aiready_warnings:
            click.echo("\nAI-Ready warnings (missing recommended properties):")
            for warning in aiready_warnings:
                click.echo(f"  WARNING: {warning}")
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

    click.echo("\n=== Processing release artifacts ===")
    
    click.echo("Generating release Croissant...")
    if process_croissant(release_directory):
        click.echo("  ✓ Release Croissant generated")
    else:
        click.echo("  WARNING: Failed to generate release Croissant")
    
    click.echo("Generating release datasheet...")
    if process_datasheet(release_directory, published=published):
        click.echo("  ✓ Release datasheet generated")
    else:
        click.echo("  WARNING: Failed to generate release datasheet")

    click.echo(f"\n✓ Release process finished successfully for: {parent_crate_guid}")

@build_group.command('datasheet')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--output', required=False, type=click.Path(path_type=pathlib.Path), help="Output HTML file path (defaults to ro-crate-datasheet.html in crate dir).")
@click.option('--template-dir', required=False, type=click.Path(exists=True, path_type=pathlib.Path), help="Custom template directory.")
@click.option('--published', is_flag=True, default=False, help="Indicate if the crate is considered published (may affect template rendering).")
@click.option('--pdf', is_flag=True, default=False, help="Also generate a PDF version of the datasheet (requires playwright).")
@click.pass_context
def build_datasheet(ctx, rocrate_path, output, template_dir, published, pdf):
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
        click.echo(f"✓ HTML datasheet: {final_output_path}")

        # Generate PDF if requested
        if pdf:
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                click.echo("ERROR: playwright is not installed.", err=True)
                click.echo("Install with:", err=True)
                click.echo("  pip install playwright", err=True)
                click.echo("  playwright install chromium", err=True)
                ctx.exit(1)

            try:
                pdf_output_path = Path(final_output_path).with_suffix('.pdf')
                click.echo(f"Generating PDF datasheet...")

                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page()
                    page.goto(f"file://{Path(final_output_path).absolute()}")
                    page.pdf(path=str(pdf_output_path), format='A4')
                    browser.close()

                click.echo(f"✓ PDF datasheet: {pdf_output_path}")
            except Exception as e:
                click.echo(f"ERROR generating PDF: {str(e)}", err=True)
                click.echo("Make sure playwright is installed:", err=True)
                click.echo("  pip install playwright", err=True)
                click.echo("  playwright install chromium", err=True)
                ctx.exit(1)

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
                    entity['localEvidenceGraph'] = {
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


@build_group.command('preview')
@click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--published', is_flag=True, default=False, help="Indicate if the crate is considered published (affects link rendering).")
@click.pass_context
def build_preview_command(ctx, rocrate_path: pathlib.Path, published: bool):
    """
    Generate a preview HTML file (ro-crate-preview.html) for an RO-Crate.

    This creates a lightweight HTML summary of the RO-Crate that can be
    viewed in a browser. Useful for quickly inspecting crate contents.
    """
    if rocrate_path.is_dir():
        crate_dir = rocrate_path
    elif rocrate_path.name == "ro-crate-metadata.json":
        crate_dir = rocrate_path.parent
    else:
        click.echo(f"ERROR: Input path must be an RO-Crate directory or a ro-crate-metadata.json file.", err=True)
        ctx.exit(1)

    metadata_file = crate_dir / "ro-crate-metadata.json"
    if not metadata_file.exists():
        click.echo(f"ERROR: Metadata file not found: {metadata_file}", err=True)
        ctx.exit(1)

    click.echo(f"Generating preview for: {crate_dir}")

    if process_preview(crate_dir, published=published):
        click.echo(f"Preview generated: {crate_dir / 'ro-crate-preview.html'}")
    else:
        click.echo("ERROR: Failed to generate preview", err=True)
        ctx.exit(1)


@build_group.command('subcrate')
@click.argument('subcrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--release-directory', type=click.Path(exists=True, path_type=pathlib.Path), default=None,
              help="Parent release directory (used for relative paths in evidence graphs).")
@click.option('--published', is_flag=True, default=False, help="Indicate if the crate is considered published.")
@click.pass_context
def build_subcrate_command(ctx, subcrate_path: pathlib.Path, release_directory: Optional[pathlib.Path], published: bool):
    """
    Process a subcrate with all augmentation and build steps.

    This command performs the following steps on a single subcrate:

    \b
    1. Link inverse properties (OWL ontology entailments)
    2. Add EVI:inputs and EVI:outputs to the root dataset
    3. Generate evidence graph (JSON + HTML visualization)
    4. Generate Croissant export (JSON-LD)
    5. Generate preview HTML

    Use this command to fully process a subcrate before or after adding it
    to a release. This is the individual-crate equivalent of the subcrate
    processing that happens during 'build release'.
    """
    if subcrate_path.is_dir():
        crate_dir = subcrate_path
    elif subcrate_path.name == "ro-crate-metadata.json":
        crate_dir = subcrate_path.parent
    else:
        click.echo(f"ERROR: Input path must be an RO-Crate directory or a ro-crate-metadata.json file.", err=True)
        ctx.exit(1)

    metadata_file = crate_dir / "ro-crate-metadata.json"
    if not metadata_file.exists():
        click.echo(f"ERROR: Metadata file not found: {metadata_file}", err=True)
        ctx.exit(1)

    click.echo(f"\n=== Processing subcrate: {crate_dir.name} ===")

    results = process_subcrate(crate_dir, release_directory=release_directory, published=published)

    # Summary
    click.echo(f"\n=== Summary ===")
    click.echo(f"  Link inverses:   {'OK' if results['link_inverses'] else 'FAILED'}")
    click.echo(f"  Add I/O:         {'OK' if results['add_io'] else 'FAILED'}")
    click.echo(f"  Evidence graph:  {'OK' if results['evidence_graph'] else 'SKIPPED/FAILED'}")
    click.echo(f"  Croissant:       {'OK' if results['croissant'] else 'FAILED'}")
    click.echo(f"  Preview:         {'OK' if results['preview'] else 'FAILED'}")

    if results['errors']:
        click.echo(f"\nErrors encountered:")
        for error in results['errors']:
            click.echo(f"  - {error}")
        ctx.exit(1)
    else:
        click.echo(f"\nSubcrate processing completed successfully.")
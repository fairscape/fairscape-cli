import click
import pathlib
import os
import traceback
from pathlib import Path
import json
from typing import Optional

from fairscape_cli.datasheet_builder.rocrate.datasheet_generator import DatasheetGenerator
from fairscape_cli.datasheet_builder.evidence_graph.graph_builder import generate_evidence_graph_from_rocrate
from fairscape_cli.datasheet_builder.evidence_graph.html_builder import generate_evidence_graph_html

@click.group('build')
def build_group():
    """Build derived artifacts from RO-Crates (datasheets, previews, graphs)."""
    pass

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
        
# Placeholder for explicit preview generation
# @build_group.command('preview')
# @click.argument('rocrate-path', type=click.Path(exists=True, path_type=pathlib.Path))
# def build_preview(ctx, rocrate_path):
#     """Generate an HTML preview for a specific RO-Crate."""
#     # Implementation using PreviewGenerator
#     pass
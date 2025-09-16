import json
import pathlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import click

def find_subcrates(release_directory: Path) -> List[Path]:
   subcrates = []
   
   def search_directory(directory: Path):
       for item in directory.iterdir():
           if item.is_dir():
               metadata_file = item / "ro-crate-metadata.json"
               if metadata_file.exists():
                   subcrates.append(item)
               search_directory(item)
   
   search_directory(release_directory)
   return subcrates

def process_link_inverses(subcrate_path: Path, ontology_path: Optional[Path] = None) -> bool:
    from fairscape_cli.entailments.inverse import augment_rocrate_with_inverses, EVI_NAMESPACE
    
    if ontology_path is None:
        import fairscape_cli
        package_root = Path(fairscape_cli.__file__).parent
        ontology_path = package_root / "entailments" / "evi.xml"
        
        if not ontology_path.exists():
            click.echo(f"  WARNING: Default ontology not found for {subcrate_path.name}")
            return False
    
    try:
        success = augment_rocrate_with_inverses(
            rocrate_path=subcrate_path,
            ontology_path=ontology_path,
            default_namespace_prefix=EVI_NAMESPACE
        )
        return success
    except Exception as e:
        click.echo(f"  ERROR linking inverses for {subcrate_path.name}: {e}")
        return False

def process_add_io(subcrate_path: Path) -> bool:
    from fairscape_cli.entailments.find_outputs import add_inputs_outputs_to_rocrate
    
    try:
        success, message = add_inputs_outputs_to_rocrate(subcrate_path)
        if not success:
            click.echo(f"  ERROR adding I/O for {subcrate_path.name}: {message}")
        return success
    except Exception as e:
        click.echo(f"  ERROR adding I/O for {subcrate_path.name}: {e}")
        return False

def find_first_evi_output(subcrate_path: Path) -> Optional[str]:
    metadata_file = subcrate_path / "ro-crate-metadata.json"
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        graph = metadata.get('@graph', [])
        if len(graph) > 1:
            root_entity = graph[1]
            outputs = root_entity.get('https://w3id.org/EVI#outputs', [])
            
            if outputs:
                if isinstance(outputs, list) and len(outputs) > 0:
                    first_output = outputs[0]
                    if isinstance(first_output, dict):
                        return first_output.get('@id')
                    return first_output
                elif isinstance(outputs, dict):
                    return outputs.get('@id')
                elif isinstance(outputs, str):
                    return outputs
        
        return None
    except Exception:
        return None
    
def has_local_evidence_graph(subcrate_path: Path) -> bool:
    metadata_file = subcrate_path / "ro-crate-metadata.json"
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        graph = metadata.get('@graph', [])
        if len(graph) > 1:
            root_entity = graph[1]
            local_graph = root_entity.get('localEvidenceGraph')
            if local_graph and isinstance(local_graph, dict) and '@id' in local_graph:
                return True
        
        return False
    except Exception:
        return False

def process_evidence_graph(subcrate_path: Path, release_directory: Optional[Path] = None) -> bool:
    from fairscape_cli.datasheet_builder.evidence_graph.graph_builder import generate_evidence_graph_from_rocrate
    from fairscape_cli.datasheet_builder.evidence_graph.html_builder import generate_evidence_graph_html
    
    if has_local_evidence_graph(subcrate_path):
        return True
    
    first_output = find_first_evi_output(subcrate_path)
    if not first_output:
        return False
    
    metadata_file = subcrate_path / "ro-crate-metadata.json"
    output_json = subcrate_path / "provenance-graph.json"
    output_html = subcrate_path / "provenance-graph.html"
    
    try:
        evidence_graph = generate_evidence_graph_from_rocrate(
            rocrate_path=metadata_file,
            output_path=output_json,
            node_id=first_output
        )
        
        try:
            result = generate_evidence_graph_html(str(output_json), str(output_html))
            if not result:
                click.echo(f"  WARNING: Failed to generate visualization for {subcrate_path.name}")
        except Exception:
            pass
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        if len(metadata.get('@graph', [])) > 1:
            if release_directory:
                relative_path = output_html.relative_to(release_directory).as_posix()
            else:
                relative_path = output_html.name
            
            metadata['@graph'][1]['localEvidenceGraph'] = {
                "@id": relative_path
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        return True
        
    except Exception as e:
        click.echo(f"  ERROR generating evidence graph for {subcrate_path.name}: {e}")
        return False

def process_croissant(crate_path: Path) -> bool:
    from fairscape_models.rocrate import ROCrateV1_2
    from fairscape_models.conversion.converter import ROCToTargetConverter
    from fairscape_models.conversion.mapping.croissant import MAPPING_CONFIGURATION as CROISSANT_MAPPING
    
    metadata_file = crate_path / "ro-crate-metadata.json"
    output_path = crate_path / "croissant.json"
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        source_crate = ROCrateV1_2(**metadata)
        croissant_converter = ROCToTargetConverter(source_crate, CROISSANT_MAPPING)
        croissant_result = croissant_converter.convert()
        
        with open(output_path, 'w') as f:
            json.dump(croissant_result.model_dump(by_alias=True, exclude_none=True), f, indent=2)
        
        return True
    except Exception as e:
        click.echo(f"  ERROR generating Croissant for {crate_path.name}: {e}")
        return False

def process_datasheet(crate_path: Path, published: bool = False) -> bool:
    from fairscape_cli.datasheet_builder.rocrate.datasheet_generator import DatasheetGenerator
    
    metadata_file = crate_path / "ro-crate-metadata.json"
    output_path = crate_path / "ro-crate-datasheet.html"
    
    try:
        import fairscape_cli
        package_dir = Path(fairscape_cli.__file__).parent
        template_dir = package_dir / 'datasheet_builder' / 'templates'
        
        generator = DatasheetGenerator(
            json_path=str(metadata_file),
            template_dir=str(template_dir),
            published=published
        )
        
        generator.process_subcrates()
        generator.save_datasheet(str(output_path))
        
        return True
    except Exception as e:
        click.echo(f"  ERROR generating datasheet for {crate_path.name}: {e}")
        return False

def process_all_subcrates(release_directory: Path) -> Dict[str, Any]:
    subcrates = find_subcrates(release_directory)
    
    results = {
        'total': len(subcrates),
        'processed': {
            'link_inverses': 0,
            'add_io': 0,
            'evidence_graphs': 0,
            'croissants': 0
        },
        'errors': []
    }
    
    if not subcrates:
        click.echo("No subcrates found to process.")
        return results
    
    click.echo(f"\nProcessing {len(subcrates)} subcrate(s)...")
    
    for subcrate in subcrates:
        click.echo(f"\n  Processing subcrate: {subcrate.name}")
        
        click.echo(f"    - Linking inverses...")
        if process_link_inverses(subcrate):
            results['processed']['link_inverses'] += 1
            click.echo(f"      ✓ Inverses linked")
        else:
            results['errors'].append(f"{subcrate.name}: Failed to link inverses")
        
        click.echo(f"    - Adding inputs/outputs...")
        if process_add_io(subcrate):
            results['processed']['add_io'] += 1
            click.echo(f"      ✓ Inputs/outputs added")
        else:
            results['errors'].append(f"{subcrate.name}: Failed to add I/O")
        
        click.echo(f"    - Checking evidence graph...")
        if process_evidence_graph(subcrate, release_directory):
            results['processed']['evidence_graphs'] += 1
            click.echo(f"      ✓ Evidence graph ready")
        else:
            click.echo(f"      - No EVI:outputs found or graph generation failed")
        
        click.echo(f"    - Generating Croissant...")
        if process_croissant(subcrate):
            results['processed']['croissants'] += 1
            click.echo(f"      ✓ Croissant generated")
        else:
            results['errors'].append(f"{subcrate.name}: Failed to generate Croissant")
    
    click.echo(f"\nSubcrate processing complete:")
    click.echo(f"  - Inverses linked: {results['processed']['link_inverses']}/{results['total']}")
    click.echo(f"  - I/O added: {results['processed']['add_io']}/{results['total']}")
    click.echo(f"  - Evidence graphs: {results['processed']['evidence_graphs']}/{results['total']}")
    click.echo(f"  - Croissants: {results['processed']['croissants']}/{results['total']}")
    
    if results['errors']:
        click.echo(f"\nEncountered {len(results['errors'])} error(s):")
        for error in results['errors']:
            click.echo(f"  - {error}")
    
    return results
import click
import pathlib
import os
import runpy
from typing import List

from fairscape_cli.tracking.io_capture import IOCapture
from fairscape_cli.tracking.provenance_tracker import ProvenanceTracker
from fairscape_cli.tracking.config import ProvenanceConfig, TrackerConfig
from fairscape_cli.tracking.metadata_generator import create_metadata_generator


@click.command('track')
@click.argument('script-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--rocrate-path', type=click.Path(path_type=pathlib.Path), default=None, help='Path to RO-Crate directory (default: current directory)')
@click.option('--author', type=str, default="Unknown", help='Author name (default: from RO-Crate or "Unknown")')
@click.option('--keywords', multiple=True, default=["computation"], help='Keywords for metadata (default: from RO-Crate or ["computation"])')
@click.option('--input', 'manual_inputs', multiple=True, help='Manual input files to track')
@click.option('--no-llm', is_flag=True, default=False, help='Disable LLM-based description generation')
@click.option('--execution-name', type=str, default=None, help='Name for this execution (default: script filename)')
@click.pass_context
def track(
    ctx,
    script_path: pathlib.Path,
    rocrate_path: pathlib.Path,
    author: str,
    keywords: List[str],
    manual_inputs: List[str],
    no_llm: bool,
    execution_name: str
):
    """Track execution of a Python script and generate provenance metadata.
    
    Executes SCRIPT_PATH while capturing file I/O operations, then generates
    RO-Crate metadata documenting the computation, software, input datasets,
    and output datasets.
    
    Examples:
    
        fairscape-cli track analysis.py
        
        fairscape-cli track analysis.py --author "Jane Doe" --keywords ml analysis
        
        fairscape-cli track analysis.py --rocrate-path ./my-crate --input config.json
        
        fairscape-cli track analysis.py --no-llm --author "John Smith"
    """
    
    rocrate_path = rocrate_path or pathlib.Path.cwd()
    
    if not script_path.exists():
        click.echo(f"ERROR: Script file not found: {script_path}", err=True)
        ctx.exit(code=1)
    
    try:
        with script_path.open('r') as f:
            code = f.read()
    except Exception as exc:
        click.echo(f"ERROR: Could not read script file: {exc}", err=True)
        ctx.exit(code=1)
    
    tracker_config = TrackerConfig()
    
    original_cwd = pathlib.Path.cwd()
    script_dir = script_path.parent.resolve()
    
    try:
        os.chdir(script_dir)
        
        with IOCapture(config=tracker_config) as capture:
            try:
                runpy.run_path(str(script_path), run_name='__main__')
            except SystemExit as e:
                if e.code != 0:
                    click.echo(f"WARNING: Script exited with code {e.code}", err=True)
            except Exception as exc:
                click.echo(f"ERROR: Script execution failed: {exc}", err=True)
                ctx.exit(code=1)
    finally:
        os.chdir(original_cwd)
    
    if not capture.inputs and not capture.outputs and not manual_inputs:
        click.echo("WARNING: No file I/O detected in script execution", err=True)
        click.echo("No metadata generated.", err=True)
        return
    
    use_llm = not no_llm and os.environ.get("GEMINI_API_KEY")
    
    metadata_generator = None
    if use_llm:
        from datetime import datetime
        try:
            metadata_generator = create_metadata_generator(
                provider="gemini",
                timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
            )
        except Exception as exc:
            click.echo(f"WARNING: Could not initialize LLM metadata generator: {exc}", err=True)
            click.echo("Falling back to simple descriptions", err=True)
    
    provenance_config = ProvenanceConfig(
        rocrate_path=rocrate_path,
        author=author,
        keywords=list(keywords),
        manual_inputs=list(manual_inputs),
        use_llm=use_llm
    )
    
    try:
        tracker = ProvenanceTracker(
            config=provenance_config,
            metadata_generator=metadata_generator
        )
        
        exec_name = execution_name or script_path.stem
        
        result = tracker.track_execution(code, capture, execution_name=exec_name)
        
        click.echo(result.computation_guid)
        
        if ctx.obj and ctx.obj.get('verbose'):
            click.echo(f"\nTracking Summary:", err=True)
            click.echo(f"  Software: {result.software_guid}", err=True)
            click.echo(f"  Inputs: {result.input_count} datasets ({result.reused_count} reused)", err=True)
            click.echo(f"  Outputs: {result.output_count} datasets", err=True)
        
    except ValueError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        ctx.exit(code=1)
    except RuntimeError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        ctx.exit(code=1)
    except Exception as exc:
        click.echo(f"ERROR: Tracking failed: {exc}", err=True)
        ctx.exit(code=1)
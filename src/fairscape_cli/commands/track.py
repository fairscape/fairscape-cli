import click
import pathlib
import os
import sys
import runpy
from typing import List, Tuple

from fairscape_cli.tracking.io_capture import IOCapture
from fairscape_cli.tracking.provenance_tracker import ProvenanceTracker
from fairscape_cli.tracking.config import ProvenanceConfig, TrackerConfig
from fairscape_cli.tracking.metadata_generator import create_metadata_generator


@click.command('track', context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
))
@click.argument('script-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--rocrate-path', type=click.Path(path_type=pathlib.Path), default=None, help='Path to RO-Crate directory (default: current directory)')
@click.option('--author', type=str, default="Unknown", help='Author name (default: from RO-Crate or "Unknown")')
@click.option('--keywords', multiple=True, default=["computation"], help='Keywords for metadata (default: from RO-Crate or ["computation"])')
@click.option('--input', 'manual_inputs', multiple=True, help='Manual input files to track')
@click.option('--no-llm', is_flag=True, default=False, help='Disable LLM-based description generation')
@click.option('--execution-name', type=str, default=None, help='Name for this execution (default: script filename)')
@click.option('--reference-crate', 'reference_crates', multiple=True, type=click.Path(exists=True, path_type=pathlib.Path), help='Reference RO-Crate(s) to look up existing ARKs for input files')
@click.option('--start-clean', is_flag=True, default=False, help='Clear existing @graph entries (except root) before tracking')
@click.argument('script_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def track(
    ctx,
    script_path: pathlib.Path,
    rocrate_path: pathlib.Path,
    author: str,
    keywords: List[str],
    manual_inputs: List[str],
    no_llm: bool,
    execution_name: str,
    reference_crates: Tuple[pathlib.Path, ...],
    start_clean: bool,
    script_args: Tuple[str, ...]
):
    """Track execution of a Python script and generate provenance metadata.

    Executes SCRIPT_PATH while capturing file I/O operations, then generates
    RO-Crate metadata documenting the computation, software, input datasets,
    and output datasets.

    Script arguments can be passed after the script path and options.

    Examples:

        fairscape-cli track analysis.py

        fairscape-cli track analysis.py --author "Jane Doe" --keywords ml analysis

        fairscape-cli track analysis.py --rocrate-path ./my-crate --input config.json

        fairscape-cli track analysis.py --no-llm --author "John Smith"

        fairscape-cli track script.py -- ./output_dir --inputdir ./input_dir

        fairscape-cli track script.py --reference-crate ./input_data_crate -- ./output --inputdir ./input_data_crate/data
    """
    
    rocrate_path = (rocrate_path or pathlib.Path.cwd()).resolve()

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

    script_path_resolved = script_path.resolve()

    resolved_args = []
    for arg in script_args:
        arg_path = pathlib.Path(arg)
        if arg_path.exists() or (not arg.startswith('-') and ('/' in arg or '\\' in arg)):
            resolved_args.append(str((original_cwd / arg).resolve()))
        else:
            resolved_args.append(arg)

    original_argv = sys.argv
    sys.argv = [str(script_path_resolved)] + resolved_args

    try:
        with IOCapture(config=tracker_config) as capture:
            try:
                runpy.run_path(str(script_path_resolved), run_name='__main__')
            except SystemExit as e:
                if e.code != 0:
                    click.echo(f"WARNING: Script exited with code {e.code}", err=True)
            except Exception as exc:
                click.echo(f"ERROR: Script execution failed: {exc}", err=True)
                ctx.exit(code=1)
    finally:
        sys.argv = original_argv

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
        use_llm=use_llm,
        reference_crates=list(reference_crates),
        start_clean=start_clean
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
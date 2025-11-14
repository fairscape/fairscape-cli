import os
import pathlib
import argparse
from IPython.core.magic import register_cell_magic
from IPython import get_ipython

from fairscape_cli.tracking.io_capture import IOCapture
from fairscape_cli.tracking.provenance_tracker import ProvenanceTracker
from fairscape_cli.tracking.config import ProvenanceConfig, TrackerConfig
from fairscape_cli.tracking.metadata_generator import create_metadata_generator


def parse_magic_arguments(line: str) -> argparse.Namespace:
    """Parse arguments from magic command line."""
    parser = argparse.ArgumentParser(description='Track Jupyter cell execution')
    parser.add_argument('command', nargs='?', default=None)
    parser.add_argument('--rocrate-path', type=str, default=None)
    parser.add_argument('--author', type=str, default="Unknown")
    parser.add_argument('--keywords', nargs='+', default=["jupyter", "computation"])
    parser.add_argument('--input', nargs='+', default=[], dest='manual_inputs')
    parser.add_argument('--no-llm', action='store_true', help='Disable LLM descriptions')
    
    args_list = line.split()
    
    try:
        args = parser.parse_args(args_list)
    except SystemExit:
        print("Usage: %%fairscape track [--rocrate-path PATH] [--author AUTHOR] [--keywords KW1 KW2] [--input FILE1 FILE2] [--no-llm]")
        raise
    
    return args


def execute_cell_safely(cell: str) -> bool:
    """Execute cell and return success status."""
    ip = get_ipython()
    result = ip.run_cell(cell)
    
    if result.error_in_exec:
        print("ERROR: Cell execution failed")
        return False
    
    return True


@register_cell_magic
def fairscape(line, cell):
    """
    Jupyter cell magic for tracking computational provenance.
    
    Usage:
        %%fairscape track [options]
        <your code here>
    
    Options:
        --rocrate-path PATH    Path to RO-Crate directory (default: current directory)
        --author AUTHOR        Author name (default: from RO-Crate or "Unknown")
        --keywords KW1 KW2     Keywords for metadata (default: from RO-Crate or ["jupyter", "computation"])
        --input FILE1 FILE2    Manual input files to track
        --no-llm               Disable LLM-based description generation
    """
    args = parse_magic_arguments(line)
    
    if args.command != 'track':
        print("Usage: %%fairscape track [options]")
        return
    
    rocrate_path = pathlib.Path(args.rocrate_path) if args.rocrate_path else pathlib.Path.cwd()
    
    tracker_config = TrackerConfig()
    
    with IOCapture(config=tracker_config) as capture:
        if not execute_cell_safely(cell):
            return
    
    use_llm = not args.no_llm and os.environ.get("GEMINI_API_KEY")
    
    metadata_generator = None
    if use_llm:
        from datetime import datetime
        metadata_generator = create_metadata_generator(
            provider="gemini",
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        )
    
    provenance_config = ProvenanceConfig(
        rocrate_path=rocrate_path,
        author=args.author,
        keywords=args.keywords,
        manual_inputs=args.manual_inputs,
        use_llm=use_llm
    )
    
    try:
        tracker = ProvenanceTracker(
            config=provenance_config,
            metadata_generator=metadata_generator
        )
        
        result = tracker.track_execution(cell, capture)
        
    except Exception as e:
        print(f"ERROR: Tracking failed: {e}")
        raise

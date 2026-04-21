"""`fairscape interpret` Click subcommand.

Wires the four local adapters (LocalGraphSource, LocalResultSink,
InMemoryTaskTracker, LocalSoftwareFetcher) into the shared
`Condenser` + `Interpreter` orchestrators and runs the pipeline
against an on-disk RO-Crate, writing the AnnotatedEvidenceGraph as a
sidecar JSON.
"""

from __future__ import annotations

import logging
import pathlib
import re
import sys

import click

from fairscape_interpret.condenser import Condenser
from fairscape_interpret.interpreter import InterpretConfig, Interpreter
from fairscape_interpret.pipeline.graph_utils import _is_rocrate_root

from fairscape_cli.interpret.local_graph import LocalGraphSource
from fairscape_cli.interpret.local_sink import LocalResultSink
from fairscape_cli.interpret.local_software import LocalSoftwareFetcher
from fairscape_cli.interpret.local_tracker import InMemoryTaskTracker
from fairscape_cli.models.rocrate import ReadROCrateMetadata


@click.group("interpret")
def interpret_group():
    """AI-driven interpretation of a local RO-Crate."""
    pass


@interpret_group.command("run")
@click.argument(
    "rocrate_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=pathlib.Path),
)
@click.option(
    "--reference",
    "references",
    multiple=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=pathlib.Path),
    help="Additional RO-Crate path whose @graph should be indexed for cross-crate ARK lookups. Repeatable.",
)
@click.option(
    "--llm-model",
    default="google-gla:gemini-2.5-flash-lite",
    show_default=True,
    help="pydantic-ai model identifier used for computation annotation and graph synthesis.",
)
@click.option(
    "--temperature",
    type=float,
    default=0.2,
    show_default=True,
)
@click.option(
    "--max-workers",
    type=int,
    default=2,
    show_default=True,
    help="Maximum parallel LLM annotation workers.",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    default=None,
    help="Where to write the AnnotatedEvidenceGraph sidecar. Default: ./<rocrate-name>-interpretation.json",
)
@click.option(
    "--save-condensed",
    "condensed_output_path",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    default=None,
    help="Also write the condensed RO-Crate produced by the Condenser pre-step to this path.",
)
@click.option(
    "--debug-llm",
    is_flag=True,
    default=False,
    help="Append every raw LLM response to <output>.llm-trace.jsonl.",
)
@click.option("--quiet", is_flag=True, default=False, help="Suppress progress output.")
def interpret_command(
    rocrate_path: pathlib.Path,
    references: tuple[pathlib.Path, ...],
    llm_model: str,
    temperature: float,
    max_workers: int,
    output_path: pathlib.Path | None,
    condensed_output_path: pathlib.Path | None,
    debug_llm: bool,
    quiet: bool,
):
    """Run AI interpretation over an RO-Crate on disk."""
    if not quiet:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    primary_metadata = ReadROCrateMetadata(rocrate_path)
    rocrate_id, rocrate_name = _find_root(primary_metadata, rocrate_path)

    if output_path is None:
        slug = _slugify(rocrate_name or rocrate_id.rsplit("/", 1)[-1] or "rocrate")
        output_path = pathlib.Path.cwd() / f"{slug}-interpretation.json"

    debug_llm_path: pathlib.Path | None = None
    if debug_llm:
        debug_llm_path = output_path.with_suffix(output_path.suffix + ".llm-trace.jsonl")

    if not quiet:
        click.echo(f"Interpreting {rocrate_id}")
        click.echo(f"  primary crate: {rocrate_path}")
        for ref in references:
            click.echo(f"  reference:     {ref}")
        click.echo(f"  output:        {output_path}")
        if condensed_output_path is not None:
            click.echo(f"  condensed out: {condensed_output_path}")
        if debug_llm_path is not None:
            click.echo(f"  llm trace:     {debug_llm_path}")

    graph = LocalGraphSource(rocrate_path, references)
    sink = LocalResultSink(output_path, condensed_output_path)
    tracker = InMemoryTaskTracker(quiet=quiet, debug_llm_path=debug_llm_path)
    software = LocalSoftwareFetcher(graph)
    condenser = Condenser(graph, sink)
    config = InterpretConfig(
        llm_model=llm_model,
        temperature=temperature,
        max_workers=max_workers,
    )
    interpreter = Interpreter(graph, sink, tracker, software, condenser, config)

    try:
        aeg_id = interpreter.run_sync(rocrate_id)
    except Exception as e:
        click.echo(f"Interpretation failed: {e}", err=True)
        sys.exit(1)

    if not quiet:
        click.echo(f"\nAnnotatedEvidenceGraph: {aeg_id}")
        click.echo(f"Wrote sidecar: {output_path}")


def _find_root(
    metadata: dict, rocrate_path: pathlib.Path
) -> tuple[str, str]:
    """Locate the RO-Crate root node in the primary crate @graph and
    return its (@id, name). Raises if no root node is found."""
    graph = metadata.get("@graph", []) or []
    for node in graph:
        if _is_rocrate_root(node):
            node_id = node.get("@id")
            if not node_id:
                continue
            name = node.get("name", "") or ""
            return node_id, name
    raise click.ClickException(
        f"No ROCrate root node found in {rocrate_path}/ro-crate-metadata.json"
    )


def _slugify(value: str) -> str:
    """Cheap filesystem-safe slug. Keeps alnum + `-` + `_`, lowercases,
    collapses whitespace. Good enough for default output filenames."""
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9\-_]", "", value)
    return value or "rocrate"

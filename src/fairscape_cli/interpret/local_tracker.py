"""InMemoryTaskTracker -- TaskTracker adapter for the CLI.

Mirrors the shape of the server's `asyncCollection` task document in
process memory, emits progress lines to stdout (unless `quiet=True`),
and optionally appends raw LLM responses to a JSONL trace file when
`--debug-llm` is set.

Tracker methods never raise: observability is best-effort, never the
reason a pipeline fails.
"""

from __future__ import annotations

import datetime
import json
import logging
import pathlib
import sys
from typing import TextIO

import click

logger = logging.getLogger(__name__)


class InMemoryTaskTracker:
    """TaskTracker that prints progress and optionally records LLM dumps."""

    def __init__(
        self,
        *,
        quiet: bool = False,
        debug_llm_path: pathlib.Path | None = None,
        stream: TextIO | None = None,
    ):
        self.quiet = quiet
        self.debug_llm_path = (
            pathlib.Path(debug_llm_path)
            if debug_llm_path is not None
            else None
        )
        self._stream = stream or sys.stdout
        self.state: dict = {
            "completed_computations": 0,
            "total_computations": 0,
            "computation_details": [],
            "llm_results": [],
        }

    # ------------------------------------------------------------------
    # TaskTracker port
    # ------------------------------------------------------------------

    def update(self, updates: dict) -> None:
        changed_step = (
            "current_step" in updates
            and updates["current_step"] != self.state.get("current_step")
        )
        self.state.update(updates)

        if changed_step:
            self._emit(f"[{updates['current_step']}]")

        if "total_computations" in updates:
            n = updates["total_computations"]
            self._emit(f"  Found {n} computation(s)")

        if updates.get("status") in ("SUCCESS", "FAILURE"):
            aeg_id = self.state.get("annotated_evidence_graph_id") or ""
            if updates["status"] == "SUCCESS":
                self._emit(f"  Done. {aeg_id}".rstrip())
            else:
                err = updates.get("error") or self.state.get("error") or {}
                msg = err.get("message", "unknown") if isinstance(err, dict) else str(err)
                self._emit(f"  Failed: {msg}")

    def update_computation_status(self, comp_id: str, updates: dict) -> None:
        for entry in self.state.get("computation_details", []):
            if entry.get("computation_id") == comp_id:
                entry.update(updates)
                break
        status = updates.get("status")
        if status and status not in ("pending", "in_progress"):
            short = comp_id.rsplit("/", 1)[-1]
            self._emit(f"  {status}: {short}")

    def increment_completed(self) -> None:
        self.state["completed_computations"] = (
            self.state.get("completed_computations", 0) + 1
        )
        done = self.state["completed_computations"]
        total = self.state.get("total_computations", 0)
        self._emit(f"  Progress: {done}/{total}")

    def push_llm_result(self, label: str, raw_output: dict) -> None:
        entry = {
            "label": label,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "output": raw_output,
        }
        self.state.setdefault("llm_results", []).append(entry)

        if self.debug_llm_path is not None:
            try:
                self.debug_llm_path.parent.mkdir(parents=True, exist_ok=True)
                with self.debug_llm_path.open("a") as f:
                    f.write(json.dumps(entry, default=str))
                    f.write("\n")
            except Exception as e:
                logger.warning(
                    f"Failed to append LLM trace to {self.debug_llm_path}: {e}"
                )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _emit(self, line: str) -> None:
        if self.quiet:
            return
        click.echo(line, file=self._stream)

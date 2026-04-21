"""LocalResultSink -- ResultSink adapter that writes sidecar JSON only.

Never modifies the source RO-Crate on disk. `persist_aeg` always writes
the full AnnotatedEvidenceGraph to `output_path`. `persist_condensed`
writes the condensed crate only when `condensed_output_path` was
provided via `--save-condensed`; otherwise it holds the metadata in
memory and returns the condensed id without writing.
"""

from __future__ import annotations

import json
import logging
import pathlib
from typing import List

from fairscape_interpret.models.annotated_computation import AnnotatedComputation
from fairscape_interpret.models.annotated_evidence_graph import AnnotatedEvidenceGraph

logger = logging.getLogger(__name__)


class LocalResultSink:
    """ResultSink that writes AEG + optional condensed-crate sidecars."""

    def __init__(
        self,
        output_path: pathlib.Path,
        condensed_output_path: pathlib.Path | None = None,
    ):
        self.output_path = pathlib.Path(output_path)
        self.condensed_output_path = (
            pathlib.Path(condensed_output_path)
            if condensed_output_path is not None
            else None
        )
        self.last_stats: dict = {}
        self.last_condensed_metadata: dict = {}

    def persist_condensed(
        self,
        condensed_id: str,
        condensed_metadata: dict,
        source_rocrate_id: str,
        stats: dict,
    ) -> str:
        self.last_stats = stats or {}
        self.last_condensed_metadata = condensed_metadata

        if self.condensed_output_path is not None:
            self.condensed_output_path.parent.mkdir(parents=True, exist_ok=True)
            with self.condensed_output_path.open("w") as f:
                json.dump(condensed_metadata, f, indent=2, default=str)
            logger.info(
                f"Wrote condensed RO-Crate {condensed_id} to "
                f"{self.condensed_output_path}"
            )

        return condensed_id

    def persist_aeg(
        self,
        aeg: AnnotatedEvidenceGraph,
        rocrate_id: str,
        step_annotations: List[AnnotatedComputation],
    ) -> str:
        payload = aeg.model_dump(by_alias=True, mode="json")

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w") as f:
            json.dump(payload, f, indent=2, default=str)

        logger.info(
            f"Wrote AnnotatedEvidenceGraph {aeg.guid} to {self.output_path} "
            f"({len(step_annotations)} step annotation(s))"
        )
        return aeg.guid

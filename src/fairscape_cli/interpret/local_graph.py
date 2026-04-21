"""LocalGraphSource -- GraphSource adapter backed by on-disk RO-Crates.

Loads a primary RO-Crate plus any number of `--reference` crates from
local paths via the existing `ReadROCrateMetadata` helper, flattens
every `@graph` entry into a single id-keyed index, and serves the
three `GraphSource` port methods against that index.

Also exposes `crate_dir_for(node_id)` so the sibling
`LocalSoftwareFetcher` can resolve a Software node's `contentUrl`
relative to the crate it was loaded from -- not a port method, just
a CLI-local affordance.
"""

from __future__ import annotations

import logging
import pathlib
import re
from typing import Iterable

from fairscape_interpret.pipeline.graph_utils import flexible_ark_query

from fairscape_cli.models.rocrate import ReadROCrateMetadata

logger = logging.getLogger(__name__)


class LocalGraphSource:
    """GraphSource that indexes primary + reference RO-Crate @graphs.

    Collisions (same @id in multiple crates) resolve to the first-loaded
    node -- the primary crate wins, then references in the order given.
    """

    def __init__(
        self,
        primary_path: pathlib.Path,
        reference_paths: Iterable[pathlib.Path] = (),
    ):
        self.primary_path = pathlib.Path(primary_path)
        self.reference_paths = [pathlib.Path(p) for p in reference_paths]

        self._index: dict[str, dict] = {}
        self._crate_dir: dict[str, pathlib.Path] = {}
        self._dataset_stats: dict[str, dict] = {}

        self._load_crate(self.primary_path)
        for ref in self.reference_paths:
            self._load_crate(ref)

    def _load_crate(self, crate_path: pathlib.Path) -> None:
        """Flatten one crate's @graph into the merged index."""
        crate_dir = (
            crate_path.parent
            if crate_path.is_file()
            else crate_path
        )
        metadata = ReadROCrateMetadata(crate_path)
        graph = metadata.get("@graph", []) or []
        for node in graph:
            node_id = node.get("@id")
            if not node_id or node_id == "ro-crate-metadata.json":
                continue
            if node_id in self._index:
                continue
            self._index[node_id] = node
            self._crate_dir[node_id] = crate_dir

            desc = node.get("descriptiveStatistics")
            split = node.get("splitStatistics")
            if desc or split:
                self._dataset_stats[node_id] = {
                    "descriptiveStatistics": desc or {},
                    "splitStatistics": split or {},
                }

        logger.info(
            f"Loaded {len(graph)} nodes from {crate_path} "
            f"(index size: {len(self._index)})"
        )

    # ------------------------------------------------------------------
    # GraphSource port
    # ------------------------------------------------------------------

    def find_entity(self, ark_id: str) -> dict | None:
        if ark_id in self._index:
            return self._index[ark_id]

        query = flexible_ark_query(ark_id)
        if query is None:
            return None
        pattern = query["@id"]["$regex"]
        regex = re.compile(pattern)
        for candidate_id, node in self._index.items():
            if regex.match(candidate_id):
                return node
        return None

    def find_dataset_stats(self, ark_ids: Iterable[str]) -> dict[str, dict]:
        return {
            aid: self._dataset_stats[aid]
            for aid in ark_ids
            if aid in self._dataset_stats
        }

    def build_full_graph(self, rocrate_id: str) -> list[dict]:
        """BFS from the RO-Crate root, following any id reference that
        resolves in the merged index. Unlike the server's Mongo BFS we
        don't gate on the `"ark:"` prefix -- local crates may reference
        nodes by bare `@id` strings, and our index is authoritative for
        what exists."""
        from fairscape_interpret.pipeline.condense import ARK_REF_FIELDS

        collected: dict[str, dict] = {}
        queue: list[str] = [rocrate_id]

        while queue:
            next_id = queue.pop(0)
            if next_id in collected:
                continue
            node = self._index.get(next_id)
            if node is None:
                continue
            collected[next_id] = node

            for field in ARK_REF_FIELDS:
                val = node.get(field)
                if val is None:
                    continue
                if isinstance(val, dict):
                    refs = [val.get("@id")]
                elif isinstance(val, list):
                    refs = [
                        (item.get("@id") if isinstance(item, dict) else item)
                        for item in val
                    ]
                elif isinstance(val, str):
                    refs = [val]
                else:
                    refs = []
                for ref in refs:
                    if isinstance(ref, str) and ref and ref not in collected:
                        queue.append(ref)

        return list(collected.values())

    # ------------------------------------------------------------------
    # CLI-local affordances (not part of the port)
    # ------------------------------------------------------------------

    def crate_dir_for(self, node_id: str) -> pathlib.Path | None:
        """Return the directory of the RO-Crate this node was loaded
        from, or None if unknown. Used by `LocalSoftwareFetcher` to
        resolve relative `contentUrl` paths."""
        return self._crate_dir.get(node_id)

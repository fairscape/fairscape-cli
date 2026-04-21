"""LocalSoftwareFetcher -- SoftwareFetcher adapter for the CLI.

Resolution order:

  1. `contentUrl` as a filesystem path -- absolute, or relative to the
     directory of the crate the Software node was loaded from.
  2. GitHub fetch via the shared `prefetch_software_code` helper
     (handles file and repo URLs).
  3. `[source not fetched]` placeholder, so annotation continues
     rather than failing the whole run.

Never raises. The server analog lives in `interpret_adapters.py` as
`ServerSoftwareFetcher` -- the CLI variant omits the
`/software/download/` endpoint and bearer-token handling since neither
exists in a local run.
"""

from __future__ import annotations

import logging
import pathlib

from fairscape_interpret.pipeline.github import (
    MAX_SOFTWARE_BYTES,
    prefetch_software_code,
)

from fairscape_cli.interpret.local_graph import LocalGraphSource

logger = logging.getLogger(__name__)

_PLACEHOLDER = "[source not fetched]"


class LocalSoftwareFetcher:
    """SoftwareFetcher that resolves local paths, then GitHub, then a placeholder."""

    def __init__(self, graph: LocalGraphSource):
        self.graph = graph

    def fetch(self, software_node: dict) -> str:
        content_url = software_node.get("contentUrl", "") or ""
        sw_id = software_node.get("@id", "?")

        code = self._fetch_local(sw_id, content_url)
        if code:
            return self._truncate(code, sw_id, source="local")

        if content_url.startswith("http"):
            code = prefetch_software_code(content_url)
            # prefetch_software_code returns bracketed placeholders for
            # non-GitHub URLs and fetch failures -- treat those as a miss
            # so we fall through to our own CLI placeholder.
            if code and not code.startswith("["):
                return self._truncate(code, sw_id, source="github")

        logger.warning(
            f"Software {sw_id}: could not fetch source for contentUrl "
            f"{content_url!r}; using placeholder"
        )
        return _PLACEHOLDER

    def _fetch_local(self, sw_id: str, content_url: str) -> str:
        """Resolve `content_url` to a file on disk.

        FAIRSCAPE RO-Crates store local contentUrls as
        `file:///<crate-relative-path>` -- the `file://` scheme with an
        empty authority, and the path after the third slash is relative
        to the crate root, not absolute on the filesystem. We also
        accept a bare relative path as a fallback for hand-authored
        crates.
        """
        if not content_url:
            return ""

        rel_path = content_url
        if rel_path.startswith("file://"):
            rel_path = rel_path[len("file://"):].lstrip("/")
        elif rel_path.startswith("file:"):
            rel_path = rel_path[len("file:"):].lstrip("/")

        if not rel_path or rel_path.startswith(("http://", "https://")):
            return ""

        crate_dir = self.graph.crate_dir_for(sw_id)
        if crate_dir is None:
            return ""

        candidate = crate_dir / rel_path

        try:
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"Software {sw_id}: failed to read {candidate}: {e}")
        return ""

    @staticmethod
    def _truncate(code: str, sw_id: str, *, source: str) -> str:
        if len(code.encode("utf-8")) > MAX_SOFTWARE_BYTES:
            code = code[:MAX_SOFTWARE_BYTES] + "\n[...truncated...]"
        logger.info(f"Fetched software {sw_id} from {source}: {len(code)} chars")
        return code

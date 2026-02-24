"""
Fetch the top Hugging Face models by download count and register each one into
an existing RO-Crate using the `fairscape rocrate register hf` command.

Example:
    python scripts/import_hf_top_models.py --crate-path "Simple" --limit 100
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import re
from pathlib import Path
from typing import Iterable, List, Optional

try:
    from huggingface_hub import list_models
except ImportError as exc:  # pragma: no cover - runtime dependency notice
    sys.stderr.write("huggingface_hub is required. Install with `pip install huggingface_hub`.\n")
    raise


REPO_ROOT = Path(__file__).resolve().parents[1]


def fetch_top_models(limit: int) -> List[str]:
    """Return the repo_ids for the top downloaded Hugging Face models."""
    repo_ids: List[str] = []
    for model in list_models(sort="downloads", direction=-1, limit=limit):
        repo_id = getattr(model, "modelId", None) or getattr(model, "id", None)
        if repo_id:
            repo_ids.append(repo_id)
    return repo_ids


def _parse_first_list_item(error_text: str) -> Optional[str]:
    """Extract the first item from a list displayed in a validation error."""
    match = re.search(r"input_value=\[([^\]]+)\]", error_text)
    if not match:
        return None
    items_raw = match.group(1).split(",")
    if not items_raw:
        return None
    first = items_raw[0].strip().strip("'\"")
    return first or None


def register_model(repo_id: str, crate_path: Path) -> bool:
    """Run the CLI command that registers a Hugging Face model into an RO-Crate."""
    base_cmd = [
        sys.executable,
        "-m",
        "fairscape_cli",
        "rocrate",
        "register",
        "hf",
        repo_id,
        str(crate_path),
    ]

    def _run(cmd: List[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)

    result = _run(base_cmd)
    if result.returncode == 0:
        sys.stdout.write(f"[OK] {repo_id}: {result.stdout.strip()}\n")
        return True

    error_text = (result.stderr or "") + (result.stdout or "")

    # Auto-retry if common validation errors appear.
    retry_cmd = base_cmd.copy()
    needs_retry = False

    if "baseModel" in error_text:
        base_model_value = _parse_first_list_item(error_text)
        if base_model_value:
            retry_cmd.extend(["--base-model", base_model_value])
            needs_retry = True

    if "license" in error_text:
        license_value = _parse_first_list_item(error_text)
        if license_value:
            retry_cmd.extend(["--license", license_value])
            needs_retry = True

    if "Could not determine model description" in error_text:
        retry_cmd.extend(["--description", "No description provided"])
        needs_retry = True

    if needs_retry:
        retry_result = _run(retry_cmd)
        if retry_result.returncode == 0:
            sys.stdout.write(f"[OK after retry] {repo_id}: {retry_result.stdout.strip()}\n")
            return True
        error_text = (retry_result.stderr or "") + (retry_result.stdout or "")

    sys.stderr.write(f"[FAIL] {repo_id}: {error_text.strip()}\n")
    return False


def validate_crate_path(crate_path: Path) -> Path:
    """Ensure the crate path exists and contains ro-crate-metadata.json."""
    resolved = crate_path if crate_path.is_absolute() else (REPO_ROOT / crate_path).resolve()
    metadata = resolved / "ro-crate-metadata.json"
    if not metadata.exists():
        raise FileNotFoundError(f"ro-crate-metadata.json not found at {metadata}")
    return resolved


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bulk register top Hugging Face models into an RO-Crate.")
    parser.add_argument(
        "--crate-path",
        type=Path,
        default=Path("Simple"),
        help="Path to the existing RO-Crate root (default: ./Simple).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of top downloaded models to register (default: 100).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list the models that would be registered.",
    )
    args = parser.parse_args(argv)

    crate_path = validate_crate_path(args.crate_path)
    repo_ids = fetch_top_models(args.limit)

    if args.dry_run:
        for repo_id in repo_ids:
            print(repo_id)
        return 0

    total = len(repo_ids)
    successes = 0
    for idx, repo_id in enumerate(repo_ids, start=1):
        print(f"({idx}/{total}) Registering {repo_id}...", flush=True)
        if register_model(repo_id, crate_path):
            successes += 1

    print(f"Completed with {successes}/{total} successful registrations.")
    return 0 if successes == total else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Manifest connector.

Reads a CSV manifest + JSON sidecar describing a published dataset that
doesn't have (or doesn't need) a dedicated repository connector, and returns a
ResearchData instance for `ResearchData.to_rocrate()` to write out.

See wizards/manifest-import-design/DESIGN.md for the format spec.
"""
import csv
import json
import os
import pathlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from fairscape_cli.data_fetcher.generic_data.research_data import ResearchData


SIDECAR_REQUIRED_FIELDS = ("name", "description", "authors")
MANIFEST_REQUIRED_COLUMNS = ("name", "description", "contentUrl")
SIZE_UNITS = ("B", "KB", "MB", "GB", "TB", "PB")

# Extensions that should default to Software entities rather than Datasets.
# Mirrors fairscape_cli.data_fetcher.generic_data.connectors.dataverse_connector
# with a few additional script suffixes.
SOFTWARE_EXTENSIONS = {
    ".py", ".r", ".sh", ".bash", ".ipynb", ".jl", ".m",
    ".exe", ".java", ".cpp", ".js", ".jsx", ".ts", ".tsx", ".css",
}


def _auto_detect_type(name: str) -> str:
    """Return 'software' or 'dataset' based on file extension."""
    ext = os.path.splitext(name)[1].lower()
    return "software" if ext in SOFTWARE_EXTENSIONS else "dataset"


def _human_size(n: int) -> str:
    """Format byte count as a short human-readable string matching the other connectors."""
    if n is None:
        return ""
    size = float(n)
    i = 0
    while size >= 1024 and i < len(SIZE_UNITS) - 1:
        size /= 1024.0
        i += 1
    if i == 0:
        return f"{int(size)} {SIZE_UNITS[i]}"
    return f"{size:.1f} {SIZE_UNITS[i]}"


def _ext_format(name: str) -> str:
    """Derive a format token from a filename extension. Returns 'unknown' if there's nothing."""
    ext = os.path.splitext(name)[1].lstrip(".")
    return ext.lower() if ext else "unknown"


def _split_pipe(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [piece.strip() for piece in value.split("|") if piece.strip()]


def _resolve_sidecar(manifest_path: pathlib.Path, explicit: Optional[pathlib.Path]) -> pathlib.Path:
    if explicit is not None:
        if not explicit.exists():
            raise ValueError(f"Sidecar not found: {explicit}")
        return explicit

    siblings = [
        manifest_path.with_suffix(".json"),
        manifest_path.parent / "crate.json",
    ]
    for candidate in siblings:
        if candidate.exists():
            return candidate

    raise ValueError(
        "No sidecar found. Looked for "
        + ", ".join(str(s) for s in siblings)
        + ". Pass --sidecar to point at one explicitly."
    )


def _load_sidecar(path: pathlib.Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    missing = [field for field in SIDECAR_REQUIRED_FIELDS if not data.get(field)]
    if missing:
        raise ValueError(
            f"Sidecar {path} is missing required field(s): {', '.join(missing)}"
        )
    if not isinstance(data.get("authors"), list):
        raise ValueError(f"Sidecar 'authors' must be a list (got {type(data.get('authors')).__name__}).")
    return data


def _row_to_file_dict(row: Dict[str, str], sidecar: Dict[str, Any]) -> Dict[str, Any]:
    """Translate one manifest row into a dict ready for ResearchData.

    The dict carries an extra '_type' key (`'dataset'` or `'software'`) so the
    caller can route it into `ResearchData.files` or `ResearchData.software`.
    The `_type` is sourced from the row's `type` column (case-insensitive),
    falling back to extension-based auto-detection.
    """
    name = (row.get("name") or "").strip()
    if not name:
        raise ValueError(f"Manifest row missing 'name': {row}")

    content_url = (row.get("contentUrl") or "").strip()
    if not content_url:
        raise ValueError(f"Manifest row '{name}' missing 'contentUrl'.")

    declared_type = (row.get("type") or "").strip().lower()
    if declared_type in ("software", "dataset"):
        row_type = declared_type
    elif declared_type == "":
        row_type = _auto_detect_type(name)
    else:
        raise ValueError(
            f"Manifest row '{name}' has unknown type {declared_type!r}; "
            f"expected 'dataset', 'software', or blank."
        )

    description = (row.get("description") or "").strip() or sidecar.get("description") or ""
    fmt = (row.get("format") or "").strip() or _ext_format(name)

    # Size: prefer explicit byte count (we format it); else accept pre-formatted string; else nothing.
    content_size: Optional[str] = None
    size_bytes_raw = (row.get("size_bytes") or "").strip()
    if size_bytes_raw:
        try:
            content_size = _human_size(int(size_bytes_raw))
        except ValueError:
            raise ValueError(f"Manifest row '{name}' has non-integer size_bytes: {size_bytes_raw!r}")
    elif (row.get("contentSize") or "").strip():
        content_size = row["contentSize"].strip()

    file_dict: Dict[str, Any] = {
        "name": name,
        "description": description,
        "contentUrl": content_url,
        "url": content_url,
        "format": fmt,
        "datePublished": (row.get("datePublished") or "").strip() or sidecar.get("publication_date"),
        "version": (row.get("version") or "").strip() or "1.0",
    }

    md5 = (row.get("md5") or "").strip()
    if md5:
        file_dict["md5"] = md5
    sha256 = (row.get("sha256") or "").strip()
    if sha256:
        file_dict["sha256"] = sha256
    if content_size:
        file_dict["contentSize"] = content_size
        # The Dataverse connector also stuffs raw bytes under 'size'; mirror that
        # so anything downstream that reads 'size' keeps working.
        if size_bytes_raw:
            file_dict["size"] = int(size_bytes_raw)

    per_row_keywords = _split_pipe(row.get("keywords"))
    if per_row_keywords:
        file_dict["keywords"] = per_row_keywords

    group = (row.get("group") or "").strip()
    if group:
        # Reserved for future schema-inference grouping; stash it where it'll
        # round-trip without breaking anything.
        file_dict["group"] = group

    file_dict["_type"] = row_type
    return file_dict


def _to_software_dict(record: Dict[str, Any]) -> Dict[str, Any]:
    """Translate a file-dict (built for ResearchData.files) into the shape
    ResearchData.software expects, which `to_rocrate` passes to GenerateSoftware.

    The only meaningful difference is `datePublished` → `dateModified`.
    """
    software = dict(record)
    if "datePublished" in software:
        software["dateModified"] = software.pop("datePublished")
    return software


class ManifestConnector:
    """Reads a CSV manifest + JSON sidecar and produces ResearchData."""

    def __init__(self, sidecar_path: Optional[pathlib.Path] = None):
        self.sidecar_path = pathlib.Path(sidecar_path) if sidecar_path else None

    def fetch_data(self, manifest_path: str, include_files: bool = True) -> ResearchData:
        manifest_p = pathlib.Path(manifest_path)
        if not manifest_p.exists():
            raise ValueError(f"Manifest not found: {manifest_p}")

        sidecar_p = _resolve_sidecar(manifest_p, self.sidecar_path)
        sidecar = _load_sidecar(sidecar_p)

        files_data: List[Dict[str, Any]] = []
        software_data: List[Dict[str, Any]] = []
        if include_files:
            with manifest_p.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                missing_cols = [c for c in MANIFEST_REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
                if missing_cols:
                    raise ValueError(
                        f"Manifest {manifest_p} is missing required column(s): {', '.join(missing_cols)}. "
                        f"Found columns: {reader.fieldnames}"
                    )
                for row in reader:
                    if not any((row.get(c) or "").strip() for c in row):
                        continue  # skip blank lines
                    record = _row_to_file_dict(row, sidecar)
                    row_type = record.pop("_type")
                    if row_type == "software":
                        software_data.append(_to_software_dict(record))
                    else:
                        files_data.append(record)

        publication_date = sidecar.get("publication_date") or datetime.utcnow().date().isoformat()

        metadata: Dict[str, Any] = {}
        if sidecar.get("url"):
            metadata["url"] = sidecar["url"]
        if sidecar.get("associated_publication"):
            metadata["contentUrl"] = sidecar["associated_publication"]
        if sidecar.get("version"):
            metadata["version"] = sidecar["version"]

        return ResearchData(
            repository_name=sidecar.get("repository_name") or "Manifest",
            project_id=sidecar.get("project_id") or sidecar.get("doi") or manifest_p.stem,
            title=sidecar["name"],
            description=sidecar["description"],
            authors=list(sidecar["authors"]),
            license=sidecar.get("license"),
            keywords=list(sidecar.get("keywords") or []),
            publication_date=publication_date,
            doi=sidecar.get("doi"),
            files=files_data,
            software=software_data,
            metadata=metadata,
        )

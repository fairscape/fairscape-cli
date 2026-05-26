"""Richer summary-statistics computation for tabular Datasets in an RO-Crate.

The stdlib row/column counter on `fairscape_models.dataset.Dataset.add_summary_stats`
covers csv/tsv locally with no extra deps. This module is the CLI-side counterpart:
it uses pandas (already a fairscape-cli dependency) for parquet support, per-column
statistics, and `requests` for http(s) `contentUrl` fetching.
"""
import io
import json
import pathlib
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote

import pandas as pd
import requests


TABULAR_EXTENSIONS = {".csv", ".tsv", ".parquet", ".pq"}
TABULAR_FORMAT_TOKENS = ("csv", "tsv", "tab-separated", "parquet")


def is_tabular_entity(entity: Dict[str, Any]) -> bool:
    fmt = (entity.get("format") or entity.get("fileFormat") or "").lower()
    if any(tok in fmt for tok in TABULAR_FORMAT_TOKENS):
        return True
    url = _first_str(entity.get("contentUrl"))
    if url:
        suffix = pathlib.PurePosixPath(url.split("?", 1)[0]).suffix.lower()
        if suffix in TABULAR_EXTENSIONS:
            return True
    return False


def is_dataset(entity: Dict[str, Any]) -> bool:
    t = entity.get("@type")
    types = t if isinstance(t, list) else [t] if t else []
    return any("Dataset" in (s or "") for s in types) and entity.get("additionalType") != "ROCrate"


def resolve_local_path(content_url: str, crate_root: pathlib.Path) -> Optional[pathlib.Path]:
    """Map a `contentUrl` to a local path, or return None if not local."""
    if content_url.startswith(("http://", "https://")):
        return None
    if content_url.startswith("file://"):
        rel = unquote(content_url[len("file://"):]).lstrip("/")
        return crate_root / rel
    p = pathlib.Path(content_url)
    if not p.is_absolute():
        p = crate_root / p
    return p


def read_table(content_url: str, crate_root: pathlib.Path, http_timeout: int = 60) -> Tuple[pd.DataFrame, int, str]:
    """Return (df, byte_size, source_description)."""
    local = resolve_local_path(content_url, crate_root)
    if local is not None:
        if not local.exists():
            raise FileNotFoundError(f"Local contentUrl resolved to missing file: {local}")
        size = local.stat().st_size
        df = _read_path_or_buffer(local, _suffix_of(str(local)))
        return df, size, str(local)

    resp = requests.get(content_url, timeout=http_timeout)
    resp.raise_for_status()
    body = resp.content
    size = len(body)
    df = _read_path_or_buffer(io.BytesIO(body), _suffix_of(content_url.split("?", 1)[0]))
    return df, size, content_url


def compute_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Compact per-column stats. Numeric columns get min/max/mean/std; all get dtype + null_count."""
    cols: List[Dict[str, Any]] = []
    for name in df.columns:
        s = df[name]
        col: Dict[str, Any] = {
            "name": str(name),
            "dtype": str(s.dtype),
            "nullCount": int(s.isna().sum()),
            "uniqueCount": int(s.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            non_null = s.dropna()
            if len(non_null):
                col["min"] = _json_safe(non_null.min())
                col["max"] = _json_safe(non_null.max())
                col["mean"] = _json_safe(non_null.mean())
                col["std"] = _json_safe(non_null.std())
        cols.append(col)
    return {"columns": cols}


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024


def _suffix_of(url_or_path: str) -> str:
    return pathlib.PurePosixPath(url_or_path).suffix.lower()


def _read_path_or_buffer(target, suffix: str) -> pd.DataFrame:
    if suffix in (".parquet", ".pq"):
        return pd.read_parquet(target)
    if suffix == ".tsv":
        return pd.read_csv(target, sep="\t")
    return pd.read_csv(target)


def _first_str(v: Any) -> Optional[str]:
    if isinstance(v, str):
        return v
    if isinstance(v, list) and v:
        return v[0] if isinstance(v[0], str) else None
    return None


def _json_safe(v: Any) -> Any:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def build_summary_dataset(
    source: Dict[str, Any],
    row_count: int,
    column_count: int,
    content_size: str,
    per_column: Dict[str, Any],
) -> Dict[str, Any]:
    """Construct the child SummaryStats Dataset entity (raw dict, ready for @graph)."""
    source_id = source["@id"]
    stats_id = f"{source_id.rstrip('/')}/summary-stats"
    return {
        "@id": stats_id,
        "@type": ["prov:Entity", "https://w3id.org/EVI#Dataset"],
        "additionalType": "Dataset",
        "name": f"{source.get('name', source_id)} — Summary Statistics",
        "author": source.get("author", "fairscape-cli"),
        "description": (
            f"Per-column summary statistics for {source.get('name', source_id)} "
            f"({source_id}). Generated by `fairscape augment summary-stats`."
        ),
        "datePublished": source.get("datePublished", ""),
        "keywords": (source.get("keywords") or []) + ["summary-statistics"],
        "format": "application/json",
        "rowCount": row_count,
        "columnCount": column_count,
        "contentSize": content_size,
        "sampleSize": row_count,
        "derivedFrom": [{"@id": source_id}],
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "perColumnStats", "value": json.dumps(per_column)},
        ],
    }

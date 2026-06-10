from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def prune_none(value: Any) -> Any:
    """Recursively remove None values while preserving defaults and empty containers."""
    if isinstance(value, BaseModel):
        value = value.model_dump(by_alias=True)

    if isinstance(value, dict):
        return {
            key: prune_none(item)
            for key, item in value.items()
            if item is not None
        }

    if isinstance(value, list):
        return [prune_none(item) for item in value if item is not None]

    if isinstance(value, tuple):
        return [prune_none(item) for item in value if item is not None]

    return value


def model_dump_pruned(model: BaseModel, **kwargs: Any) -> dict[str, Any]:
    """Dump a Pydantic model and recursively remove None values."""
    return prune_none(model.model_dump(**kwargs))


def write_json_atomic(path: Path | str, data: Any, indent: int = 2) -> None:
    """Write JSON to ``path`` atomically.

    Writes to a temp file in the same directory and renames it into place, so a
    failure mid-write never leaves a truncated/corrupt file behind.
    """
    path = Path(path)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
        os.replace(tmp_path, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise

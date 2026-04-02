from __future__ import annotations

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

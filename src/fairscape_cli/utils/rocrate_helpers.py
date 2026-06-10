"""Helpers for resolving the root data entity of an RO-Crate @graph.

The root entity is the Dataset the crate describes. Per the RO-Crate spec it is
referenced by the `about` property of the metadata descriptor entry
(`ro-crate-metadata.json`); historically much of this codebase assumed it lived
at index 1 of @graph, which breaks on reordered graphs. These helpers resolve
it properly with graph[1] kept only as a last-resort fallback.
"""
from typing import Any, Dict, List, Optional

from fairscape_models.rocrate import (
    ROCrateV1_2,
    ROCrateMetadataElem,
    ROCrateMetadataFileElem,
)


def get_root_entity_dict(graph: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find the root data entity in a raw @graph list of dicts.

    Resolution order: descriptor `about` reference, then the first entity typed
    as an ROCrate, then graph[1]. Returns the dict from `graph` itself so
    callers may mutate it in place.
    """
    if not graph:
        return None

    descriptor = next(
        (e for e in graph if e.get('@id') == 'ro-crate-metadata.json'),
        None
    )
    if descriptor is None:
        descriptor = next(
            (e for e in graph if str(e.get('@id', '')).endswith('ro-crate-metadata.json')),
            None
        )

    if descriptor is not None:
        about = descriptor.get('about')
        about_id = about.get('@id') if isinstance(about, dict) else about
        if about_id:
            for entity in graph:
                if entity is not descriptor and entity.get('@id') == about_id:
                    return entity

    for entity in graph:
        if entity is descriptor:
            continue
        types = entity.get('@type', [])
        if isinstance(types, str):
            types = [types]
        if any('ROCrate' in str(t) for t in types):
            return entity

    return graph[1] if len(graph) > 1 else None


def get_root_entity(crate: ROCrateV1_2):
    """Find the root data entity model in a parsed ROCrateV1_2, or None."""
    graph = crate.metadataGraph
    if not graph:
        return None

    descriptor = next(
        (item for item in graph if isinstance(item, ROCrateMetadataFileElem)),
        None
    )
    if descriptor is not None and descriptor.about is not None:
        about_id = descriptor.about.guid
        for item in graph:
            if item is not descriptor and getattr(item, 'guid', None) == about_id:
                return item

    for item in graph:
        if isinstance(item, ROCrateMetadataElem):
            return item

    return graph[1] if len(graph) > 1 else None

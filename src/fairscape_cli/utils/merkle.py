"""Merkle tree generation for RO-Crate file integrity verification.

Builds a SHA-256 Merkle tree from all file-backed entities in an RO-Crate's
@graph (those with a contentUrl pointing to a local file). The tree and its
root hash can be used to verify the integrity of the crate's contents.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional


def sha256_file(filepath: Path) -> str:
    """Compute the SHA-256 hex digest of a file, reading in chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_concat(left: str, right: str) -> str:
    """Hash the concatenation of two hex-encoded hashes (as raw bytes)."""
    combined = bytes.fromhex(left) + bytes.fromhex(right)
    return hashlib.sha256(combined).hexdigest()


def build_merkle_tree(leaves: List[Dict]) -> dict:
    """Build a Merkle tree from a list of leaf dicts.

    Args:
        leaves: List of {"contentUrl": str, "sha256": str} dicts, pre-sorted.

    Returns:
        Dict with algorithm, rootHash, leafCount, leaves (indexed), and levels.
    """
    if not leaves:
        empty_hash = hashlib.sha256(b"").hexdigest()
        return {
            "algorithm": "SHA-256",
            "rootHash": empty_hash,
            "leafCount": 0,
            "leaves": [],
            "levels": [[empty_hash]],
        }

    indexed_leaves = [
        {"index": i, "contentUrl": leaf["contentUrl"], "sha256": leaf["sha256"]}
        for i, leaf in enumerate(leaves)
    ]

    # Single leaf: root hash is the leaf hash itself
    if len(leaves) == 1:
        return {
            "algorithm": "SHA-256",
            "rootHash": leaves[0]["sha256"],
            "leafCount": 1,
            "leaves": indexed_leaves,
            "levels": [[leaves[0]["sha256"]]],
        }

    # Extract hashes for tree construction
    current_level = [leaf["sha256"] for leaf in leaves]
    levels = [list(current_level)]

    while len(current_level) > 1:
        # Duplicate last element if odd count
        if len(current_level) % 2 != 0:
            current_level.append(current_level[-1])
            # Update stored level to include the duplicate
            levels[-1] = list(current_level)

        next_level = []
        for i in range(0, len(current_level), 2):
            next_level.append(sha256_concat(current_level[i], current_level[i + 1]))
        current_level = next_level
        levels.append(list(current_level))

    return {
        "algorithm": "SHA-256",
        "rootHash": current_level[0],
        "leafCount": len(leaves),
        "leaves": indexed_leaves,
        "levels": levels,
    }


def resolve_content_url(content_url: str, crate_dir: Path) -> Optional[Path]:
    """Resolve a contentUrl to a local file path.

    Handles bare relative paths and file:// URLs. Returns None for HTTP(S)
    URLs, embargoed entries, or other non-local references.
    """
    if not content_url or not isinstance(content_url, str):
        return None

    stripped = content_url.strip()

    # Skip remote URLs
    if stripped.startswith("http://") or stripped.startswith("https://"):
        return None

    # Skip embargoed or placeholder values
    if stripped.lower() in ("embargoed", ""):
        return None

    # Handle file:// protocol
    if stripped.startswith("file:///"):
        stripped = stripped[len("file:///"):]
    elif stripped.startswith("file://"):
        stripped = stripped[len("file://"):]

    resolved = crate_dir / stripped
    if resolved.is_file():
        return resolved

    return None


def generate_merkle_tree(crate_dir: Path) -> Optional[dict]:
    """Generate a Merkle tree for all local files in an RO-Crate.

    Reads ro-crate-metadata.json, finds entities with contentUrl fields,
    hashes the referenced local files, and builds a Merkle tree.

    Returns the tree dict, or None if no hashable files are found.
    """
    metadata_file = crate_dir / "ro-crate-metadata.json"
    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    graph = metadata.get("@graph", [])
    leaves = []

    for entity in graph:
        content_url = entity.get("contentUrl")
        if content_url is None:
            continue

        # contentUrl can be a string or list of strings
        urls = content_url if isinstance(content_url, list) else [content_url]

        for url in urls:
            filepath = resolve_content_url(url, crate_dir)
            if filepath is not None:
                file_hash = sha256_file(filepath)
                leaves.append({"contentUrl": url, "sha256": file_hash})

    if not leaves:
        return None

    # Sort by contentUrl for deterministic ordering
    leaves.sort(key=lambda x: x["contentUrl"])

    return build_merkle_tree(leaves)

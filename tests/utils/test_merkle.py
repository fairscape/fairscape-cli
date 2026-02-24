"""Tests for Merkle tree generation."""

import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from fairscape_cli.utils.merkle import (
    sha256_file,
    sha256_concat,
    build_merkle_tree,
    resolve_content_url,
    generate_merkle_tree,
)


class TestSha256File:
    def test_known_content(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_bytes(b"hello world")
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert sha256_file(f) == expected

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert sha256_file(f) == expected

    def test_large_file(self, tmp_path):
        """Ensure chunked reading produces the correct hash."""
        content = b"x" * 10000
        f = tmp_path / "large.bin"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert sha256_file(f) == expected


class TestSha256Concat:
    def test_basic(self):
        left = hashlib.sha256(b"aaa").hexdigest()
        right = hashlib.sha256(b"bbb").hexdigest()
        result = sha256_concat(left, right)
        expected = hashlib.sha256(bytes.fromhex(left) + bytes.fromhex(right)).hexdigest()
        assert result == expected

    def test_order_matters(self):
        a = hashlib.sha256(b"a").hexdigest()
        b = hashlib.sha256(b"b").hexdigest()
        assert sha256_concat(a, b) != sha256_concat(b, a)


class TestBuildMerkleTree:
    def test_empty(self):
        tree = build_merkle_tree([])
        assert tree["leafCount"] == 0
        assert tree["algorithm"] == "SHA-256"
        assert tree["rootHash"] == hashlib.sha256(b"").hexdigest()

    def test_single_leaf(self):
        h = hashlib.sha256(b"file1").hexdigest()
        tree = build_merkle_tree([{"contentUrl": "f1.txt", "sha256": h}])
        assert tree["rootHash"] == h
        assert tree["leafCount"] == 1
        assert len(tree["leaves"]) == 1
        assert tree["leaves"][0]["index"] == 0

    def test_two_leaves(self):
        h1 = hashlib.sha256(b"file1").hexdigest()
        h2 = hashlib.sha256(b"file2").hexdigest()
        tree = build_merkle_tree([
            {"contentUrl": "f1.txt", "sha256": h1},
            {"contentUrl": "f2.txt", "sha256": h2},
        ])
        expected_root = sha256_concat(h1, h2)
        assert tree["rootHash"] == expected_root
        assert tree["leafCount"] == 2
        assert len(tree["levels"]) == 2  # leaf level + root level

    def test_three_leaves_odd_duplication(self):
        h1 = hashlib.sha256(b"f1").hexdigest()
        h2 = hashlib.sha256(b"f2").hexdigest()
        h3 = hashlib.sha256(b"f3").hexdigest()
        tree = build_merkle_tree([
            {"contentUrl": "f1", "sha256": h1},
            {"contentUrl": "f2", "sha256": h2},
            {"contentUrl": "f3", "sha256": h3},
        ])
        # h3 gets duplicated, then pairwise: hash(h1,h2), hash(h3,h3), then root
        left = sha256_concat(h1, h2)
        right = sha256_concat(h3, h3)
        expected_root = sha256_concat(left, right)
        assert tree["rootHash"] == expected_root
        assert tree["leafCount"] == 3
        # levels[0] should have 4 entries (3 + 1 duplicate)
        assert len(tree["levels"][0]) == 4

    def test_four_leaves(self):
        hashes = [hashlib.sha256(f"f{i}".encode()).hexdigest() for i in range(4)]
        leaves = [{"contentUrl": f"f{i}", "sha256": h} for i, h in enumerate(hashes)]
        tree = build_merkle_tree(leaves)
        left = sha256_concat(hashes[0], hashes[1])
        right = sha256_concat(hashes[2], hashes[3])
        expected_root = sha256_concat(left, right)
        assert tree["rootHash"] == expected_root
        assert len(tree["levels"]) == 3  # 4 leaves -> 2 -> 1

    def test_deterministic(self):
        leaves = [
            {"contentUrl": "a.txt", "sha256": hashlib.sha256(b"a").hexdigest()},
            {"contentUrl": "b.txt", "sha256": hashlib.sha256(b"b").hexdigest()},
        ]
        tree1 = build_merkle_tree(leaves)
        tree2 = build_merkle_tree(leaves)
        assert tree1["rootHash"] == tree2["rootHash"]


class TestResolveContentUrl:
    def test_relative_path(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("data")
        assert resolve_content_url("data.csv", tmp_path) == f

    def test_nested_relative_path(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        f = d / "file.csv"
        f.write_text("data")
        assert resolve_content_url("data/file.csv", tmp_path) == f

    def test_file_protocol(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("data")
        assert resolve_content_url("file:///test.txt", tmp_path) == f

    def test_http_returns_none(self, tmp_path):
        assert resolve_content_url("https://example.com/file.csv", tmp_path) is None

    def test_embargoed_returns_none(self, tmp_path):
        assert resolve_content_url("Embargoed", tmp_path) is None

    def test_missing_file_returns_none(self, tmp_path):
        assert resolve_content_url("nonexistent.csv", tmp_path) is None

    def test_empty_string_returns_none(self, tmp_path):
        assert resolve_content_url("", tmp_path) is None

    def test_none_returns_none(self, tmp_path):
        assert resolve_content_url(None, tmp_path) is None


class TestGenerateMerkleTree:
    def _make_crate(self, tmp_path, entities):
        """Helper to create a minimal RO-Crate with given entities in @graph."""
        metadata = {
            "@context": {"@vocab": "https://schema.org/"},
            "@graph": [
                {"@id": "ro-crate-metadata.json", "@type": "CreativeWork"},
                {"@id": "ark:test/root", "@type": ["Dataset"], "hasPart": []},
                *entities,
            ],
        }
        metadata_file = tmp_path / "ro-crate-metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)
        return metadata_file

    def test_basic_integration(self, tmp_path):
        # Create actual files
        (tmp_path / "a.txt").write_bytes(b"aaa")
        (tmp_path / "b.txt").write_bytes(b"bbb")

        self._make_crate(tmp_path, [
            {"@id": "ark:test/a", "@type": "Dataset", "contentUrl": "a.txt"},
            {"@id": "ark:test/b", "@type": "Dataset", "contentUrl": "b.txt"},
        ])

        tree = generate_merkle_tree(tmp_path)
        assert tree is not None
        assert tree["leafCount"] == 2
        assert tree["algorithm"] == "SHA-256"
        assert len(tree["rootHash"]) == 64  # hex-encoded SHA-256

    def test_no_content_urls_returns_none(self, tmp_path):
        self._make_crate(tmp_path, [
            {"@id": "ark:test/comp", "@type": "Computation"},
        ])
        assert generate_merkle_tree(tmp_path) is None

    def test_deterministic_ordering(self, tmp_path):
        """Same files, different @graph order -> same root hash."""
        (tmp_path / "x.txt").write_bytes(b"xxx")
        (tmp_path / "y.txt").write_bytes(b"yyy")

        self._make_crate(tmp_path, [
            {"@id": "ark:test/x", "@type": "Dataset", "contentUrl": "x.txt"},
            {"@id": "ark:test/y", "@type": "Dataset", "contentUrl": "y.txt"},
        ])
        tree1 = generate_merkle_tree(tmp_path)

        # Reverse order in @graph
        self._make_crate(tmp_path, [
            {"@id": "ark:test/y", "@type": "Dataset", "contentUrl": "y.txt"},
            {"@id": "ark:test/x", "@type": "Dataset", "contentUrl": "x.txt"},
        ])
        tree2 = generate_merkle_tree(tmp_path)

        assert tree1["rootHash"] == tree2["rootHash"]

    def test_content_url_list(self, tmp_path):
        """contentUrl as a list produces multiple leaves."""
        (tmp_path / "a.txt").write_bytes(b"aaa")
        (tmp_path / "b.txt").write_bytes(b"bbb")

        self._make_crate(tmp_path, [
            {"@id": "ark:test/multi", "@type": "Dataset", "contentUrl": ["a.txt", "b.txt"]},
        ])
        tree = generate_merkle_tree(tmp_path)
        assert tree is not None
        assert tree["leafCount"] == 2

    def test_skips_missing_files(self, tmp_path):
        (tmp_path / "exists.txt").write_bytes(b"data")

        self._make_crate(tmp_path, [
            {"@id": "ark:test/e", "@type": "Dataset", "contentUrl": "exists.txt"},
            {"@id": "ark:test/m", "@type": "Dataset", "contentUrl": "missing.txt"},
        ])
        tree = generate_merkle_tree(tmp_path)
        assert tree is not None
        assert tree["leafCount"] == 1

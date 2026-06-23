# File: tests/commands/build/test_build_commands.py

import pytest
import pathlib
import shutil
import json
from unittest.mock import patch, Mock
from fairscape_cli.__main__ import cli as fairscape_cli_app


@pytest.fixture
def test_release_crate(tmp_path: pathlib.Path):
    """
    Copies the static test release crate into a temporary directory for modification.
    Returns the path to the temporary release crate directory.
    """
    source_crate_dir = pathlib.Path("tests/data/cm4ai-release")
    temp_crate_dir = tmp_path / "cm4ai-release"
    shutil.copytree(source_crate_dir, temp_crate_dir)
    return temp_crate_dir


@pytest.fixture
def empty_crate_dir(tmp_path: pathlib.Path):
    """Create an empty directory without ro-crate-metadata.json"""
    empty_dir = tmp_path / "empty_crate"
    empty_dir.mkdir()
    return empty_dir


@pytest.fixture
def invalid_metadata_file(tmp_path: pathlib.Path):
    """Create a directory with invalid JSON metadata file"""
    crate_dir = tmp_path / "invalid_crate"
    crate_dir.mkdir()
    metadata_file = crate_dir / "ro-crate-metadata.json"
    metadata_file.write_text("invalid json content")
    return crate_dir


@pytest.fixture
def minimal_valid_crate(tmp_path: pathlib.Path):
    """Create a minimal valid RO-Crate for testing"""
    crate_dir = tmp_path / "minimal_crate"
    crate_dir.mkdir()
    metadata = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@type": "CreativeWork",
                "@id": "ro-crate-metadata.json",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": "./"}
            },
            {
                "@type": ["Dataset", "Thing"],
                "@id": "./",
                "name": "Test Dataset"
            }
        ]
    }
    metadata_file = crate_dir / "ro-crate-metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))
    return crate_dir


class TestBuildCommands:
    """Test suite for 'fairscape build' commands."""

    def test_build_datasheet_success(self, runner, test_release_crate: pathlib.Path):
        """
        Test Case: Successfully generate a datasheet for a complex release RO-Crate.
        Command: fairscape build datasheet
        """
        result = runner.invoke(
            fairscape_cli_app,
            [
                "build", "datasheet", str(test_release_crate)
            ]
        )

        assert result.exit_code == 0, f"CLI Error: {result.output}"
        assert "✓ HTML datasheet:" in result.output

        datasheet_path = test_release_crate / "ro-crate-datasheet.html"
        assert datasheet_path.exists()
        assert datasheet_path.stat().st_size > 0

        subcrate_preview_1 = test_release_crate / "Perturb-Seq/cell-atlas/ro-crate-preview.html"
        subcrate_preview_2 = test_release_crate / "mass-spec/cancer-cells/ro-crate-preview.html"
        
        assert subcrate_preview_1.exists()
        assert subcrate_preview_1.stat().st_size > 0
        assert subcrate_preview_2.exists()
        assert subcrate_preview_2.stat().st_size > 0

        datasheet_content = datasheet_path.read_text()
        assert "Cell Maps for Artificial Intelligence - June 2025 Data Release" in datasheet_content
        assert "Perturbation Cell Atlas" in datasheet_content
        assert "Mass Spec" in datasheet_content

    def test_build_datasheet_with_metadata_file_directly(self, runner, test_release_crate: pathlib.Path):
        """Test building datasheet by passing metadata file directly"""
        metadata_file = test_release_crate / "ro-crate-metadata.json"
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "build", "datasheet", str(metadata_file)
            ]
        )

        assert result.exit_code == 0
        assert "✓ HTML datasheet:" in result.output

        datasheet_path = test_release_crate / "ro-crate-datasheet.html"
        assert datasheet_path.exists()

    def test_build_datasheet_nonexistent_path(self, runner):
        """Test building datasheet with nonexistent path"""
        result = runner.invoke(
            fairscape_cli_app,
            [
                "build", "datasheet", "/nonexistent/path"
            ]
        )

        assert result.exit_code == 2

    def test_build_datasheet_invalid_file_type(self, runner, tmp_path):
        """Test building datasheet with invalid file type"""
        invalid_file = tmp_path / "not_metadata.txt"
        invalid_file.write_text("not a metadata file")
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "build", "datasheet", str(invalid_file)
            ]
        )

        assert result.exit_code == 1
        assert "ERROR: Input path must be an RO-Crate directory" in result.output

    def test_build_datasheet_missing_metadata(self, runner, empty_crate_dir: pathlib.Path):
        """Test building datasheet when metadata file is missing"""
        result = runner.invoke(
            fairscape_cli_app,
            [
                "build", "datasheet", str(empty_crate_dir)
            ]
        )

        assert result.exit_code == 1
        assert "ERROR: Metadata file not found" in result.output

    def test_build_datasheet_generation_error(self, runner, minimal_valid_crate: pathlib.Path):
        """Test handling of datasheet generation errors"""
        with patch('fairscape_cli.commands.build_commands.DatasheetGenerator') as mock_generator:
            mock_instance = Mock()
            mock_instance.process_subcrates.side_effect = Exception("Generation failed")
            mock_generator.return_value = mock_instance
            
            result = runner.invoke(
                fairscape_cli_app,
                [
                    "build", "datasheet", str(minimal_valid_crate)
                ]
            )

            assert result.exit_code == 1
            assert "Error generating datasheet" in result.output

    def test_build_evidence_graph_success(self, runner, test_release_crate: pathlib.Path):
        """
        Test Case: Successfully generate an evidence graph for a subcrate.
        Command: fairscape build evidence-graph
        """
        subcrate_path = test_release_crate / "Perturb-Seq" / "cell-atlas"
        subcrate_metadata_path = subcrate_path / "ro-crate-metadata.json"
        
        ark_id = "ark:59852/dataset-kolf-pan-genome-aggregated-data-B9Fd0uujkz"

        result = runner.invoke(
            fairscape_cli_app,
            [
                "build", "evidence-graph", str(subcrate_metadata_path), ark_id
            ]
        )
        
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        assert "Evidence graph saved" in result.output
        assert "Visualization saved" in result.output
        assert "Added hasEvidenceGraph reference" in result.output

        evidence_json_path = subcrate_path / "provenance-graph.json"
        assert evidence_json_path.exists()
        
        with open(evidence_json_path, 'r') as f:
            evidence_data = json.load(f)
        # Phase 4 rewires the CLI to the shared EvidenceGraphBuilder, which
        # derives the graph @id server-style: ark:NAAN/evidence-graph-<postfix>
        # instead of the old CLI's {ark_id}-evidence-graph.
        assert evidence_data["@id"] == "ark:59852/evidence-graph-dataset-kolf-pan-genome-aggregated-data-B9Fd0uujkz"
        assert evidence_data["owner"] == ark_id
        
        evidence_html_path = subcrate_path / "provenance-graph.html"
        assert evidence_html_path.exists()
        assert evidence_html_path.stat().st_size > 0

        with open(subcrate_metadata_path, 'r') as f:
            metadata = json.load(f)

        # The reference must land on the root entity referenced by the
        # ro-crate-metadata.json descriptor's `about`, not blindly @graph[1]
        descriptor = next(
            e for e in metadata['@graph']
            if e['@id'].endswith('ro-crate-metadata.json')
        )
        root_dataset = next(
            e for e in metadata['@graph']
            if e['@id'] == descriptor['about']['@id']
        )
        assert "localEvidenceGraph" in root_dataset
        assert root_dataset["localEvidenceGraph"]["@id"] == str(evidence_html_path)

        # atomic metadata writes must not leave temp files behind
        assert not list(subcrate_path.glob("*.tmp"))

    def test_build_evidence_graph_with_directory(self, runner, test_release_crate: pathlib.Path):
        """Test evidence graph generation with directory path"""
        subcrate_path = test_release_crate / "Perturb-Seq" / "cell-atlas"
        ark_id = "ark:59852/dataset-kolf-pan-genome-aggregated-data-B9Fd0uujkz"

        result = runner.invoke(
            fairscape_cli_app,
            [
                "build", "evidence-graph", str(subcrate_path), ark_id
            ]
        )
        
        assert result.exit_code == 0
        assert "Evidence graph saved" in result.output

    def test_build_evidence_graph_with_custom_output(self, runner, test_release_crate: pathlib.Path):
        """Test evidence graph generation with custom output file"""
        subcrate_path = test_release_crate / "Perturb-Seq" / "cell-atlas"
        subcrate_metadata_path = subcrate_path / "ro-crate-metadata.json"
        custom_output = subcrate_path / "custom-evidence.json"
        ark_id = "ark:59852/dataset-kolf-pan-genome-aggregated-data-B9Fd0uujkz"

        result = runner.invoke(
            fairscape_cli_app,
            [
                "build", "evidence-graph", str(subcrate_metadata_path), ark_id,
                "--output-file", str(custom_output)
            ]
        )
        
        assert result.exit_code == 0
        assert "Evidence graph saved" in result.output
        assert custom_output.exists()

    def test_build_evidence_graph_missing_metadata(self, runner, empty_crate_dir: pathlib.Path):
        """Test evidence graph generation when metadata is missing"""
        ark_id = "test-ark-id"

        result = runner.invoke(
            fairscape_cli_app,
            [
                "build", "evidence-graph", str(empty_crate_dir), ark_id
            ]
        )
        
        assert result.exit_code == 1
        assert "ERROR: ro-crate-metadata.json not found" in result.output

    # The mock-based error-path tests that patched
    # `generate_evidence_graph_from_rocrate` were removed in Phase 4 of the
    # evidence-graph migration -- that function no longer exists, and the
    # replacements (LocalGraphSource + EvidenceGraphBuilder) have no single
    # "generation" patch point to stub out. See EVIDENCE_GRAPH_MIGRATION.md.

    # ------------------------------------------------------------------
    # Phase 5 CLI E2E coverage: start-node type matrix.
    # Backed by the real cm4ai-release/Perturb-Seq/cell-atlas fixture
    # so the builder runs end-to-end through LocalGraphSource / BFS /
    # condensation / LocalResultSink. The DatasetGroup-trigger scenario
    # is covered in the shared-pkg unit tests
    # (fairscape_graph_tools/tests/test_evidence_graph_builder.py) --
    # this fixture's 90+ input datasets are stub refs not present in
    # the crate's @graph, so they become error-stubs rather than
    # clustering into a DatasetGroup.
    # ------------------------------------------------------------------

    def test_build_evidence_graph_from_computation_start(
        self, runner, test_release_crate: pathlib.Path
    ):
        """Computation as the start node: BFS fans out through
        usedDataset / usedSoftware instead of generatedBy."""
        subcrate_path = test_release_crate / "Perturb-Seq" / "cell-atlas"
        subcrate_metadata_path = subcrate_path / "ro-crate-metadata.json"
        ark_id = (
            "ark:59852/computation-perturbation-cell-atlas-"
            "data-processing-Cmx85JtSguG"
        )

        result = runner.invoke(
            fairscape_cli_app,
            ["build", "evidence-graph", str(subcrate_metadata_path), ark_id],
        )
        assert result.exit_code == 0, result.output
        assert "Evidence graph saved" in result.output

        evidence_json_path = subcrate_path / "provenance-graph.json"
        data = json.loads(evidence_json_path.read_text())
        # Derived @id matches the builder's server-style scheme.
        assert data["@id"] == (
            "ark:59852/evidence-graph-computation-perturbation-cell-"
            "atlas-data-processing-Cmx85JtSguG"
        )
        # Start node is in the graph, and BFS followed usedSoftware to the
        # one software node that *is* present in the crate's @graph.
        assert ark_id in data["@graph"]
        start = data["@graph"][ark_id]
        # Computation nodes preserve their used* edges under Phase 2's
        # projection.
        assert "usedSoftware" in start
        sw_ids = [ref["@id"] for ref in start["usedSoftware"]]
        assert "ark:59852/software-10x-genomics-cell-ranger" in sw_ids
        assert (
            "ark:59852/software-10x-genomics-cell-ranger" in data["@graph"]
        )

    def test_build_evidence_graph_from_rocrate_root_start(
        self, runner, test_release_crate: pathlib.Path
    ):
        """RO-Crate root as the start node: outputs derive from the
        crate's `hasOutputs` / `EVI:outputs`, and the start-node entry
        carries a `hasOutputs` annotation (see
        `_build_node_from_cache`'s rocrate-start branch)."""
        subcrate_path = test_release_crate / "Perturb-Seq" / "cell-atlas"
        subcrate_metadata_path = subcrate_path / "ro-crate-metadata.json"
        ark_id = (
            "ark:59852/rocrate-a-perturbation-cell-atlas-of-human-"
            "induced-pluripotent-stem-cells-Cmx85JJSgWm/"
        )

        result = runner.invoke(
            fairscape_cli_app,
            ["build", "evidence-graph", str(subcrate_metadata_path), ark_id],
        )
        assert result.exit_code == 0, result.output
        assert "Evidence graph saved" in result.output

        evidence_json_path = subcrate_path / "provenance-graph.json"
        data = json.loads(evidence_json_path.read_text())
        # The start node is a crate root, so outputs should include *it*
        # plus any crate-level outputs the projection collected.
        output_ids = {o["@id"] for o in data["outputs"]}
        assert ark_id in output_ids
        # The rocrate root entry itself carries the projection-added
        # `hasOutputs` annotation (it's the start-rocrate branch of
        # `_build_node_from_cache`).
        root_entry = data["@graph"][ark_id]
        assert "hasOutputs" in root_entry
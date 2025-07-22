# File: tests/commands/build/test_build_commands.py

import pytest
import pathlib
import shutil
import json
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


class TestBuildCommands:
    """Test suite for 'fairscape build' commands."""

    def test_build_datasheet_success(self, runner, test_release_crate: pathlib.Path):
        """
        Test Case: Successfully generate a datasheet for a complex release RO-Crate.
        Command: fairscape build datasheet
        """
        # The command should operate on the temporary copy of the crate
        result = runner.invoke(
            fairscape_cli_app,
            [
                "build", "datasheet", str(test_release_crate)
            ]
        )

        assert result.exit_code == 0, f"CLI Error: {result.output}"
        assert "Datasheet generated successfully" in result.output
        
        # 1. Verify the main datasheet was created
        datasheet_path = test_release_crate / "ro-crate-datasheet.html"
        assert datasheet_path.exists()
        assert datasheet_path.stat().st_size > 0  # Check it's not empty

        # 2. Verify previews for subcrates were created
        subcrate_preview_1 = test_release_crate / "Perturb-Seq/cell-atlas/ro-crate-preview.html"
        subcrate_preview_2 = test_release_crate / "mass-spec/cancer-cells/ro-crate-preview.html"
        
        assert subcrate_preview_1.exists()
        assert subcrate_preview_1.stat().st_size > 0
        assert subcrate_preview_2.exists()
        assert subcrate_preview_2.stat().st_size > 0

        # 3. (Optional) Spot-check content of the main datasheet
        datasheet_content = datasheet_path.read_text()
        assert "Cell Maps for Artificial Intelligence - June 2025 Data Release" in datasheet_content
        assert "Perturbation Cell Atlas" in datasheet_content # Check if subcrate is listed
        assert "Mass Spec" in datasheet_content


    def test_build_evidence_graph_success(self, runner, test_release_crate: pathlib.Path):
        """
        Test Case: Successfully generate an evidence graph for a subcrate.
        Command: fairscape build evidence-graph
        """
        # We will build the evidence graph for one of the subcrates
        subcrate_path = test_release_crate / "Perturb-Seq" / "cell-atlas"
        subcrate_metadata_path = subcrate_path / "ro-crate-metadata.json"
        
        # The ARK ID for the root of this subcrate
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

        # 1. Verify the JSON evidence graph was created
        evidence_json_path = subcrate_path / "provenance-graph.json"
        assert evidence_json_path.exists()
        
        with open(evidence_json_path, 'r') as f:
            evidence_data = json.load(f)
        assert evidence_data["@id"] == f"{ark_id}-evidence-graph"
        assert evidence_data["owner"] == ark_id
        
        # 2. Verify the HTML visualization was created
        evidence_html_path = subcrate_path / "provenance-graph.html"
        assert evidence_html_path.exists()
        assert evidence_html_path.stat().st_size > 0

        # 3. Verify the original ro-crate-metadata.json was modified to include a link
        with open(subcrate_metadata_path, 'r') as f:
            metadata = json.load(f)
        
        root_dataset = metadata['@graph'][1] 
        assert "hasEvidenceGraph" in root_dataset
        assert root_dataset["hasEvidenceGraph"]["@id"] == str(evidence_html_path)
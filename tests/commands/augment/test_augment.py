import pytest
import pathlib
import json
import shutil
from fairscape_cli.__main__ import cli as fairscape_cli_app


@pytest.fixture
def mass_spec_crate(tmp_path: pathlib.Path):
    """
    Creates a copy of the mass-spec cancer cells RO-Crate for testing augment commands.
    """
    source_metadata = pathlib.Path("tests/data/cm4ai-release/mass-spec/cancer-cells/ro-crate-metadata.json")
    
    crate_dir = tmp_path / "mass-spec-crate"
    crate_dir.mkdir()
    
    metadata_file = crate_dir / "ro-crate-metadata.json"
    shutil.copy2(source_metadata, metadata_file)
    
    return crate_dir


def _load_metadata(crate_path: pathlib.Path):
    """Helper function to load and return metadata from RO-Crate"""
    metadata_path = crate_path / "ro-crate-metadata.json"
    with open(metadata_path, 'r') as f:
        return json.load(f)


class TestAugmentCommands:
    """Test suite for 'fairscape augment' commands."""

    def test_update_entities_change_root_dataset_name(self, runner, mass_spec_crate: pathlib.Path):
        """
        Test updating the root dataset name using MongoDB-style query and update.
        """
        query = '{"@type": {"$in": ["Dataset"]}, "@id": "ark:59852/rocrate-data-from-treated-human-cancer-cells/"}'
        update = '{"$set": {"name": "Updated SEC-MS Dataset - Enhanced Analysis"}}'
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "augment", "update-entities", str(mass_spec_crate),
                "--query", query,
                "--update", update
            ]
        )
        
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        assert "Successfully processed entities" in result.output
        
        metadata = _load_metadata(mass_spec_crate)
        root_dataset = next(
            item for item in metadata["@graph"] 
            if item["@id"] == "ark:59852/rocrate-data-from-treated-human-cancer-cells/"
        )
        assert root_dataset["name"] == "Updated SEC-MS Dataset - Enhanced Analysis"

    def test_update_entities_change_version_all_datasets(self, runner, mass_spec_crate: pathlib.Path):
        """
        Test updating version for all datasets in the crate.
        """
        query = '{"@type": {"$in": ["Dataset"]}, "version": {"$exists": true}}'
        update = '{"$set": {"version": "2.0"}}'
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "augment", "update-entities", str(mass_spec_crate),
                "--query", query,
                "--update", update
            ]
        )
        
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        
        metadata = _load_metadata(mass_spec_crate)
        datasets_with_version = [
            item for item in metadata["@graph"]
            if "Dataset" in (item.get("@type", []) if isinstance(item.get("@type"), list) else [item.get("@type", "")])
            and "version" in item
        ]
        
        for dataset in datasets_with_version:
            assert dataset["version"] == "2.0"

    def test_update_entities_add_new_field_to_instruments(self, runner, mass_spec_crate: pathlib.Path):
        """
        Test adding a new field to all instruments using $set operator.
        """
        query = '{"@type": "https://w3id.org/EVI#Instrument"}'
        update = '{"$set": {"calibrationDate": "2025-01-15", "maintenanceStatus": "verified"}}'
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "augment", "update-entities", str(mass_spec_crate),
                "--query", query,
                "--update", update
            ]
        )
        
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        
        metadata = _load_metadata(mass_spec_crate)
        instruments = [
            item for item in metadata["@graph"]
            if item.get("@type") == "https://w3id.org/EVI#Instrument"
        ]
        
        for instrument in instruments:
            assert instrument["calibrationDate"] == "2025-01-15"
            assert instrument["maintenanceStatus"] == "verified"

    def test_update_entities_modify_experiment_descriptions(self, runner, mass_spec_crate: pathlib.Path):
        """
        Test updating experiment descriptions that contain specific text.
        """
        query = '{"@type": "https://w3id.org/EVI#Experiment", "name": {"$regex": "Control Experiment"}}'
        update = '{"$set": {"description": "Updated: SEC-MS profiling of MDA-MB468 breast cancer cell line with enhanced methodology. Each SEC-MS set is composed of 72 fractions with improved precision."}}'
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "augment", "update-entities", str(mass_spec_crate),
                "--query", query,
                "--update", update
            ]
        )
        
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        
        metadata = _load_metadata(mass_spec_crate)
        control_experiments = [
            item for item in metadata["@graph"]
            if (item.get("@type") == "https://w3id.org/EVI#Experiment" and 
                "Control Experiment" in item.get("name", ""))
        ]
        
        for experiment in control_experiments:
            assert "Updated: SEC-MS profiling" in experiment["description"]
            assert "enhanced methodology" in experiment["description"]

    def test_update_entities_add_keywords_to_samples(self, runner, mass_spec_crate: pathlib.Path):
        """
        Test adding keywords to sample entities using $push operator.
        """
        query = '{"@type": "https://w3id.org/EVI#Sample"}'
        update = '{"$push": {"keywords": {"$each": ["validated", "quality-controlled"]}}}'
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "augment", "update-entities", str(mass_spec_crate),
                "--query", query,
                "--update", update
            ]
        )
        
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        
        metadata = _load_metadata(mass_spec_crate)
        samples = [
            item for item in metadata["@graph"]
            if item.get("@type") == "https://w3id.org/EVI#Sample"
        ]
        
        for sample in samples:
            assert "validated" in sample["keywords"]
            assert "quality-controlled" in sample["keywords"]

    def test_update_entities_invalid_query_json(self, runner, mass_spec_crate: pathlib.Path):
        """
        Test error handling for invalid JSON in query parameter.
        """
        invalid_query = '{"@type": "Dataset", invalid json}'
        update = '{"$set": {"version": "2.0"}}'
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "augment", "update-entities", str(mass_spec_crate),
                "--query", invalid_query,
                "--update", update
            ]
        )
        
        assert result.exit_code == 1
        assert "Invalid JSON in --query string" in result.output

    def test_update_entities_invalid_update_json(self, runner, mass_spec_crate: pathlib.Path):
        """
        Test error handling for invalid JSON in update parameter.
        """
        query = '{"@type": "Dataset"}'
        invalid_update = '{"$set": {"version": "2.0", invalid json}}'
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "augment", "update-entities", str(mass_spec_crate),
                "--query", query,
                "--update", invalid_update
            ]
        )
        
        assert result.exit_code == 1
        assert "Invalid JSON in --update string" in result.output

    def test_update_entities_no_matches(self, runner, mass_spec_crate: pathlib.Path):
        """
        Test behavior when query matches no entities.
        """
        query = '{"@type": "NonExistentType"}'
        update = '{"$set": {"newField": "value"}}'
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "augment", "update-entities", str(mass_spec_crate),
                "--query", query,
                "--update", update
            ]
        )
        
        assert result.exit_code == 0
        assert "No entities were modified" in result.output

    def test_link_inverses_success(self, runner, mass_spec_crate: pathlib.Path):
        """
        Test successful execution of link-inverses command.
        """
        result = runner.invoke(
            fairscape_cli_app,
            [
                "augment", "link-inverses", str(mass_spec_crate)
            ]
        )
        
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        assert f"Augmenting RO-Crate at: {mass_spec_crate}" in result.output
        assert "Primary JSON property namespace:" in result.output

    def test_link_inverses_with_custom_namespace(self, runner, mass_spec_crate: pathlib.Path):
        """
        Test link-inverses with custom namespace parameter.
        """
        custom_namespace = "https://custom.example.org/"
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "augment", "link-inverses", str(mass_spec_crate),
                "--namespace", custom_namespace
            ]
        )
        
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        assert f"Primary JSON property namespace: {custom_namespace}" in result.output

    def test_link_inverses_nonexistent_rocrate_path(self, runner):
        """
        Test link-inverses with nonexistent RO-Crate path.
        """
        nonexistent_path = "/tmp/nonexistent/path"
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "augment", "link-inverses", nonexistent_path
            ]
        )
        
        assert result.exit_code == 2
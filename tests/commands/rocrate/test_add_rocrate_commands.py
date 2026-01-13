import pytest
import pathlib
import json
import os
from click.testing import CliRunner
from fairscape_cli.__main__ import cli as fairscape_cli_app

def _load_and_get_graph_entity(crate_path: pathlib.Path, entity_id: str):
    metadata_path = crate_path / "ro-crate-metadata.json"
    assert metadata_path.exists(), f"Metadata file not found at {metadata_path}"
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    entity = next((item for item in metadata.get("@graph", []) if item.get("@id") == entity_id), None)
    assert entity is not None, f"Entity with id '{entity_id}' not found in @graph"
    return entity

def _get_root_dataset(crate_path: pathlib.Path):
    metadata_path = crate_path / "ro-crate-metadata.json"
    assert metadata_path.exists()
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    root_dataset = next((item for item in metadata.get("@graph", []) if isinstance(item.get("@type", []), list) and "Dataset" in item["@type"] and "https://w3id.org/EVI#ROCrate" in item["@type"]), None)
    assert root_dataset is not None, "RO-Crate root dataset not found"
    return root_dataset

def _print_directory_tree(path: pathlib.Path, prefix=""):
    if path.is_dir():
        children = sorted(path.iterdir())
        for child in children:
            if child.is_dir():
                _print_directory_tree(child, prefix + "  ")

class TestRocrateAddLocal:
    @pytest.fixture(scope="function")
    def test_environment(self, runner: CliRunner, tmp_path: pathlib.Path):
        crate_dir = tmp_path / "test-crate"
        source_dataset_dir = tmp_path / "source_data" / "datasets"
        source_software_dir = tmp_path / "source_data" / "software"
        
        source_dataset_dir.mkdir(parents=True, exist_ok=True)
        source_csv_path = source_dataset_dir / "apms-embeddings.csv"
        source_csv_path.write_text("protein,embedding1,embedding2\nBRCA1,0.1,0.2\nTP53,0.3,0.4")
        
        source_software_dir.mkdir(parents=True, exist_ok=True)
        source_py_path = source_software_dir / "analysis_tool.py"
        source_py_path.write_text("import pandas as pd\nprint('hello world')")

        create_result = runner.invoke(
            fairscape_cli_app,
            [
                "rocrate", "create", str(crate_dir),
                "--name", "Local Add Test Crate",
                "--organization-name", "Test Org",
                "--project-name", "Test Proj",
                "--keywords", "test",
                "--description", "A temporary crate for testing local add commands."
            ],
            catch_exceptions=False
        )
        assert create_result.exit_code == 0, f"Fixture setup failed: {create_result.output}"
        
        yield {
            "crate_dir": crate_dir,
            "source_csv_path": source_csv_path,
            "source_py_path": source_py_path,
            "tmp_path": tmp_path
        }

    def test_add_dataset_to_crate(self, runner: CliRunner, test_environment: dict):
        crate_dir = test_environment["crate_dir"]
        source_csv_path = test_environment["source_csv_path"]
        tmp_path = test_environment["tmp_path"]
        destination_relative_path = "./embeddings.csv"
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = runner.invoke(
                fairscape_cli_app,
                [
                    "rocrate", "add", "dataset", str(crate_dir),
                    "--name", "AP-MS Embeddings",
                    "--author", "Test Lab",
                    "--version", "1.0",
                    "--description", "Embeddings from AP-MS data",
                    "--keywords", "proteomics",
                    "--data-format", "csv",
                    "--date-published", "2023-10-26",
                    "--source-filepath", str(source_csv_path),
                    "--destination-filepath", destination_relative_path,
                ],
                catch_exceptions=False 
            )
            
            assert result.exit_code == 0, f"CLI Error: {result.output}"
            dataset_guid = result.output.strip()
            
            destination_full_path = pathlib.Path(destination_relative_path)
            assert destination_full_path.exists(), f"File was not copied to {destination_full_path}"
            
            dataset_entity = _load_and_get_graph_entity(crate_dir, dataset_guid)
            assert dataset_entity["contentUrl"] == 'file:///embeddings.csv'
            root_dataset = _get_root_dataset(crate_dir)
            assert {"@id": dataset_guid} in root_dataset.get("hasPart", [])
        
        finally:
            os.chdir(original_cwd)

    def test_add_software_to_crate(self, runner: CliRunner, test_environment: dict):
        crate_dir = test_environment["crate_dir"]
        source_py_path = test_environment["source_py_path"]
        tmp_path = test_environment["tmp_path"]
        destination_relative_path = "./analysis_tool.py"
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = runner.invoke(
                fairscape_cli_app,
                [
                    "rocrate", "add", "software", str(crate_dir),
                    "--name", "Analysis Tool",
                    "--author", "Test Coder",
                    "--version", "0.1.0",
                    "--description", "A tool for analysis",
                    "--keywords", "python",
                    "--file-format", "py",
                    "--date-modified", "2023-10-26",
                    "--source-filepath", str(source_py_path),
                    "--destination-filepath", destination_relative_path,
                ],
                catch_exceptions=False 
            )

            assert result.exit_code == 0, f"CLI Error: {result.output}"
            software_guid = result.output.strip()

            destination_full_path = pathlib.Path(destination_relative_path)
            assert destination_full_path.exists(), f"File was not copied to {destination_full_path}"
            
            software_entity = _load_and_get_graph_entity(crate_dir, software_guid)
            assert software_entity["contentUrl"] == 'file:///analysis_tool.py'
            root_dataset = _get_root_dataset(crate_dir)
            assert {"@id": software_guid} in root_dataset.get("hasPart", [])
        
        finally:
            os.chdir(original_cwd)
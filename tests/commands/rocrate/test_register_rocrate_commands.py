import pytest
import pathlib
import json
import os
import shutil
from fairscape_cli.__main__ import cli as fairscape_cli_app

def _load_and_validate_crate(crate_path: pathlib.Path):
    metadata_path = crate_path / "ro-crate-metadata.json"
    assert metadata_path.exists(), f"Metadata file not found at {metadata_path}"

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    root_dataset = next(
        (item for item in metadata.get("@graph", []) 
         if isinstance(item.get("@type", []), list) and 
            "Dataset" in item["@type"] and 
            "https://w3id.org/EVI#ROCrate" in item["@type"]),
        None
    )
    assert root_dataset is not None, "RO-Crate root dataset not found in @graph"
    return metadata, root_dataset


class TestRocrateCommands:
    original_cwd = os.getcwd()

    @pytest.fixture(scope="function")
    def prepared_rocrate(self, runner, tmp_path_factory):
        crate_dir = tmp_path_factory.mktemp("prepared_crate")
        result = runner.invoke(
            fairscape_cli_app,
            [
                "rocrate", "create", str(crate_dir), 
                "--name", "Base Crate",
                "--organization-name", "Test Org",
                "--project-name", "Test Proj",
                "--description", "Base crate for testing",
                "--keywords", "base"
            ]
        )
        assert result.exit_code == 0, f"Fixture setup failed: {result.output}"
        return crate_dir

    def test_rocrate_create_success(self, runner, tmp_path: pathlib.Path):
        crate_dir = tmp_path / "my-create-crate"
        
        result = runner.invoke(
            fairscape_cli_app,
            [
                "rocrate", "create", str(crate_dir),
                "--guid", "ark:59852/test-create",
                "--name", "My Created Crate",
                "--organization-name", "Org",
                "--project-name", "Proj",
                "--description", "A test create.",
                "--keywords", "create",
                "--keywords", "test",
                "--custom-properties", '{"customKey": "customValue"}'
            ]
        )
        
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        assert "ark:59852/test-create" in result.output

        _, root_dataset = _load_and_validate_crate(crate_dir)
        
        assert root_dataset["@id"] == "ark:59852/test-create"
        assert root_dataset["name"] == "My Created Crate"
        assert root_dataset["keywords"] == ["create", "test"]
        assert root_dataset["customKey"] == "customValue"

    def test_rocrate_init_success(self, runner, tmp_path: pathlib.Path):
        init_dir = tmp_path / "init_dir"
        init_dir.mkdir()
        
        os.chdir(init_dir)

        result = runner.invoke(
            fairscape_cli_app,
            [
                "rocrate", "init",
                "--name", "Initialized Crate",
                "--organization-name", "Init Org",
                "--project-name", "Init Proj",
                "--description", "An initialized crate.",
                "--keywords", "init"
            ]
        )

        assert result.exit_code == 0, f"CLI Error: {result.output}"
        
        _, root_dataset = _load_and_validate_crate(init_dir)
        assert root_dataset["name"] == "Initialized Crate"
        
        os.chdir(self.original_cwd)

    def test_register_software(self, runner, prepared_rocrate):
        result = runner.invoke(
            fairscape_cli_app,
            [
                "rocrate", "register", "software", str(prepared_rocrate),
                "--name", "My Registered Software",
                "--author", "Test Author",
                "--version", "1.0",
                "--description", "Software registered in the crate.",
                "--keywords", "tool",
                "--keywords", "science",
                "--date-modified", "2023-10-26",
                "--file-format", "py",
                "--filepath", "https://github.com/example/my-tool"
            ]
        )
        
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        software_guid = result.output.strip()

        metadata, root_dataset = _load_and_validate_crate(prepared_rocrate)
        
        registered_software = next(item for item in metadata["@graph"] if item["@id"] == software_guid)
        assert registered_software["name"] == "My Registered Software"
        assert registered_software["contentUrl"] == "https://github.com/example/my-tool"
        assert {"@id": software_guid} in root_dataset["hasPart"]

    def test_register_dataset(self, runner, prepared_rocrate):
        result = runner.invoke(
            fairscape_cli_app,
            [
                "rocrate", "register", "dataset", str(prepared_rocrate),
                "--name", "My Registered Dataset",
                "--author", "Data Author",
                "--version", "1.0",
                "--description", "Dataset registered in the crate.",
                "--keywords", "data",
                "--keywords", "test",
                "--data-format", "csv",
                "--filepath", "https://example.com/existing_data.csv",
                "--date-published", "2023-10-26"
            ]
        )
        
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        dataset_guid = result.output.strip()

        metadata, root_dataset = _load_and_validate_crate(prepared_rocrate)
        
        registered_dataset = next(item for item in metadata["@graph"] if item["@id"] == dataset_guid)
        assert registered_dataset["name"] == "My Registered Dataset"
        assert registered_dataset["contentUrl"] == "https://example.com/existing_data.csv"
        assert {"@id": dataset_guid} in root_dataset["hasPart"]

    def test_register_sample(self, runner, prepared_rocrate):
        result = runner.invoke(
            fairscape_cli_app,
            [
                "rocrate", "register", "sample", str(prepared_rocrate),
                "--name", "U2OS-cell-line",
                "--author", "Lab Tech",
                "--description", "A registered sample.",
                "--keywords", "cell",
                "--keywords", "sample"
            ]
        )
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        sample_guid = result.output.strip()

        metadata, root_dataset = _load_and_validate_crate(prepared_rocrate)
        registered_sample = next(item for item in metadata["@graph"] if item["@id"] == sample_guid)
        assert registered_sample["name"] == "U2OS-cell-line"
        assert {"@id": sample_guid} in root_dataset["hasPart"]

    def test_register_instrument(self, runner, prepared_rocrate):
        result = runner.invoke(
            fairscape_cli_app,
            [
                "rocrate", "register", "instrument", str(prepared_rocrate),
                "--name", "Confocal Microscope",
                "--manufacturer", "Zeiss",
                "--model", "LSM 980",
                "--description", "A registered instrument."
            ]
        )
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        instrument_guid = result.output.strip()

        metadata, root_dataset = _load_and_validate_crate(prepared_rocrate)
        registered_instrument = next(item for item in metadata["@graph"] if item["@id"] == instrument_guid)
        assert registered_instrument["name"] == "Confocal Microscope"
        assert registered_instrument["manufacturer"] == "Zeiss"
        assert {"@id": instrument_guid} in root_dataset["hasPart"]

    def test_register_experiment(self, runner, prepared_rocrate):
        result = runner.invoke(
            fairscape_cli_app,
            [
                "rocrate", "register", "experiment", str(prepared_rocrate),
                "--name", "Cell Imaging Experiment",
                "--experiment-type", "Microscopy",
                "--run-by", "Dr. Scientist",
                "--description", "An imaging experiment.",
                "--date-performed", "2024-01-15"
            ]
        )
        assert result.exit_code == 0, f"CLI Error: {result.output}"
        exp_guid = result.output.strip()

        metadata, root_dataset = _load_and_validate_crate(prepared_rocrate)
        registered_exp = next(item for item in metadata["@graph"] if item["@id"] == exp_guid)
        assert registered_exp["name"] == "Cell Imaging Experiment"
        assert registered_exp["experimentType"] == "Microscopy"
        assert {"@id": exp_guid} in root_dataset["hasPart"]
        
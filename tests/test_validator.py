from unittest import TestCase

from typer.testing import CliRunner

#from apps.validator import app
from main import app

runner = CliRunner()




class Test(TestCase):
    def test_validate_json_document(self):
        result = runner.invoke(app, ["fairscape", "validate", "json",
                                     "data/minimal_rocrate.json"])
        assert result.exit_code == 0
        assert "Successfully validated JSON document" in result.stdout

    def test_validate_json_dataset_document(self):
        result = runner.invoke(app, ["fairscape", "validate", "json",
                                     "data/dataset_local.json"])
        assert result.exit_code == 0
        assert "Successfully validated JSON document" in result.stdout

    def test_validate_json_software_document(self):
        result = runner.invoke(app, ["fairscape", "validate", "json",
                                     "data/software_local.json"])
        assert result.exit_code == 0
        assert "Successfully validated JSON document" in result.stdout

    def test_validate_json_computation_document(self):
        result = runner.invoke(app, ["fairscape", "validate", "json",
                                     "data/computation.json"])
        assert result.exit_code == 0
        assert "Successfully validated JSON document" in result.stdout

    def test_validate_dataset_local_metadata(self):
        result = runner.invoke(app, ["fairscape", "validate", "dataset",
                                     "data/dataset_local.json"])
        assert result.exit_code == 0
        assert "Successfully" in result.stdout

    def test_validate_dataset_remote_metadata(self):
        result = runner.invoke(app, ["fairscape", "validate", "dataset",
                                     "data/dataset_remote.json"])
        assert result.exit_code == 0
        assert "Successfully" in result.stdout

    def test_validate_software_local_metadata(self):
        result = runner.invoke(app, ["fairscape", "validate", "software",
                                     "data/software_local.json"])
        assert result.exit_code == 0
        assert "Successfully" in result.stdout

    def test_validate_software_remote_metadata(self):
        result = runner.invoke(app, ["fairscape", "validate", "software",
                                     "data/software_remote.json"])
        assert result.exit_code == 0
        assert "Successfully" in result.stdout

    def test_validate_computation_metadata(self):
        result = runner.invoke(app, ["fairscape", "validate", "computation",
                                     "data/computation.json"])
        assert result.exit_code == 0
        assert "Successfully" in result.stdout


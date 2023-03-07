import context
import unittest

from typer.testing import CliRunner
from fairscape_cli import fairscape_cli_app

runner = CliRunner()


class TestValidateSoftware(unittest.TestCase):

    def test_success(self):
        result = runner.invoke(fairscape_cli_app, [ ])
        assert result.exit_code == 0

    def test_missing_properties(self):
        pass

    def test_incorrect_type(self):
        pass


class TestValidateComputation(unittest.TestCase):
    
    def test_success(self):
        pass


class TestValidateDataset(unittest.TestCase):

    def test_success(self):
        pass


class TestValidateROCrate(unittest.TestCase):

    def test_success(self):
        pass


class TestCache(unittest.TestCase):
        pass


class TestROCrate(unittest.TestCase):
    
    def test_create_rocrate(self):
        pass
    
    def test_add_dataset(self):
        pass

    def test_add_computation(self):
        pass

    def test_add_software(self):
        pass

    def test_validate_rocrate(self):
        pass

    def test_hash_rocrate(self):
        pass

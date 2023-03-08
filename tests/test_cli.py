import os
import sys

sys.path.insert(
    0, 
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), 
        '..')
    )
)

import unittest
import logging
from typer.testing import CliRunner
from fairscape_cli import fairscape_cli_app

runner = CliRunner()

test_logger = logging.getLogger()
test_logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
test_logger.addHandler(stream_handler)

def run_test_command(test_command):

    result = runner.invoke(
        fairscape_cli_app, 
        test_command
    )

    test_logger.debug(f"COMMAND: {' '.join(test_command)}\nExitCode: {result.exit_code}\nOutput: {result.stdout}")
    return result


class TestValidateSoftware(unittest.TestCase):


    def test_validate_json(self):
        validate_json_software = [
            "fairscape", 
            "validate", 
            "json", 
            "./tests/data/software.json"
        ]
        
        result = run_test_command(validate_json_software)
        assert result.exit_code == 0


    def test_validate_software(self):
        validate_json_software = [
            "fairscape", 
            "validate", 
            "software", 
            "./tests/data/software.json"
        ]
        
        result = run_test_command(validate_json_software)
        assert result.exit_code == 0
        

    def test_missing_properties(self):
        validate_missing_software = [
            "fairscape", 
            "validate", 
            "software", 
            "./tests/data/software_missing.json"
        ]
        
        result = run_test_command(validate_missing_software)
        assert result.exit_code != 0


    def test_incorrect_type(self):
        pass


class TestValidateComputation(unittest.TestCase):
 
    def test_validate_json(self):
        validate_json_computation= [
            "fairscape", 
            "validate", 
            "json", 
            "./tests/data/computation.json"
        ]
        
        result = run_test_command(validate_json_computation)
        assert result.exit_code == 0


class TestValidateDataset(unittest.TestCase):

    def test_validate_json(self):
        validate_json_dataset= [
            "fairscape", 
            "validate", 
            "json", 
            "./tests/data/dataset.json"
        ]
        
        result = run_test_command(validate_json_dataset)
        assert result.exit_code == 0


class TestValidateROCrate(unittest.TestCase):

    def test_validate_json(self):
        pass





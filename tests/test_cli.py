import os
import sys

sys.path.insert(
    0, 
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), 
        '..')
    )
)

from click.testing import CliRunner
from fairscape_cli.__main__ import cli as fairscape_cli_app

runner = CliRunner()

def run_test_command(test_command):

    result = runner.invoke(
        fairscape_cli_app, 
        test_command
    )

    print(f"COMMAND: {' '.join(test_command)}\nExitCode: {result.exit_code}\nOutput: {result.stdout}")
    return result




def test_software_validate_software():
    validate_json_software = [
        "validate", 
        "software", 
        "./tests/data/software.json"
    ]
    
    result = run_test_command(validate_json_software)
    assert result.exit_code == 0
    

def test_software_missing_properties():
    validate_missing_software = [
        "validate", 
        "software", 
        "./tests/data/software_missing.json"
    ]
    
    result = run_test_command(validate_missing_software)
    assert result.exit_code != 0


def _test_software_incorrect_type():
    pass


 
def test_computation_validate_json():
    validate_json_computation= [
        "validate", 
        "computation", 
        "./tests/data/computation.json"
    ]
    
    result = run_test_command(validate_json_computation)
    assert result.exit_code == 0



def test_dataset_validate_json():
    validate_json_dataset= [
        "validate", 
        "dataset", 
        "./tests/data/dataset.json"
    ]
    
    result = run_test_command(validate_json_dataset)
    assert result.exit_code == 0





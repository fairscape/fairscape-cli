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

def run_test_command(test_command):

    result = runner.invoke(
        fairscape_cli_app, 
        test_command
    )

    print(f"\nCOMMAND: {' '.join(test_command)}\nExitCode: {result.exit_code}\nOutput: {result.stdout}")
    return result
 
   
def test_rocrate_create(): 

    create_rocrate = [
        "rocrate", 
        "create", 
        "--rocrate ./tests/test_rocrate"
    ]
    
    result = run_test_command(create_rocrate)

    assert result.exit_code == 0


def test_add_dataset():
    pass

def test_add_computation():
    pass

def test_add_software(self):
    pass

def test_validate_rocrate(self):
    pass

def test_hash_rocrate(self):
    pass

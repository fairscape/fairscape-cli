import os
import sys

sys.path.insert(
    0, 
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), 
        '..')
    )
)

from typer.testing import CliRunner
from fairscape_cli.apps.fairscape import app as fairscape_cli_app

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
        "--guid ark:59853/UVA/B2AI/rocrate_test",
        "--name 'test rocrate'",
        "--organization ' '",
        "--project ' '",
        "--path './tests/test_rocrate'",
    ]
    
    result = run_test_command(create_rocrate)

    assert result.exit_code == 0
    assert "Created RO Crate at" in result.stdout

    # TODO check that the ro-crate-metadata.json is correct


def test_add_dataset():
    add_dataset = [
        "rocrate",
        "add",
        "dataset",
        "--guid ark:59853/UVA/B2AI/rocrate_test/music_data",
        "--name ",
        "--description" ,
        "--datePublished ",
        "--version 1.0.0",
        "--associatedPublication ",
        "--additionalDocumentation ",
        "--dataFormat .csv",
        "--sourcePath ''",
        "--destinationPath ''"
    ]

    result = run_test_command(add_dataset)

    assert result.exit_code == 0
    

def test_add_computation():
    add_computation = [
        "rocrate",
        "add",
        "computation",
        "--guid ark:59853/UVA/B2AI/rocrate_test/music_test_run",
        "--name music test run",
        "--runBy Max Levinson",
        "--description 'test run of music pipeline using example data'",
        "--associatedPublication ",
        "--additionalDocumentation ",
        "--usedSoftware ",
        "--usedDataset ",
        "--generated "
    ]

    result = run_test_command(add_computation)

    assert result.exit_code == 0

def test_add_software():
    add_software = [
        "rocrate",
        "add",
        "dataset",
        "--guid ark:59853/UVA/B2AI/rocrate_test/music_software",
        "--name MuSIC",
        "--author ",
        "--version ",
        "--description ",
        "--associatedPublication ",
        "--format .py",
        "--sourcePath ",
        "--destinationPath ",
    
    ]

    result = run_test_command(add_software)

    assert result.exit_code == 0

def test_validate_rocrate():
    pass

def test_hash_rocrate():
    pass

def test_package_rocrate():
    pass

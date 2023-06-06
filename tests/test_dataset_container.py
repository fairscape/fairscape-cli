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
from fairscape_cli.main import cli as fairscape_cli_app

runner = CliRunner()


class TestDatasetContainerClass():

    def test_pydantic_init(self):
        pass

    def test_crate_register(self):
        pass

    def test_crate_push(self):
        pass

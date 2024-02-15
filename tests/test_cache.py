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



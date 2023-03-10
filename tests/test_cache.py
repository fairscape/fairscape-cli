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



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


class TestCache(unittest.TestCase):
        pass


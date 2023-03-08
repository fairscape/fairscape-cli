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

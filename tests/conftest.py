import pytest
from click.testing import CliRunner

@pytest.fixture(scope="session")
def runner():
    """Provides a click.testing.CliRunner instance to invoke CLI commands."""
    return CliRunner()
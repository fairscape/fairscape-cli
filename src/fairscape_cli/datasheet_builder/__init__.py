"""
Datasheet Builder module for RO-Crate metadata visualization and documentation.
"""

from pathlib import Path

from fairscape_cli.datasheet_builder.rocrate.datasheet_generator import DatasheetGenerator


def get_default_template_dir() -> Path:
    """Return the Jinja template directory shipped with the package."""
    return Path(__file__).parent / 'templates'


__all__ = ['DatasheetGenerator', 'get_default_template_dir']

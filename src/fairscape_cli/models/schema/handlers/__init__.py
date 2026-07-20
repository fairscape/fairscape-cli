# Importing these modules registers the built-in handlers as a side effect.
from fairscape_cli.models.schema.handlers import tabular
from fairscape_cli.models.schema.handlers import hdf5
from fairscape_cli.models.schema.handlers import parquet

__all__ = ['tabular', 'hdf5', 'parquet']

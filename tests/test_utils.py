import pathlib
import pytest

from fairscape_cli.rocrate.utils import (
    inside_crate 
)

def test_inside_crate():
    rocrate_path = pathlib.Path("./tests/guid_test_rocrate")
    destination_filepath = pathlib.Path("./tests/example_rocrate/APMS_embedding_MUSIC.csv")

    with pytest.raises(Exception):
        inside_crate(rocrate_path, destination_filepath)

    



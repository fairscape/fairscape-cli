from fairscape_cli.models.rocrate import (
    ReadROCrateMetadata
)

class TestROCrateUtils():
    def test_read_rocrate_metadata(self):
        test_crate = ReadROCrateMetadata('./tests/data/test_crates/build_test_rocrate/ro-crate-metadata.json')

        assert test_crate.guid is not None

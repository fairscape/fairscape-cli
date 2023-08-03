import os
import sys
import pathlib
import json

sys.path.insert(
    0, 
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), 
        '..')
    )
)


from fairscape_cli.models import (
    ROCrate,
    Dataset,
    Software,
    Computation
)

class TestROCrateModel():

    def test_rocrate_init(self):
        
        rocrate_data = {
            "@id": "ark:59853/UVA/B2AI/rocrate_test",
            "name": 'test rocrate',
            "organizationName": "UVA",
            "projectName":  "B2AI",
            "description":  "Testing ROCrate Model",
            "keywords": ["test", "fair"],
            "path": pathlib.Path.cwd(),
            "metadataGraph": []
        }
       
        test_crate = ROCrate(
            **rocrate_data
        ) 

        test_crate.initCrate()


    def test_rocrate_add_dataset(self):
        pass


    def test_rocrate_add_software(self):
        pass


    def test_rocrate_add_computation(self):
        pass


    def test_rocrate_hash(self):
        pass


    def test_rocrate_zip(self):
        pass


    def test_rocrate_read(self):
        pass


class TestDatasetModel():

    def test_dataset_full_properties(self):
        pass

    def test_dataset_remote(self):
        pass

    def test_dataset_missing_optional(self):
        pass

    def test_dataset_json_marshal(self):
        pass


class TestSoftwareModel():
    
    def test_software_full_properties(self):
        pass

    def test_software_remote(self):
        pass

    def test_software_missing_optional(self):
        pass

    def test_software_json_marshal(self):
        pass


class TestComputationModel():
    
    def test_computation_full_properties(self):
        pass

    def test_remote_computation(self):
        pass

    def test_missing_optional(self):
        pass

    def test_json_marshal(self):
        pass

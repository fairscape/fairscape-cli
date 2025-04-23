import os
import sys
import pathlib
import json
import shutil

sys.path.insert(
    0, 
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), 
        '../src/')
    )
)

import unittest
import datetime 
import random

from fairscape_cli.models.computation import GenerateComputation
from fairscape_cli.models.dataset import GenerateDataset
from fairscape_cli.models.software import GenerateSoftware
from fairscape_cli.models.rocrate import (
    GenerateROCrate,
    ReadROCrateMetadata,
    AppendCrate
)
from sqids import Sqids

class TestAPI(unittest.TestCase):
    
    def setUp(self):
        # Create test directory structure
        self.rocratePath = pathlib.Path.cwd() / 'tests' / 'data' / 'test_api'
        self.rocratePath.mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        # Clean up test directory after tests
        pass
        # if self.rocratePath.exists():
        #     shutil.rmtree(self.rocratePath)
        
    def test_api(self):
        # Clean start - safely handle metadata file deletion
        metadataFile = self.rocratePath / 'ro-crate-metadata.json'
        if metadataFile.exists():
            metadataFile.unlink()

        rocrate_metadata = {
            "guid": "ark:59853/UVA/B2AI/rocrate_test",
            "name": 'test rocrate',
            "author": "Fake Person",
            "version": "0.1",
            "datePublished": "2024-01-01",
            "license": "CC-BY-4.0",
            "organizationName": "UVA",
            "projectName":  "B2AI",
            "description":  "Testing ROCrate Model",
            "keywords": ["test", "fair"],
            "path": self.rocratePath
        }

        rocrate = GenerateROCrate(**rocrate_metadata)
        
        software_metadata = {
            "guid": "955cf26c-e3a3-4f0f-b2df-fca4c693cac4:cm4ai_chromatin_mda-mb-468_untreated_ifimage_0.7alpha",
            "author": "Cell Maps team",
            "url": "https://github.com/idekerlab/cellmaps_utils",
            "name": "cellmaps_utils",
            "keywords": [
                "CM4AI",
                "0.7alpha",
                "MDA-MB-468",
                "untreated",
                "IF microscopy",
                "images",
                "breast; mammary gland",
                "chromatin",
                "tools",
                "cellmaps_utils"
            ],
            "description": "CM4AI 0.7alpha MDA-MB-468 untreated IF microscopy images breast; mammary gland chromatin Contains utilities needed by Cell Maps tools",
            "dateModified": "2024-10-22",
            "version": "0.5.0",
            "fileFormat": "py",
            "usedByComputation": [],
            "associatedPublication": None,
            "additionalDocumentation": None,
            "filepath": "https://github.com/idekerlab/cellmaps_utils",
            "cratePath": self.rocratePath
        }
        software = GenerateSoftware(**software_metadata)

        yellowFolder = self.rocratePath / 'yellow'
        yellowFolder.mkdir(exist_ok=True)

        # Create datasets
        datasetList = []
        for i in range(10000):
            fileName = f'B2AI_5_untreated_B5_R5_z01_yellow_{i}.jpg'
            datasetMetadata = {
                "guid": f"322ab5a2-e6a7-4c46-be79-cbf3e9453cde:cm4ai_chromatin_mda-mb-468_untreated_ifimage_0.7alpha_{i}",  # Make unique
                "name": f"B2AI_5_untreated_B5_R5_z01_yellow_{i}.jpg yellow channel image",
                "keywords": [
                    "CM4AI",
                    "0.7alpha",
                    "MDA-MB-468",
                    "untreated",
                    "IF microscopy",
                    "images",
                    "breast; mammary gland",
                    "chromatin",
                    "yellow",
                    "IF",
                    "image",
                    "ER (Calreticulin antibody)"
                ],
                "description": "CM4AI 0.7alpha MDA-MB-468 untreated IF microscopy images breast; mammary gland chromatin IF image file",
                "author": "Lundberg Lab",
                "datePublished": "2024-10-22",
                "version": "0.7alpha",
                "format": "jpg",
                "generatedBy": [],
                "derivedFrom": [],
                "usedBy": [],
                "url": None,
                "associatedPublication": None,
                "additionalDocumentation": None,
                "schema": None,
                "filepath": f"file:///yellow/{fileName}",
                "cratePath": self.rocratePath
            }
            dataset = GenerateDataset(**datasetMetadata)
            datasetList.append(dataset)

        AppendCrate(self.rocratePath, datasetList)

        # Verify crate metadata
        rocrateMetadataRecord = ReadROCrateMetadata(self.rocratePath)
        rocrateGUIDs = [elem["@id"] for elem in rocrateMetadataRecord["@graph"]]

        # Verify all dataset GUIDs are present
        for ds in datasetList:
            self.assertIn(ds.guid, rocrateGUIDs, f"Dataset GUID {ds.guid} not found in metadata")

        computation_metadata = {
            "guid": "test-computation-guid",  # Made more specific
            "name": "Image Compression",
            "runBy": "Chris Churas",
            "command": "./test.sh",
            "dateCreated": "10-28-2024",
            "description": "A placeholder computation for image compression",
            "keywords": ["cm4ai", "image"],
            "usedSoftware": software.guid,
            "usedDataset": [ds.guid for ds in datasetList],
            "generated": None
        }
        computation = GenerateComputation(**computation_metadata)
        AppendCrate(self.rocratePath, [software, computation])

        # Final verification
        rocrateMetadataRecord = ReadROCrateMetadata(self.rocratePath)
        rocrateGUIDs = [elem["@id"] for elem in rocrateMetadataRecord["@graph"]]

        self.assertIn(computation.guid, rocrateGUIDs, "Computation GUID not found in metadata")
        self.assertIn(software.guid, rocrateGUIDs, "Software GUID not found in metadata")

if __name__ == "__main__":
    unittest.main()
import os
import sys
import pathlib
import json

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
		
	def test_api(self):
		rocratePath = pathlib.Path.cwd() / 'tests'/ 'data' / 'test_api'

		# delete the test_api folder
		metadataFile = rocratePath / 'ro-crate-metadata.json'
		metadataFile.unlink()

		rocrate_metadata = {
			"guid": "ark:59853/UVA/B2AI/rocrate_test",
			"name": 'test rocrate',
			"organizationName": "UVA",
			"projectName":  "B2AI",
			"description":  "Testing ROCrate Model",
			"keywords": ["test", "fair"],
			"path": rocratePath
			}

		# touch a file for the dataset to say exists

		rocrate = GenerateROCrate(**rocrate_metadata)
		
		software_metadata={
			"guid" : "955cf26c-e3a3-4f0f-b2df-fca4c693cac4:cm4ai_chromatin_mda-mb-468_untreated_ifimage_0.7alpha",
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
			"cratePath": rocratePath
		}
		software = GenerateSoftware(**software_metadata)

		yellowFolder = rocratePath / 'yellow'
		yellowFolder.mkdir(exist_ok=True)

		# create 10k identifiers
		datasetList = []
		#for i in range(100000):
		#	fileName = f'B2AI_5_untreated_B5_R5_z01_yellow_{i}.jpg'
		#	datasetFilePath = yellowFolder / fileName
		#	datasetFilePath.touch(exist_ok=True)

		for i in range(10000):
			fileName = f'B2AI_5_untreated_B5_R5_z01_yellow_{i}.jpg'
			datasetMetadata = {
				"guid": "322ab5a2-e6a7-4c46-be79-cbf3e9453cde:cm4ai_chromatin_mda-mb-468_untreated_ifimage_0.7alpha",
				"name": "B2AI_5_untreated_B5_R5_z01_yellow.jpg yellow channel image",
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
			"dataFormat": "jpg",
			"generatedBy": [],
			"derivedFrom": [],
			"usedBy": [],
			"url": None,
			"associatedPublication": None,
			"additionalDocumentation": None,
			"schema": None,
			"filepath": f"file:///yellow/{fileName}",
			"cratePath": rocratePath
			}
			dataset = GenerateDataset(**datasetMetadata)
			datasetList.append(dataset)

		AppendCrate(rocratePath, datasetList)

		# read in the crate metadata
		rocrateMetadataRecord = ReadROCrateMetadata(rocratePath)
		rocrateGUIDs = [ elem.guid for elem in rocrateMetadataRecord.metadataGraph]

		# assert that all dataset guids are present
		for ds in datasetList:
			assert ds.guid in rocrateGUIDs

		computation_metadata = {
			"guid": "test guid",
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
		AppendCrate(rocratePath, [software, computation])

		# read in ROCrate
		rocrateMetadataRecord = ReadROCrateMetadata(rocratePath)
		rocrateGUIDs = [ elem.guid for elem in rocrateMetadataRecord.metadataGraph]

		assert computation.guid in rocrateGUIDs
		assert software.guid in rocrateGUIDs




if __name__ == "__main__":
	unittest.main()
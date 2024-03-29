import os
import sys
import json
import shutil

sys.path.insert(
    0, 
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), 
        '..')
    )
)

from click.testing import CliRunner
from fairscape_cli.__main__ import cli as fairscape_cli_app

###########################
# Test Metadata for ROCrate 
###########################


test_dataset = {
    "id": "ARK:APMS_embedding.MuSIC.1/5b3793b6-2bd0-4c51-9f35-c5cd7ddd366c.csv",
    "name": "AP-MS embeddings",
    "type": "schema:Dataset",
    "author": "Gygi lab (https://gygi.hms.harvard.edu/team.html)",
    "datePublished": "2021-04-23",
    "version": "1.0",
    "description": "Affinity purification mass spectrometer (APMS) embeddings for each protein in the study,  generated by node2vec predict.",
    "associatedPublication": 
        "Qin, Y. et al. A multi-scale map of cell structure fusing protein images and interactions",
    "additionalDocumentation": [
        "https://idekerlab.ucsd.edu/music/"
    ],
    "format": "CSV",
    "dataSchema": 
      'APMS_ID str, "APMS_1, APMS_2, ...", protein, embedding array of float X 1024',
    "derivedFrom": ["node2vec predict"],
    "generatedBy": [],
    "usedBy": ["create labeled training & test sets  random_forest_samples.py"],
    "contentUrl": "https://github.com/idekerlab/MuSIC/blob/master/Examples/APMS_embedding.MuSIC.csv"
}

test_software = {
    "id": "ARK:calibrate_pariwise_distance.1/467f5ebd-cb29-43a1-beab-aa2d50606eff.py",
    "name": "calibrate pairwise distance",
    "type": "evi:Software",
    "author": "Qin, Y.",
    "dateModified": "2021-06-20",
    "version": "1.0",
    "description": "script written in python to calibrate pairwise distance.",
    "associatedPublication": "Qin, Y. et al. A multi-scale map of cell structure fusing protein images and interactions. Nature 600, 536–542 2021",
    "additionalDocumentation": ["https://idekerlab.ucsd.edu/music/"],
    "format": "py",
    "usedByComputation": ["ARK:compute_standard_proximities.1/f9aa5f3f-665a-4ab9-8879-8d0d52f05265"],
    "contentUrl": "https://github.com/idekerlab/MuSIC/blob/master/calibrate_pairwise_distance.py"
}

test_computation = {
    "id": "ARK:average_predicted_protein_proximities.1/c295abcd-8ad8-44ff-95e3-e5e65f1667da",
    "name": "average predicted protein proximities",
    "type": "evi:Computation",
    "runBy": "Qin, Y.",
    "dateCreated": "2021-05-23",
    "description": "Average the predicted proximities",
    "usedSoftware":[
      "random_forest_output (https://github.com/idekerlab/MuSIC/blob/master/random_forest_output.py)"
    ],
    "usedDataset": [ 
"""predicted protein proximities:
Fold 1 proximities:
    IF_emd_1_APMS_emd_1.RF_maxDep_30_nEst_1000.fold_1.pkl""",
    "IF_emd_2_APMS_emd_1.RF_maxDep_30_nEst_1000.fold_1.pkl",
"""Fold 1 proximities:
      IF_emd_1_APMS_emd_1.RF_maxDep_30_nEst_1000.fold_2.pkl""",
    "IF_emd_2_APMS_emd_1.RF_maxDep_30_nEst_1000.fold_2.pkl",
"""Fold 1 proximities:
      IF_emd_1_APMS_emd_1.RF_maxDep_30_nEst_1000.fold_3.pkl""",
    "IF_emd_2_APMS_emd_1.RF_maxDep_30_nEst_1000.fold_3.pkl",
"""Fold 1 proximities:
      IF_emd_1_APMS_emd_1.RF_maxDep_30_nEst_1000.fold_4.pkl""",
    "IF_emd_2_APMS_emd_1.RF_maxDep_30_nEst_1000.fold_4.pkl",
"""Fold 1 proximities:
      IF_emd_1_APMS_emd_1.RF_maxDep_30_nEst_1000.fold_5.pkl""",
"IF_emd_2_APMS_emd_1.RF_maxDep_30_nEst_1000.fold_5.pkl"
    ],
"associatedPublication": "Qin, Y. et al. A multi-scale map of cell structure fusing protein images and interactions. Nature 600, 536–542 2021",
    "additionalDocumentation": ["https://idekerlab.ucsd.edu/music/"],
    "generated": [
    "averages of predicted protein proximities (https://github.com/idekerlab/MuSIC/blob/master/Examples/MuSIC_predicted_proximity.txt)"
    ]
}



class TestROCrateGenerateID():
    runner = CliRunner()
    rocrate_path = "./tests/data/guid_rocrate"
   
 
    def test_create_rocrate(self):
        """
        Invoke the create rocrate command without the guid flag and assert
        that a proper guid has been created and the ro crate initilized correctly
        """
        
        try:
            # remove existing crate
            shutil.rmtree(self.rocrate_path)
        except:
            pass

        create_rocrate = [
            "rocrate", 
            "create", 
            "--name 'test rocrate'",
            "--organization-name 'UVA'",
            "--project-name 'B2AI'",
            "--description 'A test crate for provenance of protien protien interactions of the MUSIC pipeline using a U2OS cell line'",
            "--keywords 'CM4AI'",
            f"'{self.rocrate_path}'",
        ]
        
        result = self.runner.invoke(
            fairscape_cli_app, 
            ' '.join(create_rocrate) 
        )

        print(result.stdout)

        assert result.exit_code == 0
        assert "ark:5982" in result.stdout
        

    def test_add_dataset(self):
        """
        Add a dataset without the guid and test if one is generated properly
        """

        add_dataset = [
            "rocrate",
            "add",
            "dataset",
            f"--name '{test_dataset['name']}'",
            f"--description '{test_dataset['description']}'" ,
            "--description 'A test crate for provenance of protien protien interactions of the MUSIC pipeline using a U2OS cell line'",
            "--keywords 'CM4AI'",
            f"--date-published '{test_dataset['datePublished']}'",
            f"--author '{test_dataset['author']}'",
            "--version '1.0.0'",
            f"--associated-publication '{test_dataset['associatedPublication']}'",
            f"--additional-documentation '{test_dataset['additionalDocumentation'][0]}'",
            f"--data-format '{test_dataset['format']}'",
            "--source-filepath './tests/data/APMS_embedding_MUSIC.csv'",
            f"--destination-filepath '{self.rocrate_path}/APMS_embedding_MUSIC.csv'",
            f"'{self.rocrate_path}'",
        ]

        print(' '.join(add_dataset))

        result = self.runner.invoke(
            fairscape_cli_app, 
            ' '.join(add_dataset) 
        )
        print(result.stdout)

        assert result.exit_code == 0
        
    
    def test_add_software(self):
        add_software = [
            "rocrate",
            "add",
            "dataset",
            "--guid ark:59853/UVA/B2AI/rocrate_test/music_software",
            "--name MuSIC",
            f"--author '{test_software['author']}'",
            "--version '1.0'",
            f"--description '{test_software['description']}'",
            "--description 'A test crate for provenance of protien protien interactions of the MUSIC pipeline using a U2OS cell line'",
            "--keywords 'CM4AI'",
            f"--associated-publication '{test_software['associatedPublication']}'",
            "--data-format '.py'",
            f"--date-published '{test_software['dateModified']}'",
            "--source-filepath './tests/data/calibrate_pairwise_distance.py'",
            f"--destination-filepath '{self.rocrate_path}/calibrate_pairwise_distance.py'",
            f"'{self.rocrate_path}'", 
        ]

        result = self.runner.invoke(
            fairscape_cli_app, 
            ' '.join(add_software) 
        )
        print(result.stdout)

        assert result.exit_code == 0


    def test_add_computation(self):
        add_computation = [
            "rocrate",
            "register",
            "computation",
            f"--name '{test_computation['name']}'",
            "--run-by 'Max Levinson'",
            "--date-created '03-17-2023'",
            "--description 'test run of music pipeline using example data'",
            "--description 'A test crate for provenance of protien protien interactions of the MUSIC pipeline using a U2OS cell line'",
            "--keywords 'CM4AI'",
            #f"--used-software '[{','.join(software)}]'",
            #f"--used-dataset '[{','.join(datasets)}]'",
            "--command 'wingardium leviosa'",
            f"--used-software '{test_computation['usedSoftware'][0]}'",
            f"--used-dataset '[{test_computation['usedDataset'][0]}]'", 
            f"--generated '[{test_computation['generated'][0]}]'",
            f"'{self.rocrate_path}'"
        ]

        print(' '.join(add_computation))

        result = self.runner.invoke(
            fairscape_cli_app, 
            ' '.join(add_computation) 
        )
        print(result.stdout)

        assert result.exit_code == 0

 

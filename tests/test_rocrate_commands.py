import unittest
import pathlib
import shutil
import subprocess
import json
import os
from rocrate_validator import services, models

class TestCLICommands(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path.cwd() / 'tests' / 'data' / 'test_cli'
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Change to test directory
        os.chdir(self.test_dir)
        # Create files relative to test directory
        pathlib.Path('input_data.csv').touch()
        pathlib.Path('subcrate').mkdir(exist_ok=True)
        pathlib.Path('subcrate/subcrate_data.csv').touch()
        pathlib.Path('subcrate/software.py').touch()
        
    # def tearDown(self):
    #     if self.test_dir.exists():
    #         shutil.rmtree(self.test_dir)
            
    def test_cli_workflow(self):
        # Create top-level crate
        top_crate_result = subprocess.run([
            'fairscape-cli', 'rocrate', 'create',
            '--name', 'Top Level Crate',
            '--organization-name', 'Test Org',
            '--project-name', 'Test Project',
            '--date-published', '2025-01-22',
            '--description', 'Top level test crate',
            '--keywords', 'test,top-level',
            '.'
        ], capture_output=True, text=True)
        print(f"Top crate output: {top_crate_result.stdout}")
        print(f"Top crate error: {top_crate_result.stderr}")
        self.assertEqual(top_crate_result.returncode, 0)
        top_crate_id = top_crate_result.stdout.strip()
        
        # Create subcrate
        subcrate_result = subprocess.run([
            'fairscape-cli', 'rocrate', 'register', 'subrocrate',
            '.', 'subcrate',
            '--name', 'Sub Crate',
            '--organization-name', 'Test Org',
            '--project-name', 'Test Project',
            '--description', 'Test subcrate',
            '--keywords', 'test,subcrate'
        ], capture_output=True, text=True)
        print(f"Subcrate output: {subcrate_result.stdout}")
        print(f"Subcrate error: {subcrate_result.stderr}")
        self.assertEqual(subcrate_result.returncode, 0)
        subcrate_id = subcrate_result.stdout.strip()
        
        # Register top-level dataset
        top_dataset_result = subprocess.run([
            'fairscape-cli', 'rocrate', 'register', 'dataset',
            '.',
            '--name', 'Top Level Data',
            '--author', 'Test Author',
            '--version', '1.0',
            '--date-published', '2025-01-22',
            '--description', 'Top level test data',
            '--keywords', 'test,data',
            '--data-format', 'csv',
            '--filepath', 'input_data.csv'
        ], capture_output=True, text=True)
        print(f"Top dataset output: {top_dataset_result.stdout}")
        print(f"Top dataset error: {top_dataset_result.stderr}")
        self.assertEqual(top_dataset_result.returncode, 0)
        top_dataset_id = top_dataset_result.stdout.strip()
        
        # Register subcrate dataset
        subcrate_dataset_result = subprocess.run([
            'fairscape-cli', 'rocrate', 'register', 'dataset',
            str(self.test_dir / 'subcrate'),
            '--name', 'Subcrate Data',
            '--author', 'Test Author',
            '--version', '1.0',
            '--date-published', '2025-01-22',
            '--description', 'Subcrate test data',
            '--keywords', 'test,data',
            '--data-format', 'csv',
            '--filepath', 'subcrate/subcrate_data.csv'
        ], capture_output=True, text=True)
        print(f"Subcrate dataset output: {subcrate_dataset_result.stdout}")
        print(f"Subcrate dataset error: {subcrate_dataset_result.stderr}")
        self.assertEqual(subcrate_dataset_result.returncode, 0)
        subcrate_dataset_id = subcrate_dataset_result.stdout.strip()
        
        # Register software in subcrate
        software_result = subprocess.run([
            'fairscape-cli', 'rocrate', 'register', 'software',
            str(self.test_dir / 'subcrate'),
            '--name', 'Test Software',
            '--author', 'Test Author',
            '--version', '1.0',
            '--description', 'Test analysis software',
            '--keywords', 'test,software',
            '--file-format', 'py',
            '--filepath', 'subcrate/software.py',
            '--date-modified', '2025-01-22'
        ], capture_output=True, text=True)
        print(f"Software output: {software_result.stdout}")
        print(f"Software error: {software_result.stderr}")
        self.assertEqual(software_result.returncode, 0)
        software_id = software_result.stdout.strip()
        
        # Register computation in subcrate
        computation_result = subprocess.run([
            'fairscape-cli', 'rocrate', 'register', 'computation',
            str(self.test_dir / 'subcrate'),
            '--name', 'Test Computation',
            '--run-by', 'Test Author',
            '--date-created', '2025-01-22',
            '--description', 'Test computation',
            '--keywords', 'test,computation',
            '--used-software', software_id,
            '--used-dataset', subcrate_dataset_id,
            '--command', 'python software.py subcrate_data.csv'
        ], capture_output=True, text=True)
        print(f"Computation output: {computation_result.stdout}")
        print(f"Computation error: {computation_result.stderr}")
        self.assertEqual(computation_result.returncode, 0)
        computation_id = computation_result.stdout.strip()
        
        # Verify crate structure
        with open(self.test_dir / 'ro-crate-metadata.json') as f:
            top_metadata = json.load(f)
        with open(self.test_dir / 'subcrate' / 'ro-crate-metadata.json') as f:
            sub_metadata = json.load(f)
            
        # Verify top-level crate structure
        top_root_id = next(item['about']['@id'] for item in top_metadata['@graph'] 
                      if item['@id'] == 'ro-crate-metadata.json')
        top_root = next(item for item in top_metadata['@graph'] 
                       if item['@id'] == top_root_id)
        
        # Verify top-level relationships
        self.assertIn(subcrate_id, [part['@id'] for part in top_root['hasPart']])
        self.assertIn(top_dataset_id, [part['@id'] for part in top_root['hasPart']])
        
        # Verify subcrate structure
        sub_root_id = next(item['about']['@id'] for item in sub_metadata['@graph']
                         if item['@id'] == 'ro-crate-metadata.json')
        sub_root = next(item for item in sub_metadata['@graph']
                       if item['@id'] == sub_root_id)
        
        # Verify subcrate relationships
        sub_parts = [part['@id'] for part in sub_root['hasPart']]
        self.assertIn(subcrate_dataset_id, sub_parts)
        self.assertIn(software_id, sub_parts)
        self.assertIn(computation_id, sub_parts)
        
        # Verify computation relationships
        computation = next(item for item in sub_metadata['@graph']
                         if item['@id'] == computation_id)
        self.assertIn(software_id, [item["@id"] for item in computation['usedSoftware']])
        self.assertIn(subcrate_dataset_id, [item["@id"] for item in computation['usedDataset']])

        for metadata_file in [self.test_dir / 'ro-crate-metadata.json', 
                                self.test_dir / 'subcrate' / 'ro-crate-metadata.json']:
            with open(metadata_file, 'r+') as f:
                metadata = json.load(f)
                metadata['@graph'][0]['conformsTo']['@id'] = 'https://w3id.org/ro/crate/1.1'
                metadata['@context'] = 'https://w3id.org/ro/crate/1.1/context'
                f.seek(0)
                json.dump(metadata, f, indent=2)
                f.truncate()

        # Validate both crates
        settings = services.ValidationSettings(
            rocrate_uri=str(self.test_dir),
            data_path=str(self.test_dir),
            profile_identifier='ro-crate-1.1',
            requirement_severity=models.Severity.REQUIRED
        )
        result = services.validate(settings)
        self.assertFalse(result.has_issues(), 
                        f"Top-level crate validation failed: {[i.message for i in result.get_issues()]}")

        subcrate_settings = services.ValidationSettings(
            rocrate_uri=str(self.test_dir / 'subcrate'),
            data_path=str(self.test_dir / 'subcrate'),
            profile_identifier='ro-crate-1.1',
            requirement_severity=models.Severity.REQUIRED
        )
        subcrate_result = services.validate(subcrate_settings)
        self.assertFalse(subcrate_result.has_issues(),
                        f"Subcrate validation failed: {[i.message for i in subcrate_result.get_issues()]}")

if __name__ == '__main__':
    unittest.main()
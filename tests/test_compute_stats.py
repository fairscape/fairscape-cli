import os
import sys
import pathlib
import json
import shutil
import unittest
import subprocess
import datetime
from typing import Tuple

class TestStatisticsCliWorkflow(unittest.TestCase):
    
    def setUp(self):
        # Create test directory
        self.test_dir = pathlib.Path.cwd() / 'tests' / 'stats-compute-tests'
        self.test_dir.mkdir(parents=True, exist_ok=True)
            
    def tearDown(self):
        # Only remove the generated files, not the entire directory
        metadata_file = self.test_dir / 'ro-crate-metadata.json'
        stats_file = self.test_dir / 'summary_stats_numbers.csv'
        
        if metadata_file.exists():
            metadata_file.unlink()
        if stats_file.exists():
            stats_file.unlink()

    def run_cli_command(self, command: str) -> Tuple[int, str, str]:
        """Run a CLI command and return returncode, stdout, stderr"""
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        return process.returncode, stdout.strip(), stderr.strip()

    def test_cli_workflow(self):
        # Change to test directory
        os.chdir(self.test_dir)
        
        # Initialize ROCrate
        init_cmd = '''python -m fairscape_cli rocrate init \
            --name "Data Analysis Project" \
            --organization-name "My Organization" \
            --project-name "Data Analysis" \
            --description "A project for analyzing data using summary statistics" \
            --keywords "data-analysis" --keywords "statistics" --keywords "python"'''
        
        returncode, stdout, stderr = self.run_cli_command(init_cmd)
        self.assertEqual(returncode, 0, f"ROCrate init failed: {stderr}")
        rocrate_guid = stdout.strip()
        
        # Register software
        software_cmd = f'''python -m fairscape_cli rocrate register software ./ \
            --name "Summary Statistics Generator" \
            --author "Your Name" \
            --version "1.0.0" \
            --description "Python script that generates summary statistics for CSV data" \
            --keywords "data-analysis" --keywords "statistics" --keywords "python" \
            --file-format "text/x-python" \
            --date-modified "{datetime.date.today().isoformat()}" \
            --filepath "summary.py"'''
        
        returncode, stdout, stderr = self.run_cli_command(software_cmd)
        self.assertEqual(returncode, 0, f"Software registration failed: {stderr}")
        software_guid = stdout.strip()
        
        # Register dataset
        dataset_cmd = f'''python -m fairscape_cli rocrate register dataset ./ \
            --name "Analysis Dataset" \
            --author "Your Name" \
            --version "1.0.0" \
            --date-published "{datetime.date.today().isoformat()}" \
            --description "Dataset for statistical analysis" \
            --keywords "data-analysis" --keywords "statistics" --keywords "python" \
            --data-format "text/csv" \
            --filepath "numbers.csv"'''
        
        returncode, stdout, stderr = self.run_cli_command(dataset_cmd)
        self.assertEqual(returncode, 0, f"Dataset registration failed: {stderr}")
        dataset_guid = stdout.strip()
        
        # Compute statistics
        compute_cmd = f'''python -m fairscape_cli rocrate compute-statistics ./ \
            --dataset-id "{dataset_guid}" \
            --software-id "{software_guid}" \
            --command "python"'''
        
        returncode, stdout, stderr = self.run_cli_command(compute_cmd)
        self.assertEqual(returncode, 0, f"Computation failed: {stderr}")
        computation_guid = stdout.strip()
        
        # Verify the metadata file exists and has correct structure
        metadata_file = self.test_dir / 'ro-crate-metadata.json'
        self.assertTrue(metadata_file.exists())
        
        # Load and verify metadata
        with open(metadata_file) as f:
            metadata = json.load(f)
            
        # Basic structure tests
        self.assertEqual(metadata['name'], "Data Analysis Project")
        self.assertEqual(metadata['@id'], rocrate_guid)
        
        # Verify all components are present in @graph
        guids = [item['@id'] for item in metadata['@graph']]
        self.assertIn(software_guid, guids)
        self.assertIn(dataset_guid, guids)
        self.assertIn(computation_guid, guids)
        
        # Find computation record
        computation = next(item for item in metadata['@graph'] if item['@id'] == computation_guid)
        
        # Verify computation relationships
        self.assertEqual(computation['usedSoftware'], [software_guid])
        self.assertEqual(computation['usedDataset'], [dataset_guid])
        self.assertTrue(len(computation['generated']) > 0)
        
        # Verify output file exists
        output_file = self.test_dir / 'summary_stats_numbers.csv'
        self.assertTrue(output_file.exists())
        
        # Find dataset record and verify it has summary statistics
        dataset = next(item for item in metadata['@graph'] if item['@id'] == dataset_guid)
        self.assertTrue('hasSummaryStatistics' in dataset)
        self.assertEqual(dataset['hasSummaryStatistics'], computation['generated'])

if __name__ == '__main__':
    unittest.main()
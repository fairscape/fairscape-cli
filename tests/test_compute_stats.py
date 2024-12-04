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
        summary_file = self.test_dir / 'fake_summary.csv'
        
        if metadata_file.exists():
            metadata_file.unlink()
        if stats_file.exists():
            stats_file.unlink()
        if summary_file.exists():
            summary_file.unlink()

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

    def test_dataset_with_summary_stats(self):
        # Change to test directory
        os.chdir(self.test_dir)
        
        # Initialize ROCrate
        init_cmd = '''python -m fairscape_cli rocrate init \
            --name "Dataset Summary Test" \
            --organization-name "Test Organization" \
            --project-name "Summary Stats Test" \
            --description "Testing dataset registration with summary statistics" \
            --keywords "data" --keywords "testing" --keywords "summary-stats"'''
        
        returncode, stdout, stderr = self.run_cli_command(init_cmd)
        self.assertEqual(returncode, 0, f"ROCrate init failed: {stderr}")
        rocrate_guid = stdout.strip()
        
        # Create fake summary file
        summary_path = self.test_dir / 'fake_summary.csv'
        with open(summary_path, 'w') as f:
            f.write("statistic,value\nmean,42.0\nmedian,41.5\nstd,5.2")
        
        # Register dataset with summary statistics
        dataset_cmd = f'''python -m fairscape_cli rocrate register dataset ./ \
            --name "Test Dataset" \
            --author "Test Author" \
            --version "1.0.0" \
            --date-published "{datetime.date.today().isoformat()}" \
            --description "Dataset with pre-existing summary statistics" \
            --keywords "data" --keywords "testing" \
            --data-format "text/csv" \
            --filepath "numbers.csv" \
            --summary-statistics-filepath "fake_summary.csv"'''
        
        returncode, stdout, stderr = self.run_cli_command(dataset_cmd)
        self.assertEqual(returncode, 0, f"Dataset registration failed: {stderr}")
        dataset_guid = stdout.strip()
        
        # Verify the metadata file exists and has correct structure
        metadata_file = self.test_dir / 'ro-crate-metadata.json'
        self.assertTrue(metadata_file.exists())
        
        # Load and verify metadata
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        # Find dataset record and verify it has summary statistics
        dataset = next(item for item in metadata['@graph'] if item['@id'] == dataset_guid)

        # Get summary stats ID
        summary_stats_id = dataset['hasSummaryStatistics']

        # Find the summary statistics dataset in the graph - with more flexible matching
        summary_stats = next(
            (item for item in metadata['@graph'] 
            if 'stats' in item['@id'] and item['@type'] == 'https://w3id.org/EVI#Dataset'),
            None
        )
        self.assertEqual(summary_stats['@type'], 'https://w3id.org/EVI#Dataset')
        self.assertTrue('stats' in summary_stats['@id'])
        self.assertEqual(summary_stats['author'], 'Test Author')
    
        computation = next(
            (item for item in metadata['@graph'] 
            if item['@type'] == 'https://w3id.org/EVI#Computation' and summary_stats_id in item.get('generated', [])),
            None
        )
        self.assertIsNotNone(computation)
        self.assertEqual(computation['usedDataset'], [dataset_guid])

if __name__ == '__main__':
    unittest.main()
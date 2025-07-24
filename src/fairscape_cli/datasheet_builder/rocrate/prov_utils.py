from typing import List, Dict, Tuple, Set, Optional, Any
from collections import Counter

class ProvenanceAnalyzer:
    """Analyzes provenance patterns in RO-Crate data."""
    
    def __init__(self, processor):
        self.processor = processor
        self.graph = processor.graph
        self.graph_ids = {item.get("@id") for item in self.graph if item.get("@id")}
    
    def extract_computation_patterns(self, computations: List[Dict], 
                                   subcrate_processors: Optional[Dict] = None) -> Tuple[List[str], List[Dict]]:
        """
        Extract input→output patterns from computations.
        Returns: (patterns list, external datasets list)
        """
        patterns = {}
        external_datasets = []
        
        for computation in computations:
            input_formats = set()
            output_formats = set()
            
            used_datasets = self._normalize_to_list(computation.get("usedDataset", []))
            
            for dataset_ref in used_datasets:
                dataset_id = self._extract_id(dataset_ref)
                if not dataset_id:
                    continue
                
                format_info = self._get_dataset_format_info(dataset_id, subcrate_processors)
                if format_info:
                    if format_info['is_external']:
                        display_fmt = f"{format_info['subcrate_name']} ({format_info['format']})"
                        input_formats.add(display_fmt)
                        external_datasets.append({
                            "id": dataset_id,
                            "format": format_info['format'],
                            "subcrate": format_info['subcrate_name']
                        })
                    else:
                        input_formats.add(format_info['format'])
                else:
                    if self._is_experiment(dataset_id):
                        input_formats.add("Sample")
            
            generated_datasets = self._normalize_to_list(computation.get("generated", []))
            for dataset_ref in generated_datasets:
                dataset_id = self._extract_id(dataset_ref)
                if dataset_id:
                    format_value = self.processor.get_dataset_format(dataset_id)
                    if format_value != "unknown":
                        output_formats.add(format_value)
            
            if input_formats and output_formats:
                pattern = f"{', '.join(sorted(input_formats))} → {', '.join(sorted(output_formats))}"
                patterns[pattern] = patterns.get(pattern, 0) + 1
        
        return list(patterns.keys()), external_datasets
    
    def extract_experiment_patterns(self, experiments: List[Dict]) -> List[str]:
        """Extract Sample→output patterns from experiments."""
        patterns = {}
        
        for experiment in experiments:
            output_formats = set()
            
            generated_datasets = self._normalize_to_list(experiment.get("generated", []))
            for dataset_ref in generated_datasets:
                dataset_id = self._extract_id(dataset_ref)
                if dataset_id:
                    format_value = self.processor.get_dataset_format(dataset_id)
                    if format_value != "unknown":
                        output_formats.add(format_value)
            
            if output_formats:
                pattern = f"Sample → {', '.join(sorted(output_formats))}"
                patterns[pattern] = patterns.get(pattern, 0) + 1
        
        return list(patterns.keys())
    
    def identify_crate_inputs(self) -> List[Dict]:
        """
        Identify datasets that are inputs to the crate (not generated internally).
        These are datasets in the graph that don't have a 'generatedBy' property.
        """
        internal_inputs = []
        
        for item in self.graph:
            if not self._is_dataset(item):
                continue
            
            if not item.get("generatedBy"):
                format_value = item.get("format", "unknown")
                if format_value == "unknown" and self._is_experiment(item.get("@id", "")):
                    format_value = "Sample"
                    
                internal_inputs.append({
                    "id": item.get("@id", ""),
                    "format": format_value,
                    "subcrate": ""
                })
        
        return internal_inputs
    
    def aggregate_input_datasets(self, external_datasets: List[Dict], 
                               internal_inputs: List[Dict]) -> Dict[str, int]:
        """
        Aggregate input datasets by format and subcrate.
        Returns dict with keys like "SubcrateName, format" or just "format" for internal.
        """
        all_inputs = external_datasets + internal_inputs
        aggregated = {}
        
        for dataset in all_inputs:
            fmt = dataset["format"]
            subcrate_name = dataset["subcrate"]
            
            if subcrate_name:
                key = f"{subcrate_name}, {fmt}"
            else:
                key = fmt
            
            aggregated[key] = aggregated.get(key, 0) + 1
        
        return aggregated
    
    def _normalize_to_list(self, value: Any) -> List:
        """Convert single values or dicts to list format."""
        if not value:
            return []
        if isinstance(value, list):
            return value
        return [value]
    
    def _extract_id(self, ref: Any) -> Optional[str]:
        """Extract @id from various reference formats."""
        if isinstance(ref, dict) and "@id" in ref:
            return ref["@id"]
        elif isinstance(ref, str):
            return ref
        return None
    
    def _is_dataset(self, item: Dict) -> bool:
        """Check if an item is a dataset type."""
        item_type = item.get("@type", [])
        if isinstance(item_type, str):
            item_type = [item_type]
        
        dataset_types = ["Dataset", "EVI:Dataset", "https://w3id.org/EVI#Dataset"]
        return any(dt in item_type for dt in dataset_types)
    
    def _is_experiment(self, item_id: str) -> bool:
        """Check if an item ID refers to an experiment."""
        for item in self.graph:
            if item.get("@id") == item_id:
                item_type = item.get("@type", [])
                if isinstance(item_type, str):
                    item_type = [item_type]
                
                experiment_types = ["Experiment", "EVI:Experiment", "https://w3id.org/EVI#Experiment"]
                return any(et in item_type for et in experiment_types)
        return False
    
    def _get_dataset_format_info(self, dataset_id: str, 
                               subcrate_processors: Optional[Dict] = None) -> Optional[Dict]:
        """
        Get format info for a dataset, checking local and external sources.
        Returns dict with format, is_external flag, and subcrate_name if external.
        """
        format_value = self.processor.get_dataset_format(dataset_id)
        if format_value != "unknown":
            return {
                'format': format_value,
                'is_external': False,
                'subcrate_name': None
            }
        
        if subcrate_processors:
            for subcrate_id, subcrate_proc in subcrate_processors.items():
                if subcrate_proc:
                    format_value = subcrate_proc.get_dataset_format(dataset_id)
                    if format_value != "unknown":
                        return {
                            'format': format_value,
                            'is_external': True,
                            'subcrate_name': subcrate_proc.root.get("name", "Unknown")
                        }
        
        return None
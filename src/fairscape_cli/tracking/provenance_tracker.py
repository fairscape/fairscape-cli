from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional

from fairscape_cli.models.rocrate import ReadROCrateMetadata, AppendCrate
from fairscape_cli.models.dataset import GenerateDataset, Dataset
from fairscape_cli.models.software import GenerateSoftware, Software
from fairscape_cli.models.computation import GenerateComputation, Computation

from .config import ProvenanceConfig, TrackingResult
from .io_capture import IOCapture
from .metadata_generator import MetadataGenerator, FallbackMetadataGenerator, create_metadata_generator
from .utils import collect_dataset_samples, format_samples_for_prompt

from fairscape_cli.models.rocrate import GenerateROCrate
from datetime import datetime


class ProvenanceTracker:
    """Tracks computational provenance and generates RO-Crate metadata."""
    
    def __init__(
        self,
        config: ProvenanceConfig,
        metadata_generator: Optional[MetadataGenerator] = None
    ):
        self.config = config
        self.metadata_generator = metadata_generator
        self.filepath_to_guid: Dict[str, str] = {}
        self.crate_metadata = None
        
        self._ensure_crate_exists()
        self._load_crate_context()
    
    def _ensure_crate_exists(self):
        """Create RO-Crate if it doesn't exist with placeholder metadata."""
        metadata_path = self.config.rocrate_path / 'ro-crate-metadata.json'
        
        if metadata_path.exists():
            return
        
        placeholder_name = f"Research Project {datetime.now().strftime('%Y%m%d')}"
        placeholder_description = "Automatically generated RO-Crate for computational provenance tracking"
        
        GenerateROCrate(
            path=self.config.rocrate_path,
            guid=None,  
            name=placeholder_name,
            description=placeholder_description,
            author=self.config.author if self.config.author != "Unknown" else "Researcher",
            keywords=self.config.keywords,
            datePublished=datetime.now().isoformat(),
            version="1.0",
            license="https://creativecommons.org/licenses/by/4.0/"
        )
    

    def _load_crate_context(self):
        """Load existing RO-Crate and build filepath to GUID mapping."""
        try:
            self.crate_metadata = ReadROCrateMetadata(self.config.rocrate_path)
            
            root_dataset = self.crate_metadata['@graph'][1]
            
            if self.config.author == "Unknown":
                if hasattr(root_dataset, 'author') and root_dataset.author:
                    self.config.author = root_dataset.author
            
            if self.config.keywords == ["jupyter", "computation"]:
                if hasattr(root_dataset, 'keywords') and root_dataset.keywords:
                    self.config.keywords = root_dataset.keywords
            
            for entity in self.crate_metadata.get('@graph', []):
                entity_types = getattr(entity, '@type', [])
                if isinstance(entity_types, str):
                    entity_types = [entity_types]
                
                content_url = getattr(entity, 'contentUrl', None)
                if content_url and content_url.startswith('file://'):
                    relative_path = content_url.replace('file:///', '').lstrip('/')
                    filepath_full = (self.config.rocrate_path / relative_path).resolve()
                    self.filepath_to_guid[str(filepath_full)] = getattr(entity, 'guid')
                        
            print(self.filepath_to_guid)
            
        except Exception as e:
            raise RuntimeError(f"Could not read RO-Crate at {self.config.rocrate_path}: {e}")
    
    def _resolve_manual_inputs(self) -> Set[str]:
        """Convert manual input paths to absolute paths."""
        manual_input_paths = set()
        for manual_input in self.config.manual_inputs:
            manual_path = Path(manual_input)
            if not manual_path.is_absolute():
                manual_path = (self.config.rocrate_path / manual_input).resolve()
            else:
                manual_path = manual_path.resolve()
            manual_input_paths.add(str(manual_path))
        return manual_input_paths
    
    def _resolve_inputs(self, io_capture: IOCapture) -> tuple[List[Dataset], int]:
        """Resolve input datasets, reusing existing ones where possible."""
        all_input_files = set(io_capture.inputs)
        all_input_files.update(self._resolve_manual_inputs())
        
        input_datasets = []
        reused_count = 0
        
        for input_file in all_input_files:
            input_path = Path(input_file)
            
            if not input_path.exists():
                print(f"WARNING: Input file does not exist: {input_file}")
                continue
            
            normalized_path = input_path.resolve()
            
            if str(normalized_path) in self.filepath_to_guid:
                existing_guid = self.filepath_to_guid[str(normalized_path)]
                print(f"Reusing existing dataset: {input_path.name} ({existing_guid})")
                
                existing_dataset = next(
                    (e for e in self.crate_metadata['@graph'] if e.get('@id') == existing_guid),
                    None
                )
                if existing_dataset:
                    dataset_obj = Dataset(**existing_dataset)
                    input_datasets.append(dataset_obj)
                    reused_count += 1
                continue
            
            rel_path = input_path.relative_to(self.config.rocrate_path) if input_path.is_relative_to(self.config.rocrate_path) else input_path
            
            dataset_metadata = GenerateDataset(
                name=input_path.name,
                author=self.config.author,
                version="1.0",
                description=f"Input dataset",
                keywords=self.config.keywords,
                format=input_path.suffix.lstrip('.') or "unknown",
                filepath=str(rel_path),
                datePublished=datetime.now().isoformat(),
                cratePath=self.config.rocrate_path
            )
            input_datasets.append(dataset_metadata)
        
        return input_datasets, reused_count
    
    def _resolve_outputs(self, io_capture: IOCapture) -> List[Dataset]:
        """Resolve output datasets."""
        output_datasets = []
        
        for output_file in io_capture.outputs:
            output_path = Path(output_file)
            normalized_output = output_path.resolve()
            
            if str(normalized_output) in self.filepath_to_guid:
                print(f"WARNING: Overwriting existing dataset: {output_path.name}")
            
            rel_path = output_path.relative_to(self.config.rocrate_path) if output_path.is_relative_to(self.config.rocrate_path) else output_path
            
            dataset_metadata = GenerateDataset(
                name=output_path.name,
                author=self.config.author,
                version="1.0",
                description=f"Output dataset",
                keywords=self.config.keywords,
                format=output_path.suffix.lstrip('.') or "unknown",
                filepath=str(rel_path),
                datePublished=datetime.now().isoformat(),
                generatedBy=[],
                cratePath=self.config.rocrate_path
            )
            output_datasets.append(dataset_metadata)
        
        return output_datasets
    
    def _enhance_with_llm(
        self,
        code: str,
        input_datasets: List[Dataset],
        output_datasets: List[Dataset]
    ) -> Optional[Dict]:
        """Use LLM to generate better descriptions if available."""

        if not self.metadata_generator:
            return None
        
        all_input_files = set()
        for ds in input_datasets:
            if ds.contentUrl:
                url = ds.contentUrl if isinstance(ds.contentUrl, str) else ds.contentUrl[0]
                filepath = url.replace('file:///', '').replace('file:', '')
                full_path = str((self.config.rocrate_path / filepath).resolve())
                all_input_files.add(full_path)

        all_output_files = set()
        for ds in output_datasets:
            if ds.contentUrl:
                url = ds.contentUrl if isinstance(ds.contentUrl, str) else ds.contentUrl[0]
                filepath = url.replace('file://', '').replace('file:', '')
                full_path = str((self.config.rocrate_path / filepath).resolve())
                all_output_files.add(full_path)
        
        input_samples = collect_dataset_samples(all_input_files)
        output_samples = collect_dataset_samples(all_output_files)
        
        if not input_samples and not output_samples:
            return None
        
        input_samples_str = format_samples_for_prompt(input_samples)
        output_samples_str = format_samples_for_prompt(output_samples)
        
        return self.metadata_generator.generate_descriptions(
            code, 
            input_samples_str, 
            output_samples_str
        )
    
    def _apply_llm_descriptions(
        self,
        llm_descriptions: Optional[Dict],
        software_name: str,
        input_datasets: List[Dataset],
        output_datasets: List[Dataset]
    ) -> tuple[str, str]:
        """Apply LLM descriptions to datasets and return software/computation descriptions."""
        software_description = f"Code executed"
        computation_description = f"Computation executed"
        
        if llm_descriptions:
            if 'software_description' in llm_descriptions:
                software_description = llm_descriptions['software_description']
            
            if 'computation_description' in llm_descriptions:
                computation_description = llm_descriptions['computation_description']
            
            if 'input_datasets' in llm_descriptions:
                for ds in input_datasets:
                    if ds.name in llm_descriptions['input_datasets']:
                        ds.description = llm_descriptions['input_datasets'][ds.name]
            
            if 'output_datasets' in llm_descriptions:
                for ds in output_datasets:
                    if ds.name in llm_descriptions['output_datasets']:
                        ds.description = llm_descriptions['output_datasets'][ds.name]
        
        return software_description, computation_description
    
    def _create_software(self, code: str, name: str, description: str) -> Software:
        """Create software metadata."""
        software_filepath = f"software/{name}.py"
        software_full_path = self.config.rocrate_path / software_filepath
        software_full_path.parent.mkdir(parents=True, exist_ok=True)
        software_full_path.write_text(code)
        
        return GenerateSoftware(
            name=name,
            author=self.config.author,
            version="1.0",
            description=description,
            dateModified=datetime.now().isoformat(),
            keywords=self.config.keywords,
            fileFormat="py",
            filepath=software_filepath,
            cratePath=self.config.rocrate_path
        )
    
    def _create_computation(
        self,
        name: str,
        description: str,
        software: Software,
        input_datasets: List[Dataset],
        output_datasets: List[Dataset]
    ) -> Computation:
        """Create computation metadata."""
        computation = GenerateComputation(
            name=name,
            runBy=self.config.author,
            dateCreated=datetime.now().isoformat(),
            description=description,
            keywords=self.config.keywords,
            usedSoftware=[software.guid],
            usedDataset=[ds.guid for ds in input_datasets],
            generated=[ds.guid for ds in output_datasets]
        )
        
        for output_ds in output_datasets:
            output_ds.generatedBy = {"@id": computation.guid}
        
        return computation
    
    def track_execution(
        self,
        code: str,
        io_capture: IOCapture,
        execution_name: Optional[str] = None
    ) -> TrackingResult:
        """Track a code execution and generate provenance metadata."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        execution_name = execution_name or f"cell_{timestamp}"
        
        if not io_capture.inputs and not io_capture.outputs and not self.config.manual_inputs:
            print("No file I/O detected in execution")
            raise ValueError("No file I/O detected")
        
        input_datasets, reused_count = self._resolve_inputs(io_capture)
        output_datasets = self._resolve_outputs(io_capture)
        
        llm_descriptions = self._enhance_with_llm(code, input_datasets, output_datasets)
        
        software_description, computation_description = self._apply_llm_descriptions(
            llm_descriptions,
            execution_name,
            input_datasets,
            output_datasets
        )
        
        software = self._create_software(code, execution_name, software_description)
        
        computation = self._create_computation(
            f"Computation_{execution_name}",
            computation_description,
            software,
            input_datasets,
            output_datasets
        )
        
        new_datasets = []
        for ds in input_datasets:
            if ds.contentUrl:
                url = ds.contentUrl if isinstance(ds.contentUrl, str) else ds.contentUrl[0]
                filepath = url.replace('file://', '').replace('file:', '')
                full_path = str((self.config.rocrate_path / filepath).resolve())
                if full_path not in self.filepath_to_guid:
                    new_datasets.append(ds)
        
        elements = [software] + new_datasets + output_datasets + [computation]
        AppendCrate(cratePath=self.config.rocrate_path, elements=elements)
        
        return TrackingResult(
            computation_guid=computation.guid,
            software_guid=software.guid,
            input_count=len(input_datasets),
            output_count=len(output_datasets),
            reused_count=reused_count,
            new_datasets=len(new_datasets)
        )

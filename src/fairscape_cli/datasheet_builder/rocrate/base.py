import os
from pathlib import Path
import json
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional

from .models import AIReadyCrate, AIReadySummary, AIReadyCriterion, CrateComposition, CrateContent
from .prov_utils import ProvenanceAnalyzer

class ROCrateProcessor:
    """
    Low-level class for parsing a single ro-crate-metadata.json file.
    Its job is to read the raw JSON and provide basic access to its contents.
    """
    
    def __init__(self, json_path: str, published: bool = False):
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Metadata file not found: {json_path}")
            
        with open(json_path, 'r', encoding='utf-8') as f:
            self.json_data = json.load(f)
        
        self.graph = self.json_data.get("@graph", [])
        self.root = self._find_root_node()
        self.published = published
        self.prov_analyzer = ProvenanceAnalyzer(self)
    
    def _find_root_node(self) -> Dict[str, Any]:
        """Find the root Dataset/ROCrate node in the graph."""
        metadata_node = next((item for item in self.graph if item.get("@id") == "ro-crate-metadata.json"), None)
        if metadata_node and 'about' in metadata_node:
            root_id = metadata_node['about'].get('@id')
            root_node = next((item for item in self.graph if item.get('@id') == root_id), None)
            if root_node:
                return root_node

        for item in self.graph:
            item_types = item.get("@type", [])
            if isinstance(item_types, str): item_types = [item_types]
            if "Dataset" in item_types and "https://w3id.org/EVI#ROCrate" in item_types:
                return item
        
        return self.graph[1] if len(self.graph) > 1 else {}
    
    def find_subcrates(self) -> List[Dict[str, str]]:
        """Find entities in hasPart that are described as RO-Crates."""
        subcrates = []
        if 'hasPart' not in self.root:
            return []

        has_part_ids = {part.get('@id') for part in self.root.get('hasPart', []) if isinstance(part, dict)}

        for item in self.graph:
            if item.get('@id') in has_part_ids and item.get("ro-crate-metadata"):
                subcrates.append({
                    "id": item.get("@id", ""),
                    "metadata_path": item.get("ro-crate-metadata", "")
                })
        return subcrates
    
    def categorize_items(self) -> Tuple[list, ...]:
        """Categorize all non-root, non-subcrate entities in the graph."""
        items = [[] for _ in range(8)]
        categories = ["Dataset", "Software", "Instrument", "Sample", "Experiment", "Computation", "Schema"]
        
        root_id = self.root.get('@id')
        
        for item in self.graph:
            item_id = item.get("@id")
            if not item_id or item_id == root_id or item_id == "ro-crate-metadata.json" or "ro-crate-metadata" in item:
                continue

            item_types = item.get("@type", [])
            if isinstance(item_types, str): item_types = [item_types]
            
            found = False
            for i, cat in enumerate(categories):
                if any(cat in t for t in item_types):
                    items[i].append(item)
                    found = True
                    break
            if not found:
                items[7].append(item)
        
        return tuple(items)

    def get_formats_summary(self, items: List[Dict]) -> Dict[str, int]:
        formats = [item.get("format", "unknown") for item in items if isinstance(item, dict)]
        return Counter(formats)
    
    def get_dataset_format(self, dataset_id: str) -> str:
        """Get the format of a dataset by its ID."""
        for item in self.graph:
            if item.get("@id") == dataset_id:
                return item.get("format", "unknown")
        return "unknown"
    
    def get_property_value(self, property_name: str, additional_properties: List[Dict]) -> Optional[str]:
        """Extract value from additionalProperty list by name."""
        for prop in additional_properties:
            if prop.get("name") == property_name:
                return prop.get("value")
        return None
    
    def extract_computation_patterns(self, computations: List[Dict], 
                                   subcrate_processors: Optional[Dict] = None) -> Tuple[List[str], List[Dict]]:
        """Extract computation input→output patterns using ProvenanceAnalyzer."""
        return self.prov_analyzer.extract_computation_patterns(computations, subcrate_processors)
    
    def extract_experiment_patterns(self, experiments: List[Dict]) -> List[str]:
        """Extract experiment Sample→output patterns using ProvenanceAnalyzer."""
        return self.prov_analyzer.extract_experiment_patterns(experiments)
    
    def identify_crate_inputs(self) -> List[Dict]:
        """Identify datasets that are inputs to this crate."""
        return self.prov_analyzer.identify_crate_inputs()
    
    def aggregate_input_datasets(self, external_datasets: List[Dict], 
                               internal_inputs: List[Dict]) -> Dict[str, int]:
        """Aggregate input datasets by format and source."""
        return self.prov_analyzer.aggregate_input_datasets(external_datasets, internal_inputs)
    
    def get_access_summary(self, items: List[Dict]) -> Dict[str, int]:
        """Placeholder for access summary - implement if needed."""
        return {}
    
    def extract_cell_line_info(self, samples: List[Dict]) -> List[str]:
        """Placeholder for cell line extraction - implement if needed."""
        return []
    
    def extract_sample_species(self, samples: List[Dict]) -> List[str]:
        """Placeholder for species extraction - implement if needed."""
        return []
    
    def extract_experiment_types(self, experiments: List[Dict]) -> List[str]:
        """Placeholder for experiment type extraction - implement if needed."""
        return []


class ReleaseProcessor:
    """
    High-level class to process a full data release.
    It orchestrates the processing of the main release crate and all its sub-crates,
    populating a comprehensive AIReadyCrate data model.
    """
    def __init__(self, metadata_path: Path, published: bool = False):
        self.metadata_path = metadata_path
        self.base_dir = metadata_path.parent
        self.published = published

        self.main_processor = ROCrateProcessor(json_path=str(metadata_path), published=published)
        
        self.subcrate_processors: Dict[str, ROCrateProcessor] = {}
        subcrates_info = self.main_processor.find_subcrates()
        for info in subcrates_info:
            full_path = self.base_dir / info['metadata_path']
            if full_path.exists():
                sub_proc = ROCrateProcessor(json_path=str(full_path), published=self.published)
                self.subcrate_processors[sub_proc.root.get('@id')] = sub_proc
        
        self.release_model = self._build_release_model()

    def _process_single_crate(self, processor: ROCrateProcessor, is_subcrate: bool = False) -> AIReadyCrate:
        """Processes one crate (main or sub) into a populated AIReadyCrate model."""
        root = processor.root
        categorized_items = processor.categorize_items()
        
        authors = root.get("author", "Unknown")
        if isinstance(authors, list):
            authors = ", ".join(authors)

        publications = root.get("associatedPublication", [])
        if isinstance(publications, str):
            publications = publications.split(",")
        
        datasets, software, instruments, samples, experiments, computations, schemas, other = categorized_items

        composition = CrateComposition(
            datasets=len(datasets), software=len(software), instruments=len(instruments),
            samples=len(samples), experiments=len(experiments), computations=len(computations),
            schemas=len(schemas), other=len(other), total_size=root.get("contentSize", "N/A"),
            file_formats=processor.get_formats_summary(datasets),
            software_formats=processor.get_formats_summary(software),
        )
        
        if is_subcrate:
            patterns, external_datasets = processor.extract_computation_patterns(
                computations, self.subcrate_processors
            )
            internal_inputs = processor.identify_crate_inputs()
            
            composition.computation_patterns = patterns
            composition.experiment_patterns = processor.extract_experiment_patterns(experiments)
            composition.input_datasets = processor.aggregate_input_datasets(
                external_datasets, internal_inputs
            )
            composition.input_datasets_count = len(external_datasets) + len(internal_inputs)

        content = CrateContent(
            datasets=datasets, software=software, instruments=instruments, samples=samples,
            experiments=experiments, computations=computations, schemas=schemas, other=other
        )

        return AIReadyCrate(
            guid=root.get("@id", ""), name=root.get("name", "Untitled"),
            description=root.get("description", ""), author=authors,
            version=root.get("version", ""), keywords=root.get("keywords", []),
            license=root.get("license", ""), date_published=root.get("datePublished", ""),
            doi=root.get("identifier", ""), publisher=root.get("publisher", ""),
            principal_investigator=root.get("principalInvestigator", ""),
            contact_email=root.get("contactEmail", ""), funder=root.get("funder", ""),
            citation=root.get("citation", ""), conditions_of_access=root.get("conditionsOfAccess", ""),
            copyright_notice=root.get("copyrightNotice", ""), confidentiality_level=root.get("confidentialityLevel", ""),
            usage_info=root.get("usage_info", ""), ethical_review=root.get("ethicalReview", ""),
            published=processor.published, associated_publication=publications,
            evidence_graph_path=root.get("hasEvidenceGraph", {}).get("@id"),
            composition=composition, content=content
        )

    def _build_release_model(self) -> AIReadyCrate:
        """Builds the nested AIReadyCrate model for the entire release."""
        release_model = self._process_single_crate(self.main_processor, is_subcrate=False)
        
        subcrate_models = []
        for sub_proc in self.subcrate_processors.values():
            sub_model = self._process_single_crate(sub_proc, is_subcrate=True)
            info = next((i for i in self.main_processor.find_subcrates() if i.get('id') == sub_model.guid), None)
            if info:
                sub_model.metadata_path = str(Path(info['metadata_path']).parent)
            subcrate_models.append(sub_model)
        
        release_model.subcrates = sorted(subcrate_models, key=lambda x: x.name)

        self._aggregate_composition(release_model, subcrate_models)

        release_model.ai_ready_summary = self._generate_ai_summary()
        
        return release_model

    def _aggregate_composition(self, release_model: AIReadyCrate, subcrates: List[AIReadyCrate]):
        """Sums up composition data from sub-crates into the release model."""
        agg_composition = CrateComposition()
        file_formats_counter = Counter()
        software_formats_counter = Counter()

        for sub in subcrates:
            agg_composition.datasets += sub.composition.datasets
            agg_composition.software += sub.composition.software
            agg_composition.computations += sub.composition.computations
            agg_composition.experiments += sub.composition.experiments
            agg_composition.samples += sub.composition.samples
            agg_composition.instruments += sub.composition.instruments
            agg_composition.schemas += sub.composition.schemas
            agg_composition.other += sub.composition.other
            file_formats_counter.update(sub.composition.file_formats)
            software_formats_counter.update(sub.composition.software_formats)
        
        agg_composition.total_size = self.main_processor.root.get("contentSize", "N/A")
        agg_composition.file_formats = dict(file_formats_counter)
        agg_composition.software_formats = dict(software_formats_counter)
        release_model.composition = agg_composition

    def _calculate_score(self, checks: Dict[str, Tuple[bool, str]]) -> Tuple[int, int]:
        passed = sum(1 for passed, _ in checks.values() if passed)
        return passed, len(checks)

    def _generate_ai_summary(self) -> AIReadySummary:
            """Generates the high-level AI-Readiness summary for the main release."""
            root = self.main_processor.root
            
            fair_checks = {
                "Findable": (bool(root.get('identifier')), f"DOI: {root.get('identifier', 'Not Found')}"),
                "Accessible": (True, "Default: Metadata is accessible via RO-Crate."),
                "Interoperable": (True, "Default: Uses schema.org in RO-Crate format."),
                "Reusable": (bool(root.get('license')), f"License: {root.get('license', 'Not specified')}")
            }
            fair_passed, fair_total = self._calculate_score(fair_checks)
            
            _, software, _, _, experiments, computations, _, _ = self.main_processor.categorize_items()
            prov_checks = {
                "Transparent": (True, "Default: Ground-truth sources are the initial datasets in the provenance graph."),
                "Traceable": (len(computations) + len(experiments) > 0, f"{len(computations) + len(experiments)} computations/experiments documented."),
                "Interpretable": (len(software) > 0, f"{len(software)} software items documented."),
                "Key Actors Identified": (bool(root.get('author')), f"Authors: {root.get('author', 'Not specified')}")
            }
            prov_passed, prov_total = self._calculate_score(prov_checks)
            
            char_checks = {
                "Semantics": (True, "Default: Data is semantically described using schema.org."),
                "Statistics": (bool(root.get('contentSize')), f"Total size: {root.get('contentSize', 'N/A')}."),
                "Standards": (True, "Default: Adheres to RO-Crate community standards."),
                "Potential Sources of Bias": (bool(root.get('rai:dataBiases')), f"Bias statement provided: {'Yes' if root.get('rai:dataBiases') else 'No'}.")
            }
            char_passed, char_total = self._calculate_score(char_checks)

            expl_checks = {
                "Data Documentation Template": (True, "Default: Documentation via RO-Crate, Datasheet, and RAI properties."),
                "Fit for Purpose": (bool(root.get('rai:dataUseCases')), f"Use cases documented: {'Yes' if root.get('rai:dataUseCases') else 'No'}."),
                "Verifiable": (True, "Assumption: MD5 checksums can be implemented.")
            }
            expl_passed, expl_total = self._calculate_score(expl_checks)

            eth_checks = {
                "Ethically Acquired": (bool(root.get('rai:dataCollection')), f"Collection process described: {'Yes' if root.get('rai:dataCollection') else 'No'}."),
                "Ethically Managed": (bool(root.get('ethicalReview')), f"Ethical review contact provided: {'Yes' if root.get('ethicalReview') else 'No'}."),
                "Ethically Disseminated": (bool(root.get('license')), "License is specified."),
                "Secure": (bool(root.get('confidentialityLevel')), f"Confidentiality: {root.get('confidentialityLevel', 'N/A')}.")
            }
            eth_passed, eth_total = self._calculate_score(eth_checks)
            
            sustain_passed, sustain_total = (2, 4)
            comp_passed, comp_total = (4, 4)
            
            return AIReadySummary(
                fairness=AIReadyCriterion(name="FAIRness", score=fair_passed, max_score=fair_total, evidence=f"{fair_passed}/{fair_total} checks passed", sub_criteria_evidence={k: v[1] for k, v in fair_checks.items()}),
                provenance=AIReadyCriterion(name="Provenance", score=prov_passed, max_score=prov_total, evidence=f"{prov_passed}/{prov_total} checks passed", sub_criteria_evidence={k: v[1] for k, v in prov_checks.items()}),
                characterization=AIReadyCriterion(name="Characterization", score=char_passed, max_score=char_total, evidence=f"{char_passed}/{char_total} checks passed", sub_criteria_evidence={k: v[1] for k, v in char_checks.items()}),
                pre_model_explainability=AIReadyCriterion(name="Pre-Model Explainability", score=expl_passed, max_score=expl_total, evidence=f"{expl_passed}/{expl_total} checks passed", sub_criteria_evidence={k: v[1] for k, v in expl_checks.items()}),
                ethics=AIReadyCriterion(name="Ethics", score=eth_passed, max_score=eth_total, evidence=f"{eth_passed}/{eth_total} checks passed", sub_criteria_evidence={k: v[1] for k, v in eth_checks.items()}),
                sustainability=AIReadyCriterion(name="Sustainability", score=sustain_passed, max_score=sustain_total, evidence="Placeholder"),
                computability=AIReadyCriterion(name="Computability", score=comp_passed, max_score=comp_total, evidence="Placeholder")
            )
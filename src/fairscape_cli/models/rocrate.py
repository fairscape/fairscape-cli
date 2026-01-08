import pathlib
import shutil
import json
from datetime import datetime
from typing import Optional, Union, List, Literal, Dict, Any, Set
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, ConfigDict, model_validator
import uuid 
import mongomock

from fairscape_cli.config import NAAN, DEFAULT_CONTEXT
from fairscape_cli.models.software import Software
from fairscape_cli.models.dataset import Dataset
from fairscape_cli.models.computation import Computation
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid

from datetime import datetime
import pathlib
import json
from typing import List, Optional, Dict, Any, Tuple

from fairscape_cli.config import NAAN, DEFAULT_CONTEXT
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid, clean_guid
from fairscape_models.rocrate import ROCrateV1_2, ROCrateMetadataElem, ROCrateMetadataFileElem

def GenerateROCrate(
   path: pathlib.Path,
   guid: str,
   name: str, 
   **kwargs
):
   if not guid:
       sq = GenerateDatetimeSquid()
       seg = clean_guid(f"{name.lower().replace(' ', '-')}-{sq}")
       guid = f"ark:{NAAN}/rocrate-{seg}"

   metadata_descriptor = ROCrateMetadataFileElem.model_validate({
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"},
        "about": {"@id": guid}
    })

   root_metadata = {
       "@id": guid,
       "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
       "name": name,
       "hasPart": []
   }
   
   if "organizationName" in kwargs:
       organization_guid = f"ark:{NAAN}/organization-{kwargs['organizationName'].lower().replace(' ', '-')}-{GenerateDatetimeSquid()}"
       root_metadata["isPartOf"] = [{"@id": organization_guid}]
       del kwargs["organizationName"]
       
   if "projectName" in kwargs:
       project_guid = f"ark:{NAAN}/project-{kwargs['projectName'].lower().replace(' ', '-')}-{GenerateDatetimeSquid()}"
       if "isPartOf" not in root_metadata:
           root_metadata["isPartOf"] = []
       root_metadata["isPartOf"].append({"@id": project_guid})
       del kwargs["projectName"]
   
   if "license" in kwargs:
       root_metadata["license"] = kwargs["license"]
       del kwargs["license"]
   else:
       root_metadata["license"] = "https://creativecommons.org/licenses/by/4.0/"
   
   for key, value in kwargs.items():
       if value is not None:
           root_metadata[key] = value

   root_dataset = ROCrateMetadataElem(**root_metadata)
   
   rocrate = ROCrateV1_2(**{
       "@context":DEFAULT_CONTEXT,
       "@graph":[
           metadata_descriptor, 
           root_dataset
       ]}
   )

   rocrate_dict = rocrate.model_dump(by_alias=True, exclude_none=True)

   if 'ro-crate-metadata.json' in str(path):
       roCrateMetadataPath = path
       if not path.parent.exists():
           path.parent.mkdir(parents=True, exist_ok=True)
   else:
       roCrateMetadataPath = path / 'ro-crate-metadata.json'
       if not path.exists():
           path.mkdir(parents=True, exist_ok=True)

   with roCrateMetadataPath.open(mode="w") as metadataFile:
       json.dump(rocrate_dict, metadataFile, indent=2)

   return root_dataset.model_dump(by_alias=True, exclude_none=True)
class ROCrate(ROCrateMetadataElem):
    model_config = ConfigDict(populate_by_name=True)

    guid: Optional[str] = Field(alias="@id", default=None)
    name: str = Field(max_length=200)
    description: str = Field(min_length=5)
    author: Optional[str] = None
    datePublished: Optional[datetime] = None
    license: Optional[str] = None
    version: Optional[str] = None
    keywords: List[str]
    projectName: Optional[str] = None
    organizationName: Optional[str] = None
    path: pathlib.Path

    def generate_guid(self) -> str:
        if self.guid is None:
            sq = GenerateDatetimeSquid()
            self.guid = f"ark:{NAAN}/rocrate-{self.name.replace(' ', '-').lower()}-{sq}"
        return self.guid

    def createCrateFolder(self):
        self.path.mkdir(parents=True, exist_ok=True)

    def create_subcrate(
        self,
        subcrate_path: pathlib.Path,
        name: str,
        description: str,
        keywords: List[str],
        organization_name: Optional[str] = None,
        project_name: Optional[str] = None,
        guid: Optional[str] = None,
        author: Optional[str] = None,
        version: Optional[str] = None,
        license: Optional[str] = None
    ) -> str:
        parent_metadata_path = self.path / 'ro-crate-metadata.json'
        with parent_metadata_path.open('r') as f:
            parent_metadata = json.load(f)
            parent_id = parent_metadata['@graph'][1]['@id']
        
        if author is None:
            author = getattr(self, 'author', "Unknown")
        if version is None:
            version = getattr(self, 'version', "1.0")
        if license is None:
            license = getattr(self, 'license', "https://creativecommons.org/licenses/by/4.0/")
        
        full_subcrate_path = self.path / subcrate_path
        
        subcrate = GenerateROCrate(
            path=full_subcrate_path,
            guid=guid,
            name=name,
            description=description,
            keywords=keywords,
            author=author,
            version=version,
            license=license,
            organizationName=organization_name,
            projectName=project_name,
            datePublished=datetime.now().isoformat(),
            isPartOf=[{"@id": parent_id}],
            hasPart=[]
        )
        
        subcrate_metadata_path = full_subcrate_path / 'ro-crate-metadata.json'
        with subcrate_metadata_path.open('r+') as f:
            subcrate_metadata = json.load(f)
            root_dataset = subcrate_metadata['@graph'][1]
            
            root_dataset['isPartOf'] = [{"@id": parent_id}]
            
            f.seek(0)
            f.truncate()
            json.dump(subcrate_metadata, f, indent=2)
        
        with parent_metadata_path.open('r+') as f:
            parent_metadata = json.load(f)
            root_dataset = parent_metadata['@graph'][1]
            
            if 'hasPart' not in root_dataset:
                root_dataset['hasPart'] = []
            
            subcrate_ref = {
                "@id": subcrate['@id'],
                "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
                "name": name,
                "description": description,
                "keywords": keywords,
                "author": author,
                "version": version,
                "license": license,
                "isPartOf": [{"@id": parent_id}],
                "hasPart": [],
                "contentUrl": f"file:///{str(subcrate_path / 'ro-crate-metadata.json')}",
                "datePublished": datetime.now().isoformat()
            }
            
            parent_metadata['@graph'].append(subcrate_ref)
            
            if not any(part.get('@id') == subcrate['@id'] for part in root_dataset['hasPart']):
                root_dataset['hasPart'].append({"@id": subcrate['@id']})
            
            if 'version' not in root_dataset:
                root_dataset['version'] = getattr(self, 'version', "1.0")
            if 'author' not in root_dataset:
                root_dataset['author'] = getattr(self, 'author', "Unknown")
            if 'license' not in root_dataset:
                root_dataset['license'] = getattr(self, 'license', "https://creativecommons.org/licenses/by/4.0/")
            if 'isPartOf' not in root_dataset:
                root_dataset['isPartOf'] = []
                
            rocrate = ROCrateV1_2.model_validate(parent_metadata)
            
            f.seek(0)
            f.truncate()
            json.dump(rocrate.model_dump(by_alias=True), f, indent=2)
        
        return subcrate['@id']

    def initCrate(self):
        """Create an ROCrate and initialize ro-crate-metadata.json"""
        ro_crate_metadata_path = self.path / 'ro-crate-metadata.json'
        self.generate_guid()

        # Create root dataset
        root_dataset = {
            "@id": self.guid,
            "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords,
            "hasPart": []
        }

        # Add organization and project if specified
        if self.organizationName:
            organization_guid = f"ark:{NAAN}/organization-{self.organizationName.lower().replace(' ', '-')}-{GenerateDatetimeSquid()}"
            root_dataset['isPartOf'] = [{
                "@id": organization_guid,
            }]

        if self.projectName:
            project_guid = f"ark:{NAAN}/project-{self.projectName.lower().replace(' ', '-')}-{GenerateDatetimeSquid()}"
            if 'isPartOf' not in root_dataset:
                root_dataset['isPartOf'] = []
            root_dataset['isPartOf'].append({
                "@id": project_guid
            })

        # Create metadata descriptor
        metadata_descriptor = {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2-DRAFT"},
            "about": {"@id": self.guid}
        }

        # Create full RO-Crate structure
        rocrate_metadata = {
            "@context": DEFAULT_CONTEXT,
            "@graph": [
                metadata_descriptor,
                root_dataset
            ]
        }

        # Validate the structure
        ROCrateV1_2(**rocrate_metadata)

        # Write to file
        with ro_crate_metadata_path.open(mode="w") as metadata_file:
            json.dump(rocrate_metadata, metadata_file, indent=2)

    def registerObject(self, model: Union[Dataset, Software, Computation]):
        """Add metadata to the graph of an ROCrate"""
        metadata_path = self.path / 'ro-crate-metadata.json'

        with metadata_path.open("r+") as rocrate_metadata_file:
            rocrate_metadata = json.load(rocrate_metadata_file)
            
            # Add to the @graph
            model_data = model.model_dump(by_alias=True, exclude_none=True)
            rocrate_metadata['@graph'].append(model_data)
            
            # Add reference to root dataset's hasPart
            root_dataset = rocrate_metadata['@graph'][1]  # Second element after descriptor
            if 'hasPart' not in root_dataset:
                root_dataset['hasPart'] = []
            root_dataset['hasPart'].append({"@id": model_data["@id"]})

            # Validate updated structure
            ROCrateV1_2(**rocrate_metadata)
            
            # Write back to file
            rocrate_metadata_file.seek(0)
            rocrate_metadata_file.truncate()
            json.dump(rocrate_metadata, rocrate_metadata_file, indent=2)

    def registerDataset(self, dataset: Dataset):
        self.registerObject(dataset)

    def registerSoftware(self, software: Software):
        self.registerObject(software)

    def registerComputation(self, computation: Computation):
        self.registerObject(computation)

def ReadROCrateMetadata(cratePath: pathlib.Path) -> Dict[str, Any]:
    """Read and validate ROCrate metadata"""
    if "ro-crate-metadata.json" in str(cratePath):
        metadata_path = cratePath
    else:
        metadata_path = cratePath / "ro-crate-metadata.json"

    with metadata_path.open("r") as metadata_file:
        crate_metadata = json.load(metadata_file)
        validated_graph = ROCrateV1_2.validate_metadata_graph(crate_metadata)
        return crate_metadata

def AppendCrate(
    cratePath: pathlib.Path,
    elements: List[Union[Dataset, Software, Computation]]
):
    if cratePath.is_dir():
        cratePath = cratePath / 'ro-crate-metadata.json'

    if not elements:
        return None

    with cratePath.open("r+") as rocrate_metadata_file:
        rocrate_metadata = json.load(rocrate_metadata_file)
        
        
        root_dataset = rocrate_metadata['@graph'][1]  # Second element after descriptor
        if 'hasPart' not in root_dataset:
            root_dataset['hasPart'] = []
            
        for element in elements:
            element_data = element.model_dump(by_alias=True, exclude_none=True)
            rocrate_metadata['@graph'].append(element_data)
            root_dataset['hasPart'].append({"@id": element_data["@id"]})
        
        # Validate updated structure
        ROCrateV1_2(**rocrate_metadata)
        
        # Write back to file
        rocrate_metadata_file.seek(0)
        rocrate_metadata_file.truncate()
        json.dump(rocrate_metadata, rocrate_metadata_file, indent=2)


def CopyToROCrate(source_filepath: str, destination_filepath: str):
    if source_filepath == "":
        raise Exception(message="source path is None")

    if destination_filepath == "":
        raise Exception(message="destination path is None") 

    # check if the source file exists 
    source_path = pathlib.Path(source_filepath)
    destination_path = pathlib.Path(destination_filepath)

    if source_path.exists() != True:
        raise Exception(
            message =f"sourcePath: {source_path} Doesn't Exist"
        )

    # TODO check that destination path is in the rocrate

    # copy the file into the destinationPath
    shutil.copy(source_path, destination_path)

def UpdateCrate(
    cratePath: pathlib.Path,
    element: Union[Dataset, Software, Computation]
):
    """Update an existing element in the RO-Crate metadata"""
    if cratePath.is_dir():
        cratePath = cratePath / 'ro-crate-metadata.json'

    with cratePath.open("r+") as rocrate_metadata_file:
        rocrate_metadata = json.load(rocrate_metadata_file)
        
        # Find and replace the element with matching @id
        element_data = element.model_dump(by_alias=True, exclude_none=True)
        for i, existing in enumerate(rocrate_metadata['@graph']):
            if existing.get('@id') == element_data['@id']:
                rocrate_metadata['@graph'][i] = element_data
                break
        
        # Validate updated structure
        ROCrateV1_2(**rocrate_metadata)
        
        # Write back to file
        rocrate_metadata_file.seek(0)
        rocrate_metadata_file.truncate()
        json.dump(rocrate_metadata, rocrate_metadata_file, indent=2)

def LinkSubcrates(parent_crate_path: pathlib.Path) -> List[str]:
    parent_metadata_file = parent_crate_path / 'ro-crate-metadata.json'
    if not parent_metadata_file.is_file():
        raise FileNotFoundError(f"Parent metadata file not found: {parent_metadata_file}")

    with parent_metadata_file.open('r') as f:
        parent_metadata = json.load(f)
    
    parent_root_id = None
    parent_root_dataset = None
    
    for item in parent_metadata.get('@graph', []):
        if item.get('@id') == 'ro-crate-metadata.json' and 'about' in item:
            parent_root_id = item['about'].get('@id')
            break
    
    if parent_root_id:
        for item in parent_metadata.get('@graph', []):
            if item.get('@id') == parent_root_id:
                parent_root_dataset = item
                break
    
    if not parent_root_dataset:
        raise ValueError("Could not determine the root dataset of the parent RO-Crate")

    transferable_fields = [
        "principalInvestigator", "copyrightNotice", 
        "conditionsOfAccess", "contactEmail", "confidentialityLevel",
        "citation", "usageInfo", "additionalProperty",
        "license", "author", "version",
        "rai:dataLimitations", "rai:dataBiases", "rai:dataUseCases",
        "rai:dataReleaseMaintenancePlan", "rai:dataCollection",
        "rai:dataCollectionType", "rai:dataCollectionMissingData",
        "rai:dataCollectionRawData", "rai:dataImputationProtocol",
        "rai:dataManipulationProtocol", "rai:dataPreprocessingProtocol",
        "rai:dataAnnotationProtocol", "rai:dataAnnotationPlatform",
        "rai:dataAnnotationAnalysis", "rai:personalSensitiveInformation",
        "rai:dataSocialImpact", "rai:annotationsPerItem",
        "rai:annotatorDemographics", "rai:machineAnnotationTools",
        "rai:dataCollectionTimeframe"
    ]
    
    transferable_data = {}
    for field in transferable_fields:
        if field in parent_root_dataset:
            value = parent_root_dataset[field]
            if value is None or (isinstance(value, str) and value.strip() == "") or (isinstance(value, list) and len(value) == 0):
                continue
            transferable_data[field] = value
    
    sub_crate_references = []
    linked_sub_crate_ids = []
    
    def find_and_process_subcrates(directory: pathlib.Path, base_path: pathlib.Path):
        for item in directory.iterdir():
            if item.is_dir():
                subcrate_metadata_file = item / 'ro-crate-metadata.json'
                if subcrate_metadata_file.is_file():
                    with subcrate_metadata_file.open('r') as f:
                        subcrate_metadata = json.load(f)
                    
                    subcrate_root_id = None
                    
                    for elem in subcrate_metadata.get('@graph', []):
                        if elem.get('@id') == 'ro-crate-metadata.json' and 'about' in elem:
                            subcrate_root_id = elem['about'].get('@id')
                            break
                    
                    subcrate_root = None
                    if subcrate_root_id:
                        for index, elem in enumerate(subcrate_metadata.get('@graph', [])):
                            if elem.get('@id') == subcrate_root_id:
                                subcrate_root = elem
                                subcrate_root_index = index
                                break
                    
                    if not subcrate_root:
                        print(f"WARNING: Could not find root dataset in subcrate: {item}")
                        find_and_process_subcrates(item, base_path)
                        return
                    
                    modified = False
                    for field, value in transferable_data.items():
                        if field not in subcrate_root or subcrate_root[field] is None or \
                           (isinstance(subcrate_root[field], str) and subcrate_root[field].strip() == "") or \
                           (isinstance(subcrate_root[field], list) and len(subcrate_root[field]) == 0):
                            subcrate_root[field] = value
                            modified = True
                    
                    if 'isPartOf' not in subcrate_root:
                        subcrate_root['isPartOf'] = []
                    
                    parent_ref_exists = any(
                        part.get('@id') == parent_root_id 
                        for part in subcrate_root.get('isPartOf', [])
                    )
                    if not parent_ref_exists:
                        subcrate_root['isPartOf'].append({'@id': parent_root_id})
                        modified = True
                    
                    if modified:
                        subcrate_metadata['@graph'][subcrate_root_index] = subcrate_root
                        with subcrate_metadata_file.open('w') as f:
                            json.dump(subcrate_metadata, f, indent=2)
                    
                    reference_dict = dict(subcrate_root)
                    relative_path = (subcrate_metadata_file.relative_to(base_path)).as_posix()
                    reference_dict['ro-crate-metadata'] = relative_path
                    
                    sub_crate_references.append(reference_dict)
                    linked_sub_crate_ids.append(subcrate_root_id)
                else:
                    find_and_process_subcrates(item, base_path)
    
    find_and_process_subcrates(parent_crate_path, parent_crate_path)
    
    if sub_crate_references:
        parent_root_dataset.setdefault('hasPart', [])
        existing_haspart_ids = {part.get('@id') for part in parent_root_dataset['hasPart']}
        
        existing_graph_ids = {item.get('@id') for item in parent_metadata['@graph']}
        for ref in sub_crate_references:
            if ref['@id'] not in existing_graph_ids:
                parent_metadata['@graph'].append(ref)
        
        for sub_id in linked_sub_crate_ids:
            if sub_id not in existing_haspart_ids:
                parent_root_dataset['hasPart'].append({'@id': sub_id})
        
        with parent_metadata_file.open('w') as f:
            json.dump(parent_metadata, f, indent=2)
    else:
        print("No valid sub-crates found to link.")

    return linked_sub_crate_ids
def collect_subcrate_metadata(parent_crate_path: pathlib.Path) -> dict:
    """
    Collects author and keyword metadata from all subcrates in the parent crate.
    Returns a dictionary with 'authors' (list of unique authors) and 'keywords' (list of unique keywords).
    """
    parent_crate_path = pathlib.Path(parent_crate_path)
    authors = set()
    keywords = set()
    processed_files = set()
    
    def process_directory(directory):
        for path in directory.glob('**/ro-crate-metadata.json'):
            if path.is_file() and str(path) not in processed_files:
                processed_files.add(str(path))
                
                try:
                    subcrate_metadata = ReadROCrateMetadata(path)
                    root_dataset = None
                    if '@graph' in subcrate_metadata and len(subcrate_metadata['@graph']) > 1:
                        root_dataset = subcrate_metadata['@graph'][1]
                    
                    
                    if root_dataset:
                        if root_dataset.author:
                            author_value = root_dataset.author
                            if isinstance(author_value, str):
                                for author in [a.strip() for a in author_value.split(',')]:
                                    if author:
                                        authors.add(author)
                            elif isinstance(author_value, tuple) or isinstance(author_value, list):
                                for author in author_value:
                                    if isinstance(author, str):
                                        authors.add(author)
                        
                        if root_dataset.keywords:
                            keyword_values = root_dataset.keywords
                            if isinstance(keyword_values, list) or isinstance(keyword_values, tuple):
                                for keyword in keyword_values:
                                    if keyword:
                                        keywords.add(keyword)
                            elif isinstance(keyword_values, str):
                                for keyword in [k.strip() for k in keyword_values.split(',')]:
                                    if keyword:
                                        keywords.add(keyword)
                except Exception as e:
                    print(f"Error reading subcrate metadata {path}: {e}")
                    continue
    for dir_item in parent_crate_path.iterdir():
        if dir_item.is_dir():
            process_directory(dir_item)
    return {
        'authors': sorted(list(authors)),
        'keywords': sorted(list(keywords))
    }


@dataclass
class AggregatedMetrics:
    """
    Aggregated metrics from all sub-crates for AI-Ready scoring.

    This class accumulates entity counts, statistics, checksums, formats,
    and schema references from all sub-crates in a release to enable
    efficient AI-Ready score calculation without recursive file reads.
    """

    # Entity counts (for provenance scoring)
    dataset_count: int = 0
    computation_count: int = 0
    software_count: int = 0
    schema_count: int = 0

    # Statistics (for characterization scoring)
    total_content_size_bytes: int = 0
    entities_with_summary_stats: int = 0

    # Verification (for pre-model explainability)
    entities_with_checksums: int = 0
    total_entities: int = 0

    # Computability
    formats: Set[str] = field(default_factory=set)

    # Standards
    schemas: List[Dict[str, str]] = field(default_factory=list)


def _extract_content_size_bytes(size_str: str) -> int:
    """
    Extract content size in bytes from a size string.

    Args:
        size_str: Size string like "125.5 GB" or "1.2 TB"

    Returns:
        Size in bytes as integer, or 0 if parsing fails
    """
    if not size_str or not isinstance(size_str, str):
        return 0

    try:
        size_str = size_str.strip().upper()
        if "TB" in size_str:
            return int(float(size_str.replace("TB", "").strip()) * 1e12)
        elif "GB" in size_str:
            return int(float(size_str.replace("GB", "").strip()) * 1e9)
        elif "MB" in size_str:
            return int(float(size_str.replace("MB", "").strip()) * 1e6)
        elif "KB" in size_str:
            return int(float(size_str.replace("KB", "").strip()) * 1e3)
        else:
            # Assume bytes if no unit
            return int(float(size_str))
    except (ValueError, AttributeError):
        return 0


def _is_schema_entity(entity_type: Union[str, List[str]]) -> bool:
    """
    Check if an entity type indicates a Schema.

    Args:
        entity_type: @type value (string or list)

    Returns:
        True if entity is a Schema
    """
    if isinstance(entity_type, str):
        return "Schema" in entity_type or "evi:Schema" in entity_type
    elif isinstance(entity_type, list):
        return any("Schema" in t or "evi:Schema" in t for t in entity_type)
    return False


def _extract_checksum(entity: Dict[str, Any]) -> Optional[str]:
    """
    Extract checksum from an entity.

    Args:
        entity: Entity dictionary from RO-Crate @graph

    Returns:
        Checksum string (e.g., "md5:abc123...") or None
    """
    # Check common checksum fields
    md5 = entity.get("md5") or entity.get("MD5")
    if md5:
        if md5.startswith("md5:"):
            return md5
        else:
            return f"md5:{md5}"

    sha256 = entity.get("sha256") or entity.get("SHA256")
    if sha256:
        if sha256.startswith("sha256:"):
            return sha256
        else:
            return f"sha256:{sha256}"

    return None


def _get_entity_type(entity: Dict[str, Any]) -> str:
    """
    Get type from entity's @type or metadataType field.

    Args:
        entity: Entity dictionary from RO-Crate @graph

    Returns:
        Type string (last item if list), or empty string
    """
    type_val = entity.get("@type") or entity.get("metadataType") or []
    if isinstance(type_val, str):
        return type_val
    elif isinstance(type_val, list) and type_val:
        return type_val[-1]
    return ""


def collect_subcrate_aggregated_metrics(
    parent_crate_path: pathlib.Path
) -> AggregatedMetrics:
    """
    Collect aggregated metrics from all subcrates for AI-Ready scoring.

    This function traverses all sub-crates in a release directory and
    aggregates entity counts, statistics, checksums, formats, and schemas.
    These aggregated metrics are added to the release-level RO-Crate to
    enable efficient AI-Ready score calculation without requiring recursive
    file system reads during scoring.

    Args:
        parent_crate_path: Path to the release directory containing sub-crates

    Returns:
        AggregatedMetrics object with all roll-up properties
    """
    parent_crate_path = pathlib.Path(parent_crate_path)
    metrics = AggregatedMetrics()
    processed_files = set()

    def process_directory(directory: pathlib.Path):
        """Recursively process directories to find and aggregate subcrate metadata."""
        for path in directory.glob('**/ro-crate-metadata.json'):
            if path.is_file() and str(path) not in processed_files:
                processed_files.add(str(path))

                try:
                    # Load and validate the subcrate
                    subcrate_metadata = ReadROCrateMetadata(path)
                    graph = subcrate_metadata.get('@graph', [])

                    for entity in graph:
                        if not isinstance(entity, dict):
                            continue

                        if entity.get('@id') == 'ro-crate-metadata.json':
                            continue

                        entity_type = _get_entity_type(entity)

                        if "Dataset" in entity_type:
                            metrics.dataset_count += 1
                            metrics.total_entities += 1

                        elif "Computation" in entity_type or "Experiment" in entity_type:
                            metrics.computation_count += 1
                            metrics.total_entities += 1

                        elif "Software" in entity_type:
                            metrics.software_count += 1
                            metrics.total_entities += 1

                        elif _is_schema_entity(entity_type):
                            metrics.schema_count += 1
                            schema_id = entity.get('@id')
                            if schema_id:
                                metrics.schemas.append({"@id": schema_id})

                        content_size = entity.get("contentSize")
                        if content_size:
                            size_bytes = _extract_content_size_bytes(content_size)
                            if size_bytes > 0:
                                metrics.total_content_size_bytes += size_bytes

                        if entity.get("hasSummaryStatistics"):
                            metrics.entities_with_summary_stats += 1

                        checksum = _extract_checksum(entity)
                        if checksum:
                            metrics.entities_with_checksums += 1

                        format_val = entity.get("format") or entity.get("encodingFormat")
                        if format_val:
                            if isinstance(format_val, str):
                                metrics.formats.add(format_val)
                            elif isinstance(format_val, list):
                                for fmt in format_val:
                                    if isinstance(fmt, str):
                                        metrics.formats.add(fmt)

                except Exception:
                    continue

    for dir_item in parent_crate_path.iterdir():
        if dir_item.is_dir():
            process_directory(dir_item)

    return metrics


################################
#
# Mongomock update tests
#
#################################

def _transform_entities_for_mongo(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforms RO-Crate entities for MongoDB compatibility (adds _id)."""
    transformed = []
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        mongo_entity = entity.copy()
        mongo_entity['_id'] = entity.get('@id', str(uuid.uuid4()))
        transformed.append(mongo_entity)
    return transformed

def _transform_entities_from_mongo(mongo_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforms entities back from MongoDB representation (removes temporary _id if needed)."""
    original_entities = []
    for mongo_entity in mongo_entities:
        original_entity = mongo_entity.copy()
        if '_id' in original_entity and original_entity.get('@id'):
            del original_entity['_id']
        original_entities.append(original_entity)
    return original_entities

def UpdateEntitiesInGraph(
    cratePath: pathlib.Path,
    query_dict: Dict[str, Any],
    update_dict: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Updates entities in the RO-Crate's @graph using MongoDB-like operations.

    Args:
        cratePath: Path to the RO-Crate directory or ro-crate-metadata.json file.
        query_dict: A MongoDB-style query dictionary to select entities.
        update_dict: A MongoDB-style update dictionary defining modifications.

    Returns:
        A tuple (success_status, message_string).
    """
    try:
        if cratePath.is_dir():
            metadata_filepath = cratePath / 'ro-crate-metadata.json'
        else:
            metadata_filepath = cratePath

        crate_data = ReadROCrateMetadata(metadata_filepath)
        original_graph_entities = [entity.model_dump(by_alias=True) for entity in crate_data.get('@graph', [])]

        if not original_graph_entities:
            return True, "RO-Crate @graph is empty. No entities to update."

        collection = mongomock.MongoClient().db.collection

        entities_for_mongo = _transform_entities_for_mongo(original_graph_entities)
        
        if entities_for_mongo:
            try:
                collection.insert_many(entities_for_mongo, ordered=False)
            except Exception as e: 
                print(f"Warning: mongomock bulk insert failed during update: {e}. This might indicate issues with source data like non-unique @ids.")
                return False, f"MongoDB-style operation failed: {e}"
            

        try:
            result = collection.update_many(query_dict, update_dict)
            modified_count = result.modified_count
            matched_count = result.matched_count
        except Exception as e:
            return False, f"MongoDB-style operation failed: {e}"

        if modified_count == 0:
            return True, f"No entities were modified. Matched: {matched_count}, Modified: {modified_count}."

        updated_mongo_entities = list(collection.find({}))

        final_graph_entities = _transform_entities_from_mongo(updated_mongo_entities)
        crate_data['@graph'] = final_graph_entities
        
        try:
            validated_crate = ROCrateV1_2.model_validate(crate_data)
        except Exception as e:
            return False, f"RO-Crate became invalid after update operations. Details: {e}"

        with metadata_filepath.open(mode="w") as metadataFile:
            json.dump(validated_crate.model_dump(by_alias=True), metadataFile, indent=2, ensure_ascii=False)

        return True, f"Successfully processed entities. Matched: {matched_count}, Modified: {modified_count}."
    
    except Exception as e:
        import traceback
        print(f"DEBUG: Unexpected error in UpdateEntitiesInGraph: {traceback.format_exc()}")
        return False, f"An unexpected error occurred: {type(e).__name__} - {e}"
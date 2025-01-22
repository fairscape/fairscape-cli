import pathlib
import shutil
import json
from typing import Optional, Union, List, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

from fairscape_cli.config import NAAN, DEFAULT_CONTEXT
from fairscape_cli.models.software import Software
from fairscape_cli.models.dataset import Dataset
from fairscape_cli.models.computation import Computation
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid

class ROCrateMetadataDescriptor(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(default="ro-crate-metadata.json", alias="@id")
    type: Literal["CreativeWork"] = Field(alias="@type")
    conformsTo: Dict = Field(default={
        "@id": "https://w3id.org/ro/crate/1.2-DRAFT"
    })
    about: Dict[str, str]

class ROCrateMetadata(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid'
    )
    
    context: Dict[str, str] = Field(
        default={
            "EVI": "https://w3id.org/EVI#",
            "@vocab": "https://schema.org/"
        },
        alias="@context"
    )
    graph: List[Dict] = Field(alias="@graph")

    @model_validator(mode='after')
    def validate_metadata(self) -> 'ROCrateMetadata':
        self.validate_metadata_descriptor()
        self.validate_graph_elements()
        return self

    def validate_metadata_descriptor(self):
        # Check for metadata descriptor
        descriptors = [item for item in self.graph 
                      if item.get("@id") == "ro-crate-metadata.json"]
        if not descriptors:
            raise ValueError("Missing required metadata descriptor in @graph")
        
        descriptor = descriptors[0]
        # Validate descriptor
        ROCrateMetadataDescriptor(**descriptor)
        
        # Validate about reference exists in graph
        about_id = descriptor.get("about", {}).get("@id")
        if not about_id:
            raise ValueError("Metadata descriptor missing root node in about.@id")
            
        # Check root exists
        root_items = [item for item in self.graph if item.get("@id") == about_id]
        if not root_items:
            raise ValueError(f"Root id {about_id} referenced in about.@id not found in @graph")

    def validate_graph_elements(self):
        """Validate each element in @graph is flat and has an id"""
        for item in self.graph:
            if "@id" not in item or "@type" not in item:
                raise ValueError("All @graph elements must have @id and @type properties")
                
            # Validate nested objects only contain @id
            for key, value in item.items():
                if isinstance(value, dict):
                    allowed_keys = {"@id"}
                    if set(value.keys()) - allowed_keys:
                        raise ValueError(f"Nested object under '{key}' can only contain '@id' property")

def GenerateROCrate(
    path: pathlib.Path,
    guid: str,
    name: str,
    description: str,
    keywords: List[str],
    organizationName: str = None,
    projectName: str = None,
    ):
        
    # Generate GUID if not provided
    sq = GenerateDatetimeSquid()
    guid = f"ark:{NAAN}/rocrate-{name.lower().replace(' ', '-')}-{sq}"

    # Create root dataset entity
    root_dataset = {
        "@id": guid,
        "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
        "name": name,
        "keywords": keywords,
        "description": description,
        "hasPart": []
    }

    if 'isPartOf' not in root_dataset:
        root_dataset['isPartOf'] = []
    
    if organizationName:
        organization_guid = f"ark:{NAAN}/organization-{organizationName.lower().replace(' ', '-')}-{GenerateDatetimeSquid()}"
        root_dataset['isPartOf'] = [{
            "@id": organization_guid
        }]

    if projectName:
        project_guid = f"ark:{NAAN}/project-{projectName.lower().replace(' ', '-')}-{GenerateDatetimeSquid()}"

        root_dataset['isPartOf'].append({
            "@id": project_guid
        })

    metadata_descriptor = {
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2-DRAFT"},
        "about": {"@id": guid}
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
    ROCrateMetadata(**rocrate_metadata)
    
    # Write to file
    if 'ro-crate-metadata.json' in str(path):
        roCrateMetadataPath = path
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
    else:
        roCrateMetadataPath = path / 'ro-crate-metadata.json'
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

    with roCrateMetadataPath.open(mode="w") as metadataFile:
        json.dump(rocrate_metadata, metadataFile, indent=2)

    return rocrate_metadata["@graph"][1]

class ROCrate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    guid: Optional[str] = Field(alias="@id", default=None)
    name: str = Field(max_length=200)
    description: str = Field(min_length=5)
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
        ROCrateMetadata(**rocrate_metadata)

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
            ROCrateMetadata(**rocrate_metadata)
            
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
        # Validate the structure
        ROCrateMetadata(**crate_metadata)
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
        
        # Add elements to @graph and references to root dataset
        root_dataset = rocrate_metadata['@graph'][1]  # Second element after descriptor
        if 'hasPart' not in root_dataset:
            root_dataset['hasPart'] = []
            
        for element in elements:
            element_data = element.model_dump(by_alias=True, exclude_none=True)
            rocrate_metadata['@graph'].append(element_data)
            root_dataset['hasPart'].append({"@id": element_data["@id"]})
        
        # Validate updated structure
        ROCrateMetadata(**rocrate_metadata)
        
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
        ROCrateMetadata(**rocrate_metadata)
        
        # Write back to file
        rocrate_metadata_file.seek(0)
        rocrate_metadata_file.truncate()
        json.dump(rocrate_metadata, rocrate_metadata_file, indent=2)
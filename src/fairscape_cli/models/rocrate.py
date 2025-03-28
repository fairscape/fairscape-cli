import pathlib
import shutil
import json
from datetime import datetime
from typing import Optional, Union, List, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

from fairscape_cli.config import NAAN, DEFAULT_CONTEXT
from fairscape_cli.models.software import Software
from fairscape_cli.models.dataset import Dataset
from fairscape_cli.models.computation import Computation
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid

from datetime import datetime
import pathlib
import json
from typing import List, Optional, Dict, Any

from fairscape_cli.config import NAAN, DEFAULT_CONTEXT
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
from fairscape_models.rocrate import ROCrateV1_2, ROCrateMetadataElem, ROCrateMetadataFileElem

def GenerateROCrate(
   path: pathlib.Path,
   guid: str,
   name: str, 
   **kwargs
):
   if not guid:
       sq = GenerateDatetimeSquid()
       guid = f"ark:{NAAN}/rocrate-{name.lower().replace(' ', '-')}-{sq}/"

   metadata_descriptor = ROCrateMetadataFileElem.model_validate({
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2-DRAFT"},
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
            self.guid = f"ark:{NAAN}/rocrate-{self.name.replace(' ', '-').lower()}-{sq}/"
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
        # Validate the structure
        ROCrateV1_2(**crate_metadata)
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
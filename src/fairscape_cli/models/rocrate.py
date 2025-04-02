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

def LinkSubcrates(parent_crate_path: pathlib.Path) -> List[str]:
    parent_metadata_file = parent_crate_path / 'ro-crate-metadata.json'
    if not parent_metadata_file.is_file():
        raise FileNotFoundError(f"Parent metadata file not found: {parent_metadata_file}")

    parent_metadata_dict = ReadROCrateMetadata(parent_metadata_file)
    
    #find root node sometimes its a dict other times pydantic object?
    parent_root_id = None
    for elem in parent_metadata_dict.get('@graph', []):
        if hasattr(elem, '__class__') and elem.__class__.__name__ == 'ROCrateMetadataFileElem':
            if hasattr(elem, 'about') and elem.about:
                target_id = elem.about.guid if hasattr(elem.about, 'guid') else elem.about.get('@id', '')
                if target_id:
                    for graph_item in parent_metadata_dict.get('@graph', []):
                        if (hasattr(graph_item, 'guid') and graph_item.guid == target_id) or \
                           (isinstance(graph_item, dict) and graph_item.get('@id') == target_id):
                            parent_root_id = target_id
                            break
        elif isinstance(elem, dict) and elem.get('@type') == 'CreativeWork' and 'about' in elem:
            target_id = elem.get('about', {}).get('@id')
            if target_id:
                for graph_item in parent_metadata_dict.get('@graph', []):
                    if isinstance(graph_item, dict) and graph_item.get('@id') == target_id:
                        parent_root_id = target_id
                        break
    
    if not parent_root_id:
        raise ValueError("Could not determine the @id of the parent RO-Crate's root dataset.")

    sub_crate_references = []
    linked_sub_crate_ids = []
    processed_subdirs = set()

    #find all subcrates
    for dir_item in parent_crate_path.iterdir():
        if dir_item.is_dir() and dir_item.name not in processed_subdirs:
            subcrate_metadata_file = dir_item / 'ro-crate-metadata.json'
            if subcrate_metadata_file.is_file():
                processed_subdirs.add(dir_item.name)
                subcrate_metadata_dict = ReadROCrateMetadata(subcrate_metadata_file)
                
                subcrate_root = None
                
                for elem in subcrate_metadata_dict.get('@graph', []):
                    if hasattr(elem, '__class__') and elem.__class__.__name__ == 'ROCrateMetadataFileElem':
                        if hasattr(elem, 'about') and elem.about:
                            target_id = elem.about.guid if hasattr(elem.about, 'guid') else elem.about.get('@id', '')
                            if target_id:
                                for graph_item in subcrate_metadata_dict.get('@graph', []):
                                    if (hasattr(graph_item, 'guid') and graph_item.guid == target_id) or \
                                       (isinstance(graph_item, dict) and graph_item.get('@id') == target_id):
                                        subcrate_root = graph_item
                                        break
                    elif isinstance(elem, dict) and elem.get('@type') == 'CreativeWork' and 'about' in elem:
                        target_id = elem.get('about', {}).get('@id')
                        if target_id:
                            for graph_item in subcrate_metadata_dict.get('@graph', []):
                                if isinstance(graph_item, dict) and graph_item.get('@id') == target_id:
                                    subcrate_root = graph_item
                                    break

                if not subcrate_root:
                    continue

                relative_path = (dir_item.relative_to(parent_crate_path) / 'ro-crate-metadata.json').as_posix()
                
                if hasattr(subcrate_root, 'model_dump'):
                    reference_dict = subcrate_root.model_dump(by_alias=True, exclude_none=True)
                elif hasattr(subcrate_root, 'dict'):
                    reference_dict = subcrate_root.dict(by_alias=True, exclude_none=True)
                else:
                    reference_dict = dict(subcrate_root)
                
                reference_dict['ro-crate-metadata'] = relative_path

                sub_crate_references.append(reference_dict)
                linked_sub_crate_ids.append(reference_dict.get('@id'))
                
    #add links
    if sub_crate_references:
        with parent_metadata_file.open("r+") as f:
            parent_metadata_dict = json.load(f)

            parent_root_dataset_dict = None
            for elem in parent_metadata_dict.get('@graph', []):
                if elem.get('@id') == parent_root_id:
                    parent_root_dataset_dict = elem
                    break

            if not parent_root_dataset_dict:
                raise ValueError("Could not re-find parent root dataset in metadata file during update.")

            existing_graph_ids = {elem.get('@id') for elem in parent_metadata_dict['@graph']}
            for ref in sub_crate_references:
                if ref['@id'] not in existing_graph_ids:
                    parent_metadata_dict['@graph'].append(ref)

            parent_root_dataset_dict.setdefault('hasPart', [])
            existing_haspart_ids = {part.get('@id') for part in parent_root_dataset_dict['hasPart'] if isinstance(part, dict)}
            for sub_id in linked_sub_crate_ids:
                if sub_id not in existing_haspart_ids:
                    parent_root_dataset_dict['hasPart'].append({'@id': sub_id})

            f.seek(0)
            f.truncate()
            json.dump(parent_metadata_dict, f, indent=2, ensure_ascii=False)
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
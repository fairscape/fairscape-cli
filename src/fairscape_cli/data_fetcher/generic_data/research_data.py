# fairscape_cli/data_fetcher/generic_data/research_data.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union, Any
import json
import pathlib
from datetime import datetime
import os

from fairscape_cli.models.rocrate import GenerateROCrate, AppendCrate
from fairscape_cli.models.dataset import GenerateDataset
from fairscape_cli.models.software import GenerateSoftware

class ResearchData(BaseModel):
    repository_name: str
    project_id: str 
    title: str
    description: str
    authors: List[str]
    license: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    publication_date: Optional[str] = None 
    doi: Optional[str] = None
    files: List[Dict[str, Any]] = Field(default_factory=list)
    software: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_rocrate(self, output_dir: str, **kwargs) -> str:
        output_path = pathlib.Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        crate_version_cli = kwargs.get('crate_version', "1.0")
        organization_name_cli = kwargs.get('organization_name')
        project_name_cli = kwargs.get('project_name')

        rocrate_root_kwargs = self.metadata.copy()

        rocrate_root_kwargs.update({
            "guid": "",
            "name": self.title,
            "description": self.description,
            "keywords": self.keywords,
            "license": self.license or "https://creativecommons.org/licenses/by/4.0/",
            "author": self.authors,
            "datePublished": self.publication_date or datetime.now().isoformat(),
            "associatedPublication": self.doi or "",
            "version": crate_version_cli, 
            "isPartOf": [],
        })

        if organization_name_cli:
            rocrate_root_kwargs['organizationName'] = organization_name_cli
        if project_name_cli:
            rocrate_root_kwargs['projectName'] = project_name_cli
        
        rocrate_root_dataset = GenerateROCrate(
            path=output_path,
            **rocrate_root_kwargs 
        )
        
        elements_to_append = []
        
        for file_info in self.files:
            file_format = file_info.get("format", "")
            if not file_format and "name" in file_info:   
                ext = os.path.splitext(file_info["name"])[1].lstrip(".")
                file_format = ext or "unknown"
            
            file_description = file_info.get("description")
            if not file_description or file_description.strip() == "":
                file_description = f"File '{file_info.get('name', 'Unnamed file')}' part of dataset '{self.title}'"

            dataset_params = {
                "guid": None,
                "url": file_info.get("url"), 
                "author": self.authors,
                "name": file_info.get("name", "Unnamed file"),
                "description": file_description,
                "keywords": self.keywords,
                "datePublished": file_info.get("datePublished", self.publication_date or datetime.now().isoformat()),
                "version": file_info.get("version", "1.0"), 
                "associatedPublication": self.doi or None,
                "additionalDocumentation": None, 
                "format": file_format,
                "schema": "", 
                "derivedFrom": [],
                "usedBy": [],
                "generatedBy": [],
                "filepath": None, 
                "contentUrl": file_info.get("contentUrl", file_info.get("url", "")), 
                "cratePath": output_path 
            }
            if file_info.get("md5"):
                dataset_params["md5"] = file_info["md5"]
            
            dataset = GenerateDataset(**dataset_params)
            elements_to_append.append(dataset)
            
        for software_info in self.software:
            software_version = software_info.get("version", "0.1.0") 
            
            software_description = software_info.get("description")
            if not software_description or software_description.strip() == "":
                software_description = f"Software '{software_info.get('name', 'Unnamed software')}' used/from dataset '{self.title}'"

            software_author = self.authors[0] if self.authors else "Unknown"

            software_item = GenerateSoftware(
                guid=None, 
                name=software_info.get("name", "Unnamed software"),
                author=software_author,
                dateModified=software_info.get("dateModified", datetime.now().isoformat()),
                version=software_version,
                description=software_description,
                associatedPublication=self.doi or None,
                additionalDocumentation=software_info.get("documentation_url", None),
                format=software_info.get("format", "application/zip"), 
                usedByComputation=[],
                contentUrl=software_info.get("contentUrl", software_info.get("url", "")) 
            )
            elements_to_append.append(software_item)
        
        if elements_to_append:
            AppendCrate(output_path / "ro-crate-metadata.json", elements_to_append)
        
        return rocrate_root_dataset["@id"] 
    
    @classmethod
    def from_repository(cls, repository_type: str, identifier: str, **kwargs) -> 'ResearchData':
        if repository_type.lower() == 'figshare':
            from fairscape_cli.data_fetcher.generic_data.connectors.figshare_connector import FigshareConnector
            connector = FigshareConnector(token=kwargs.get('token'))
            return connector.fetch_data(identifier, include_files=kwargs.get('include_files', True))
        elif repository_type.lower() == 'dataverse':
            from fairscape_cli.data_fetcher.generic_data.connectors.dataverse_connector import DataverseConnector
            connector = DataverseConnector(
                server_url=kwargs.get('server_url', 'https://dataverse.harvard.edu'),
                api_token=kwargs.get('token')
            )
            return connector.fetch_data(identifier, include_files=kwargs.get('include_files', True))
        else:
            raise ValueError(f"Unsupported repository type: {repository_type}")

    def add_to_existing_rocrate(self, rocrate_path: str) -> str:
        rocrate_dir_path = pathlib.Path(rocrate_path)
        metadata_file_path = rocrate_dir_path / "ro-crate-metadata.json"
        
        if not metadata_file_path.exists():
            raise ValueError(f"No RO-Crate metadata found at {rocrate_dir_path}")
        
        dataset_objs_to_append = []
        
        for file_info in self.files:
            file_format = file_info.get("format", "")
            if not file_format and "name" in file_info:
                ext = os.path.splitext(file_info["name"])[1].lstrip(".")
                file_format = ext or "unknown"
            
            file_description = file_info.get("description", f"File from {self.repository_name} titled '{self.title}'")
            if not file_description or file_description.strip() == "":
                 file_description = f"File '{file_info.get('name', 'Unnamed file')}' from {self.repository_name} dataset '{self.title}'"

            dataset_params = {
                "guid": None, 
                "url": file_info.get("url"), 
                "author": self.authors,
                "name": file_info.get("name", "Unnamed file"),
                "description": file_description,
                "keywords": self.keywords,
                "datePublished": file_info.get("uploaded_date", self.publication_date or datetime.now().isoformat()),
                "version": "1.0", 
                "associatedPublication": self.doi or None,
                "additionalDocumentation": None,
                "format": file_format,
                "EVI:Schema": "",
                "derivedFrom": [],
                "usedBy": [],
                "generatedBy": [],
                "filepath": None, 
                "contentUrl": file_info.get("download_url", file_info.get("url", "")),
                "cratePath": rocrate_dir_path 
            }
            if file_info.get("md5"): # Add md5 if present
                dataset_params["md5"] = file_info["md5"]
            if file_info.get("contentSize"):
                dataset_params["contentSize"] = file_info["contentSize"]
            
            dataset = GenerateDataset(**dataset_params)
            dataset_objs_to_append.append(dataset)
        
        if dataset_objs_to_append:
            AppendCrate(metadata_file_path, dataset_objs_to_append)
        
        with open(metadata_file_path, 'r') as f:
            crate_data = json.load(f)
            root_id = None
            for entity in crate_data.get("@graph", []):
                if entity.get("@id") == "ro-crate-metadata.json" and "about" in entity:
                    root_id = entity["about"]["@id"]
                    break
            if not root_id: 
                 if len(crate_data.get("@graph", [])) > 1 and crate_data["@graph"][1].get("@type") and \
                    ("Dataset" in crate_data["@graph"][1]["@type"] or "ROCrate" in crate_data["@graph"][1]["@type"]):
                    root_id = crate_data["@graph"][1]["@id"]
            
            if not root_id:
                raise ValueError("Could not determine the root dataset ID of the RO-Crate.")
        
        return root_id
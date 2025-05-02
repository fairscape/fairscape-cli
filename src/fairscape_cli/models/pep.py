import os
import pathlib
import yaml
from typing import List, Dict, Optional, Union, Any
from datetime import datetime

from fairscape_cli.models import (
    GenerateROCrate,
    GenerateDataset,
    AppendCrate,
    CopyToROCrate
)
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
from fairscape_cli.models.schema.tabular import TabularValidationSchema
from fairscape_cli.config import NAAN


class PEPtoROCrateMapper:
    
    def __init__(self, pep_path: Union[str, pathlib.Path]):
        self.pep_path = pathlib.Path(pep_path)
        
        if self.pep_path.is_dir():
            yaml_files = list(self.pep_path.glob("*.yaml")) + list(self.pep_path.glob("*.yml"))
            
            if not yaml_files:
                raise FileNotFoundError(f"No YAML files found in {self.pep_path}")
            
            config_files = [f for f in yaml_files if "config" in f.name.lower()]
            
            if config_files:
                self.config_path = config_files[0]
            else:
                self.config_path = yaml_files[0]
            self.config = self._load_yaml(self.config_path)
        else:
            raise FileNotFoundError(f"PEP path {self.pep_path} is not a directory")
        
        if "pep_version" not in self.config:
            raise ValueError("Invalid PEP configuration: missing pep_version")
    
    def _load_yaml(self, path: pathlib.Path) -> Dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    
    def _resolve_path(self, path_str: str) -> pathlib.Path:
        path = pathlib.Path(path_str)
        if path.is_absolute():
            return path
        return self.pep_path / path
    
    def _extract_metadata_from_pep(self) -> Dict[str, Any]:
        metadata = {}
        
        if "name" in self.config:
            metadata["name"] = self.config["name"]
        elif "project_name" in self.config:
            metadata["name"] = self.config["project_name"]
        
        if 'descrtion' not in metadata and "description" in self.config:
            metadata["description"] = self.config["description"]
        
        if "experiment_metadata" in self.config:
            exp_meta = self.config["experiment_metadata"]
            
            if "series_title" in exp_meta:
                metadata["name"] = exp_meta["series_title"]
            
            if "series_summary" in exp_meta:
                metadata["description"] = exp_meta["series_summary"]
            
            if "series_contributor" in exp_meta and 'author' not in metadata:
                metadata["author"] = exp_meta["series_contributor"]
            
            if "author" not in metadata and "series_contact_name" in exp_meta:
                metadata["author"] = exp_meta["series_contact_name"]
            
            if "series_submission_date" in exp_meta:
                metadata["datePublished"] = exp_meta["series_submission_date"]
            elif "series_last_update_date" in exp_meta:
                metadata["datePublished"] = exp_meta["series_last_update_date"]
        
        return metadata
    
    def create_rocrate(self, 
                      output_path: Optional[Union[str, pathlib.Path]] = None,
                      name: Optional[str] = None,
                      description: Optional[str] = None,
                      author: Optional[str] = None,
                      organization_name: Optional[str] = None,
                      project_name: Optional[str] = None,
                      keywords: Optional[List[str]] = None,
                      license: Optional[str] = None,
                      date_published: Optional[str] = None,
                      version: str = "1.0") -> str:
        if output_path is None:
            output_path = self.pep_path
        else:
            output_path = pathlib.Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
        
        pep_metadata = self._extract_metadata_from_pep()
        
        final_metadata = {
            "name": name or pep_metadata.get("name"),
            "description": description or pep_metadata.get("description"),
            "author": author or pep_metadata.get("author"),
            "keywords": keywords or pep_metadata.get("keywords", []),
            "datePublished": date_published or pep_metadata.get("datePublished", datetime.now().isoformat()),
            "license": license or "https://creativecommons.org/licenses/by/4.0/",
            "version": version
        }
        
        required_fields = ["name", "description", "author"]
        missing_fields = [field for field in required_fields if not final_metadata.get(field)]
        
        if missing_fields:
            raise ValueError(
                f"Missing required metadata: {', '.join(missing_fields)}. "
                "Please provide these values as arguments or ensure they are in the PEP config."
            )
        
        if not final_metadata["keywords"]:
            final_metadata["keywords"] = ["pep", final_metadata["name"]]
        
        crate = GenerateROCrate(
            path=output_path,
            guid="",
            name=final_metadata["name"],
            description=final_metadata["description"],
            keywords=final_metadata["keywords"],
            organizationName=organization_name,
            projectName=project_name or self.config.get("name"),
            license=final_metadata["license"],
            datePublished=final_metadata["datePublished"]
        )
        
        rocrate_id = crate["@id"]
        
        if "sample_table" in self.config:
            self._add_sample_path_to_rocrate(output_path, rocrate_id, final_metadata)
        
        if "subsample_table" in self.config:
            self._add_subsample_paths_to_rocrate(output_path, rocrate_id, final_metadata)
        
        return rocrate_id
    
    def _add_sample_path_to_rocrate(self, 
                                  output_path: pathlib.Path, 
                                  rocrate_id: str, 
                                  metadata: Dict[str, Any]) -> None:
        source_path = self._resolve_path(self.config["sample_table"])
        
        rel_path = os.path.basename(source_path)
        
        dataset_name = f"Samples Data: {rel_path}"
        sq_dataset = GenerateDatetimeSquid()
        dataset_guid = f"ark:{NAAN}/dataset-samples-{sq_dataset}"
        
        schema = None
        try:
            schema = TabularValidationSchema.infer_from_file(
                str(source_path),
                f"Schema for {dataset_name}",
                f"Automatically inferred schema for {dataset_name}"
            )
            AppendCrate(output_path, [schema])
        except Exception as e:
            print(f"Warning: Could not infer schema for {source_path}: {str(e)}")
        
        dataset = GenerateDataset(
            guid=dataset_guid,
            name=dataset_name,
            description=f"Sample table from PEP project: {metadata['name']}",
            author=metadata["author"],
            keywords=metadata["keywords"],
            datePublished=metadata["datePublished"],
            version=metadata.get("version", "1.0"),
            dataFormat="csv",
            filepath=str(source_path),
            cratePath=output_path,
            url="",
            associatedPublication="",
            additionalDocumentation="",
            schema=schema.guid if schema else "",
            derivedFrom=[],
            usedBy=[],
            generatedBy=[]
        )
        
        AppendCrate(output_path, [dataset])
    
    def _add_subsample_paths_to_rocrate(self, 
                                     output_path: pathlib.Path, 
                                     rocrate_id: str, 
                                     metadata: Dict[str, Any]) -> None:
        subsample_tables = self.config["subsample_table"]
        
        if isinstance(subsample_tables, list):
            for index, table_path in enumerate(subsample_tables):
                self._register_subsample_path(output_path, rocrate_id, metadata, table_path, index)
        else:
            self._register_subsample_path(output_path, rocrate_id, metadata, subsample_tables, 0)
    
    def _register_subsample_path(self,
                               output_path: pathlib.Path,
                               rocrate_id: str,
                               metadata: Dict[str, Any],
                               table_path: str,
                               index: int) -> None:
        source_path = self._resolve_path(table_path)
        
        rel_path = os.path.basename(source_path)
        
        dataset_name = f"Subsamples Data {index+1}: {rel_path}"
        sq_dataset = GenerateDatetimeSquid()
        dataset_guid = f"ark:{NAAN}/dataset-subsamples-{index}-{sq_dataset}"
        
        schema = None
        try:
            schema = TabularValidationSchema.infer_from_file(
                str(source_path),
                f"Schema for {dataset_name}",
                f"Automatically inferred schema for {dataset_name}"
            )
        except Exception as e:
            print(f"Warning: Could not infer schema for {source_path}: {str(e)}")
        
        dataset = GenerateDataset(
            guid=dataset_guid,
            name=dataset_name,
            description=f"Subsample table from PEP project: {metadata['name']}",
            author=metadata["author"],
            keywords=metadata["keywords"],
            datePublished=metadata["datePublished"],
            version=metadata.get("version", "1.0"),
            dataFormat="csv",
            filepath=str(source_path),
            cratePath=output_path,
            url="",
            associatedPublication="",
            additionalDocumentation="",
            schema=schema.guid if schema else "",
            derivedFrom="",
            usedBy="",
            generatedBy=""
        )
        
        AppendCrate(output_path, [dataset])
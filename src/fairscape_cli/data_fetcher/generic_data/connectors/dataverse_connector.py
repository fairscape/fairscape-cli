# fairscape_cli/data_fetcher/generic_data/connectors/dataverse_connector.py
import requests
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from fairscape_cli.data_fetcher.generic_data.research_data import ResearchData

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

class DataverseConnector:
    """
    Connector for fetching data from Dataverse repositories.
    """
    
    def __init__(self, server_url: str = "https://dataverse.harvard.edu", api_token: Optional[str] = None):
        """
        Initialize the Dataverse connector.
        
        Args:
            server_url: URL of the Dataverse server
            api_token: Optional API token for accessing restricted datasets
        """
        self.server_url = server_url.rstrip("/")
        self.api_token = api_token
        self.headers = {}
        if api_token:
            self.headers["X-Dataverse-key"] = api_token
    
    def fetch_dataset(self, doi: str) -> Dict[str, Any]:
        """
        Fetch dataset metadata from Dataverse.
        
        Args:
            doi: Dataset DOI or persistent ID
            
        Returns:
            Dictionary containing dataset metadata
        """
        persistent_id = doi
        if doi.startswith("doi:"):
            persistent_id = doi
        elif doi.startswith("10."):
            persistent_id = f"doi:{doi}"
        
        url = f"{self.server_url}/api/datasets/:persistentId/"
        params = {"persistentId": persistent_id}
        
        response = requests.get(url, params=params, headers=self.headers)
        
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch dataset {doi}: {response.status_code} {response.text}")
        
        data = response.json()
        if "status" in data and data["status"] == "ERROR":
            raise ValueError(f"API error for dataset {doi}: {data.get('message', 'Unknown error')}")
        
        return data.get("data", {})
    
    def fetch_files(self, dataset_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Fetch files associated with a Dataverse dataset.
        
        Args:
            dataset_id: Dataverse dataset ID (numeric or string)
            
        Returns:
            List of dictionaries containing file metadata
        """

        url = f"{self.server_url}/api/datasets/{dataset_id}/versions/:latest/files"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch files for dataset ID {dataset_id}: {response.status_code} {response.text}")
        
        data = response.json()
        if "status" in data and data["status"] == "ERROR":
            raise ValueError(f"API error fetching files for dataset ID {dataset_id}: {data.get('message', 'Unknown error')}")
        
        return data.get("data", [])
    
    def fetch_data(self, doi: str, include_files: bool = True) -> ResearchData:
        """
        Fetch dataset and files data from Dataverse and convert to ResearchData.
        
        Args:
            doi: Dataset DOI or persistent ID
            include_files: Whether to include file metadata
            
        Returns:
            ResearchData object populated with Dataverse data
        """
        dataset_metadata_full = self.fetch_dataset(doi) 
        
        latest_version_info = dataset_metadata_full.get("latestVersion", {})
        metadata_blocks = latest_version_info.get("metadataBlocks", {})
        citation_metadata = metadata_blocks.get("citation", {}).get("fields", [])
        
        title = ""
        description = ""
        authors = []
        keywords = []
        publication_date = latest_version_info.get("releaseTime", "") 
        if not publication_date: 
             publication_date = latest_version_info.get("createTime", "")


        ds_description_values = []

        for field in citation_metadata:
            field_name = field.get("typeName", "")
            value = field.get("value")

            if field_name == "title":
                title = value if isinstance(value, str) else ""
            
            elif field_name == "dsDescription":
                if isinstance(value, list):
                    for desc_item in value:
                        if isinstance(desc_item, dict) and "dsDescriptionValue" in desc_item:
                            desc_val_field = desc_item["dsDescriptionValue"]
                            if isinstance(desc_val_field, dict) and "value" in desc_val_field:
                                ds_description_values.append(desc_val_field["value"])
                description = "\n\n".join(ds_description_values) if ds_description_values else ""


            elif field_name == "author":
                if isinstance(value, list):
                    for author_entry in value:
                        if isinstance(author_entry, dict):
                            author_name_field = author_entry.get("authorName", {})
                            if isinstance(author_name_field, dict):
                                author_name = author_name_field.get("value", "")
                                if author_name:
                                    authors.append(author_name)
            
            elif field_name == "keyword":
                if isinstance(value, list):
                    for keyword_entry in value:
                        if isinstance(keyword_entry, dict):
                            keyword_val_field = keyword_entry.get("keywordValue", {})
                            if isinstance(keyword_val_field, dict): 
                                keyword_value = keyword_val_field.get("value", "")
                                if keyword_value:
                                    keywords.append(keyword_value)
                            elif isinstance(keyword_entry, str):
                                keywords.append(keyword_entry)


            elif field_name == "distributionDate" and not publication_date:
                publication_date = value if isinstance(value, str) else ""
        
        if publication_date and isinstance(publication_date, str):
            try:
                dt = datetime.fromisoformat(publication_date.replace("Z", "+00:00"))
                publication_date = dt.isoformat()
            except ValueError:
                pass 

        files_data = []
        software_data = []
        
        if include_files:
            dataset_id = dataset_metadata_full.get("id") 
            if dataset_id:
                file_metadata_list = self.fetch_files(dataset_id)
                
                
                
                for file_entry in file_metadata_list:
                    data_file_info = file_entry.get("dataFile", {})
                    if not data_file_info: continue 

                    file_name = data_file_info.get("filename", "unnamed_file")
                    file_md5 = data_file_info.get("md5", "")
                    file_size = format_file_size(data_file_info.get("filesize", 0))
                    file_extension = os.path.splitext(file_name)[1].lower()
                    
                    software_extensions = ['.py', '.r', '.sh', '.exe', '.java', '.cpp', '.js', '.jsx', '.css'] # TODO: Make configurable
                    is_software = file_extension in software_extensions
                                       
                    file_db_id = data_file_info.get("id")
                    download_url = f"{self.server_url}/api/access/datafile/{file_db_id}"
                    dataset_landing_url = f"{self.server_url}/file.xhtml?fileId={file_db_id}"
                    
                    file_description = file_entry.get("description", "") 
                    if not file_description and data_file_info.get("description"):
                        file_description = data_file_info.get("description")
                    if len(file_description) < 10:
                        file_description = description

                    item_common_data = {
                        "id": file_db_id, 
                        "name": file_name,
                        "description": file_description,
                        "contentUrl": download_url,
                        "url": dataset_landing_url,
                        "dateModified": data_file_info.get("creationDate", publication_date), 
                        "format": file_extension.lstrip(".") or "application/octet-stream",
                        "contentSize": file_size,
                        "md5": file_md5,
                    }

                    if is_software:
                        software_data.append({
                            **item_common_data,
                            "version": latest_version_info.get("versionNumber", "1.0"), # Use dataset version for software
                            "documentation_url": dataset_landing_url
                        })
                    else:
                        files_data.append({
                            **item_common_data,
                            "size": data_file_info.get("filesize", 0),
                            "datePublished": data_file_info.get("creationDate", publication_date)
                        })
        
        # Extract license
        license_info = latest_version_info.get("license")
        license_url_or_name = "custom" 
        if license_info and isinstance(license_info, dict):
            if license_info.get("uri"):
                license_url_or_name = license_info["uri"]
            elif license_info.get("name"):
                 license_url_or_name = license_info["name"]


        return ResearchData(
            repository_name="Dataverse",
            project_id=doi, 
            title=title,
            description=description,
            authors=authors,
            license=license_url_or_name,
            keywords=keywords,
            publication_date=publication_date,
            doi=doi, 
            files=files_data,
            software=software_data,
            metadata={
                "url": f"{self.server_url}/dataset.xhtml?persistentId=doi:{doi}",
                "contentUrl": f"{self.server_url}/dataset.xhtml?persistentId=doi:{doi}",
                "publisher": dataset_metadata_full.get("publisher", ""),
                "version": latest_version_info.get("versionNumber"),
            }
        )
    
    def search_datasets(self, query: str, limit: int = 10, search_type: str = "dataset") -> List[Dict[str, Any]]:
        """
        Search for items (datasets, files, etc.) on Dataverse.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            search_type: Type of item to search for (e.g., "dataset", "file", "dataverse")
            
        Returns:
            List of item metadata dictionaries
        """
        url = f"{self.server_url}/api/search"
        params = {
            "q": query,
            "type": search_type,
            "per_page": limit,
            "show_relevance": "true"
        }
        
        response = requests.get(url, params=params, headers=self.headers)
        
        if response.status_code != 200:
            raise ValueError(f"Failed to search Dataverse: {response.status_code} {response.text}")
        
        data = response.json()
        if "status" in data and data["status"] == "ERROR":
            raise ValueError(f"API error during search: {data.get('message', 'Unknown error')}")
        
        return data.get("data", {}).get("items", [])
# fairscape_cli/data_fetcher/generic_data/connectors/figshare_connector.py
import requests
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from fairscape_cli.data_fetcher.generic_data.research_data import ResearchData

class FigshareConnector:
    BASE_URL = "https://api.figshare.com/v2"

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"token {token}"

    def fetch_article(self, article_id: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/articles/{article_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch article {article_id}: {response.status_code} {response.text}")
        return response.json()

    def fetch_files(self, article_id: str) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/articles/{article_id}/files"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch files for article {article_id}: {response.status_code} {response.text}")
        return response.json()

    def fetch_data(self, article_id: str, include_files: bool = True) -> ResearchData:
        article = self.fetch_article(article_id)

        authors = [author.get("full_name") for author in article.get("authors", []) if author.get("full_name")]
        keywords = article.get("tags", [])

        pub_date_str = article.get("published_date")
        if pub_date_str:
            try:
                dt = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%SZ")
                pub_date_str = dt.isoformat()
            except ValueError:
                pass 

        # This is the human-readable landing page URL
        figshare_landing_url = article.get("url_public_html", article.get("figshare_url", "")) # Fallback to figshare_url if url_public_html is missing

        files_list = []
        software_list = []

        if include_files:
            raw_files_data = self.fetch_files(article_id)
            for file_data in raw_files_data:
                file_name = file_data.get("name", "unnamed_file")
                file_extension = os.path.splitext(file_name)[1].lower()
                
                # Simplified software detection, you might want this to be more robust
                software_extensions = ['.py', '.r', '.sh', '.exe', '.java', '.cpp', '.js', '.jsx', '.css']
                is_software = file_extension in software_extensions
                print("file data:", file_data)


                item_attrs = {
                    "name": file_name,
                    "contentUrl": file_data.get("download_url"),
                    "url": figshare_landing_url,
                    "description": article.get("description", ""), 
                    "format": file_extension.lstrip(".") or file_data.get("mimetype", "application/octet-stream"),
                    "md5": file_data.get("supplied_md5") or file_data.get("computed_md5")
                }

                if is_software:
                    software_list.append({
                        **item_attrs,
                        "version": article.get("version", "0.1.0"), # Use Figshare item version
                        "dateDodified": article.get("modified_date", pub_date_str),
                        "documentation_url": figshare_landing_url,
                    })
                else:
                    files_list.append({
                        **item_attrs,
                        "size": file_data.get("size", 0),
                        "datePublished": article.get("published_date", pub_date_str), # Use article published date for file
                    })
        
        research_metadata = {
            "url": figshare_landing_url, 
            "contentUrl": article.get("url"),
            "citation": article.get("citation"),
            "version": str(article.get("version", "")), 
            "funding": article.get("funding_list", [])
        }

        return ResearchData(
            repository_name="Figshare",
            project_id=str(article_id),
            title=article.get("title", "Untitled Figshare Article"),
            description=article.get("description", ""),
            authors=authors,
            license=article.get("license", {}).get("url"),
            keywords=keywords,
            publication_date=pub_date_str,
            doi=article.get("doi"),
            files=files_list,
            software=software_list,
            metadata=research_metadata 
        )

    def search_articles(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/articles/search"
        params = {"search_for": query, "limit": limit}
        response = requests.post(url, json=params, headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to search articles: {response.status_code} {response.text}")
        return response.json()
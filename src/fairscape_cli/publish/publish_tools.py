import click
import json
import sys
import requests
from datetime import datetime
from pathlib import Path
import csv
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

def _load_authors_info(authors_csv_path: Optional[str]) -> Dict[str, Dict[str, str]]:
    authors_info = {}
    if authors_csv_path:
        try:
            with open(authors_csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get('name', '').strip().lower()
                    if name:
                        authors_info[name] = {
                            'affiliation': row.get('affiliation', ''),
                            'orcid': row.get('orcid', '')
                        }
        except FileNotFoundError:
            click.echo(f"Warning: Authors CSV file not found at {authors_csv_path}", err=True)
        except Exception as e:
            click.echo(f"Warning: Error loading authors CSV '{authors_csv_path}': {e}", err=True)
    return authors_info

def _read_rocrate_root(rocrate_path: Path) -> Optional[Dict]:
    try:
        with open(rocrate_path, 'r', encoding='utf-8') as f:
            rocrate_data = json.load(f)
    except FileNotFoundError:
        click.echo(f"Error: RO-Crate metadata file not found at {rocrate_path}", err=True)
        return None
    except json.JSONDecodeError:
        click.echo(f"Error: Invalid JSON in RO-Crate metadata file {rocrate_path}", err=True)
        return None
    except Exception as e:
        click.echo(f"Error reading RO-Crate metadata '{rocrate_path}': {e}", err=True)
        return None

    root_node = None
    graph = rocrate_data.get('@graph', [])
    metadata_node = next((item for item in graph if item.get('@id') == 'ro-crate-metadata.json'), None)
    if metadata_node and 'about' in metadata_node:
        about_id = metadata_node['about'].get('@id')
        root_node = next((item for item in graph if item.get('@id') == about_id), None)

    if not root_node:
        for item in graph:
            item_type = item.get('@type', [])
            if not isinstance(item_type, list):
                item_type = [item_type]
            if 'Dataset' in item_type and item.get('@id') != 'ro-crate-metadata.json':
                 if 'https://w3id.org/EVI#ROCrate' in item_type:
                     root_node = item
                     break
                 if root_node is None:
                     root_node = item

    if not root_node:
        click.echo("Error: Could not find root dataset node in RO-Crate graph.", err=True)
        return None

    return root_node


class Publisher(ABC):
    @abstractmethod
    def publish(self, rocrate_path: Path, **kwargs):
        pass

class FairscapePublisher(Publisher):
    def __init__(self, base_url: str = "https://fairscape.net/api"):
        self.base_url = base_url.rstrip('/')

    def _zip_directory(self, directory_path: Path) -> Path:
        import tempfile
        import zipfile
        import os
        
        click.echo(f"Zipping directory '{directory_path}'...")
        
        temp_zip_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip_path = Path(temp_zip_file.name)
        temp_zip_file.close()
        
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, directory_path)
                    zipf.write(file_path, arcname)
        
        click.echo(f"Directory zipped successfully: {temp_zip_path}")
        return temp_zip_path

    def _get_auth_token(self, username: str, password: str) -> str:
        url = f"{self.base_url}/login"
        
        data = {
            "username": username,
            "password": password
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            if "access_token" in token_data:
                return token_data["access_token"]
            else:
                click.echo(f"Error: Authentication response didn't contain access token", err=True)
                click.echo(f"Response: {response.text}", err=True)
                sys.exit(1)
                
        except requests.exceptions.RequestException as e:
            click.echo(f"Error authenticating with Fairscape API: {e}", err=True)
            sys.exit(1)

    def publish(self, rocrate_path: Path, username: str, password: str):
        click.echo(f"Publishing to Fairscape ({self.base_url})...")
        
        # Get authentication token
        token = self._get_auth_token(username, password)
        
        # Check if path is a directory, if so zip it
        if rocrate_path.is_dir():
            click.echo(f"Input path is a directory, zipping it first...")
            zip_path = self._zip_directory(rocrate_path)
            try:
                self._upload_zip(zip_path, token)
            finally:
                # Clean up temporary zip file
                if zip_path.exists():
                    zip_path.unlink()
        elif rocrate_path.suffix.lower() == '.zip':
            self._upload_zip(rocrate_path, token)
        else:
            click.echo(f"Error: Input path must be a directory or a zip file", err=True)
            sys.exit(1)

    def _upload_zip(self, zip_path: Path, token: str):
        url = f"{self.base_url}/rocrate/upload-async"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            with open(zip_path, 'rb') as f:
                files = {'crate': (zip_path.name, f, 'application/zip')}
                click.echo(f"Uploading zip file to Fairscape...")
                
                response = requests.post(url, headers=headers, files=files)
                
                if response.status_code == 200 or response.status_code == 201 or response.status_code == 202:
                    result = response.json()
                    transaction_id = result.get('transactionFolder', 'N/A')
                    click.echo(f"Successfully initiated upload to Fairscape!")
                    click.echo(f"Transaction ID: {transaction_id}")
                    click.echo(f"Check Fairscape dashboard for upload status.")
                    return transaction_id
                else:
                    click.echo(f"Error uploading dataset. Status: {response.status_code}", err=True)
                    click.echo(f"Response: {response.text}", err=True)
                    sys.exit(1)
                    
        except requests.exceptions.RequestException as e:
            click.echo(f"Error connecting to Fairscape API at {url}: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"An unexpected error occurred during Fairscape upload: {e}", err=True)
            sys.exit(1)

class DataversePublisher(Publisher):
    def __init__(self, base_url: str, collection_alias: str):
        self.base_url = base_url.rstrip('/')
        self.collection_alias = collection_alias

    def _transform_metadata(self, root_node: Dict, authors_info: Dict) -> Dict:
        license_map = {
            "https://creativecommons.org/licenses/by/4.0/": { "name": "CC BY 4.0", "uri": "https://creativecommons.org/licenses/by/4.0/"},
            "https://creativecommons.org/licenses/by-nc-sa/4.0/": { "name": "CC BY-NC-SA 4.0", "uri": "https://creativecommons.org/licenses/by-nc-sa/4.0/"},
            "https://creativecommons.org/publicdomain/zero/1.0/": { "name": "CC0 1.0", "uri": "http://creativecommons.org/publicdomain/zero/1.0"}
        }
        default_license_info = license_map["https://creativecommons.org/licenses/by/4.0/"]
        license_url = root_node.get('license', list(license_map.keys())[0])
        license_info = license_map.get(license_url, default_license_info)

        authors_raw = root_node.get('author', [])
        author_list = []
        if isinstance(authors_raw, str):
            delimiters = [',', ';']
            for d in delimiters:
                if d in authors_raw:
                    author_list = [a.strip() for a in authors_raw.split(d) if a.strip()]
                    break
            if not author_list:
                author_list = [authors_raw.strip()] if authors_raw.strip() else []
        elif isinstance(authors_raw, list):
             for item in authors_raw:
                 if isinstance(item, str):
                     author_list.append(item.strip())
                 elif isinstance(item, dict) and 'name' in item:
                     author_list.append(item['name'].strip())

        author_entries = []
        for name in author_list:
            author_name_lower = name.lower()
            author_details = authors_info.get(author_name_lower, {})
            entry = {
                "authorName": {"typeName": "authorName", "multiple": False, "typeClass": "primitive", "value": name},
                "authorAffiliation": {"typeName": "authorAffiliation", "multiple": False, "typeClass": "primitive", "value": author_details.get('affiliation', '')}
            }
            orcid = author_details.get('orcid', '')
            if orcid:
                if len(orcid) == 19 and orcid[4] == '-' and orcid[9] == '-' and orcid[14] == '-':
                    entry["authorIdentifierScheme"] = {"typeName": "authorIdentifierScheme", "multiple": False, "typeClass": "controlledVocabulary", "value": "ORCID"}
                    entry["authorIdentifier"] = {"typeName": "authorIdentifier", "multiple": False, "typeClass": "primitive", "value": orcid}
                else:
                    click.echo(f"Warning: Invalid ORCID format '{orcid}' for author '{name}'. Skipping ORCID.", err=True)

            author_entries.append(entry)

        if not author_entries:
             author_entries.append({
                 "authorName": {"typeName": "authorName", "multiple": False, "typeClass": "primitive", "value": "Unknown"},
                 "authorAffiliation": {"typeName": "authorAffiliation", "multiple": False, "typeClass": "primitive", "value": ""}
             })

        keywords_raw = root_node.get('keywords', [])
        keyword_list = []
        if isinstance(keywords_raw, str):
            keyword_list = [k.strip() for k in keywords_raw.split(',') if k.strip()]
        elif isinstance(keywords_raw, list):
            keyword_list = [str(k).strip() for k in keywords_raw if str(k).strip()]

        keyword_entries = [{"keywordValue": {"typeName": "keywordValue", "multiple": False, "typeClass": "primitive", "value": kw}} for kw in keyword_list]

        contact_name = root_node.get("principalInvestigator", author_list[0] if author_list else "Unknown")
        contact_email = root_node.get("contactEmail", "placeholder@example.com")

        pub_date_raw = root_node.get("datePublished", datetime.today().strftime('%Y-%m-%d'))
        try:
            dt_obj = datetime.fromisoformat(pub_date_raw.split('T')[0])
            pub_date = dt_obj.strftime('%Y-%m-%d')
        except ValueError:
             try:
                 dt_obj = datetime.strptime(pub_date_raw, '%m/%d/%Y')
                 pub_date = dt_obj.strftime('%Y-%m-%d')
             except ValueError:
                 pub_date = datetime.today().strftime('%Y-%m-%d')

        dv_metadata = {
            "datasetVersion": {
                "license": license_info,
                "metadataBlocks": {
                    "citation": {
                        "displayName": "Citation Metadata",
                        "fields": [
                            {"typeName": "title", "multiple": False, "typeClass": "primitive", "value": root_node.get("name", "Untitled Dataset")},
                            {"typeName": "author", "multiple": True, "typeClass": "compound", "value": author_entries},
                            {"typeName": "datasetContact", "multiple": True, "typeClass": "compound", "value": [
                                {"datasetContactName": {"typeName": "datasetContactName", "multiple": False, "typeClass": "primitive", "value": contact_name},
                                 "datasetContactEmail": {"typeName": "datasetContactEmail", "multiple": False, "typeClass": "primitive", "value": contact_email}}
                            ]},
                            {"typeName": "dsDescription", "multiple": True, "typeClass": "compound", "value": [
                                {"dsDescriptionValue": {"typeName": "dsDescriptionValue", "multiple": False, "typeClass": "primitive", "value": root_node.get("description", "")}}
                            ]},
                            {"typeName": "subject", "multiple": True, "typeClass": "controlledVocabulary", "value": root_node.get("subject", ["Other"])},
                            {"typeName": "keyword", "multiple": True, "typeClass": "compound", "value": keyword_entries},
                             {"typeName": "notesText", "multiple": False, "typeClass": "primitive", "value": f"RO-Crate Source: {root_node.get('@id', 'N/A')}"},
                             {"typeName": "distributionDate", "multiple": False, "typeClass": "primitive", "value": pub_date},
                             {"typeName": "dateOfDeposit", "multiple": False, "typeClass": "primitive", "value": datetime.today().strftime('%Y-%m-%d')}
                        ]
                    }
                
                }
            }
        }
        return dv_metadata

    def publish(self, rocrate_path: Path, api_token: str, authors_csv_path: Optional[str]):
        click.echo(f"Publishing RO-Crate '{rocrate_path.name}' to Dataverse ({self.base_url})...")
        root_node = _read_rocrate_root(rocrate_path)
        if not root_node:
            sys.exit(1)

        authors_info = _load_authors_info(authors_csv_path)
        dataverse_metadata = self._transform_metadata(root_node, authors_info)

        url = f"{self.base_url}/api/dataverses/{self.collection_alias}/datasets"
        headers = {"X-Dataverse-key": api_token, "Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=dataverse_metadata)
            response.raise_for_status()

            if response.status_code == 201:
                result = response.json()
                persistent_id = result.get('data', {}).get('persistentId', 'N/A')
                click.echo(f"Successfully created dataset on Dataverse!")
                click.echo(f"Persistent Identifier: {persistent_id}")
                dataset_id = result.get('data', {}).get('id', '')
                if dataset_id:
                    click.echo(f"Dataverse Dataset URL: {self.base_url}/dataset.xhtml?persistentId={persistent_id}&version=DRAFT")
                return persistent_id
            else:
                click.echo(f"Error creating dataset. Status: {response.status_code}", err=True)
                click.echo(f"Response: {response.text}", err=True)
                sys.exit(1)

        except requests.exceptions.RequestException as e:
            click.echo(f"Error connecting to Dataverse API at {url}: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"An unexpected error occurred during Dataverse publishing: {e}", err=True)
            sys.exit(1)


class DataCitePublisher(Publisher):
    def __init__(self, prefix: str, repository_id: str, api_url: str):
        self.prefix = prefix
        self.repository_id = repository_id
        self.api_url = api_url.rstrip('/')

    def _transform_metadata(self, root_node: Dict) -> Dict:
        authors_raw = root_node.get('author', [])
        creator_list = []
        if isinstance(authors_raw, str):
            delimiters = [',', ';']
            names = []
            for d in delimiters:
                if d in authors_raw:
                    names = [a.strip() for a in authors_raw.split(d) if a.strip()]
                    break
            if not names: names = [authors_raw.strip()] if authors_raw.strip() else []
            creator_list = [{"name": name} for name in names]

        elif isinstance(authors_raw, list):
             for item in authors_raw:
                 if isinstance(item, str):
                     creator_list.append({"name": item.strip()})
                 elif isinstance(item, dict):
                     entry = {}
                     if 'name' in item: entry['name'] = item['name']
                     if 'affiliation' in item: entry['affiliation'] = [item['affiliation']]
                     if 'orcid' in item:
                          entry['nameIdentifiers'] = [{
                              "nameIdentifier": item['orcid'],
                              "nameIdentifierScheme": "ORCID",
                              "schemeUri": "https://orcid.org"
                          }]
                     if entry.get("name"):
                        creator_list.append(entry)

        if not creator_list:
            creator_list = [{"name": "Unknown"}]

        keywords_raw = root_node.get('keywords', [])
        keyword_list = []
        if isinstance(keywords_raw, str):
            keyword_list = [k.strip() for k in keywords_raw.split(',') if k.strip()]
        elif isinstance(keywords_raw, list):
            keyword_list = [str(k).strip() for k in keywords_raw if str(k).strip()]
        subject_list = [{"subject": kw} for kw in keyword_list]

        pub_date_raw = root_node.get("datePublished", datetime.today().strftime('%Y-%m-%d'))
        pub_year = datetime.today().year
        dates_list = []
        try:
            dt_obj = datetime.fromisoformat(pub_date_raw.split('T')[0])
            pub_year = dt_obj.year
            dates_list.append({"date": dt_obj.strftime('%Y-%m-%d'), "dateType": "Issued"})
        except ValueError:
             try:
                 dt_obj = datetime.strptime(pub_date_raw, '%m/%d/%Y')
                 pub_year = dt_obj.year
                 dates_list.append({"date": dt_obj.strftime('%Y-%m-%d'), "dateType": "Issued"})
             except ValueError:
                 dates_list.append({"date": datetime.today().strftime('%Y-%m-%d'), "dateType": "Issued"})

        rights_list = []
        license_url = root_node.get('license')
        if license_url:
             license_name = license_url.split('/')[-2] if license_url.count('/') > 3 else license_url
             rights_list.append({
                 "rights": license_name.upper().replace('-', ' '),
                 "rightsUri": license_url
             })

        datacite_payload = {
            "data": {
                "type": "dois",
                "attributes": {
                    "prefix": self.prefix,
                    "publisher": root_node.get("publisher", "Unknown"),
                    "publicationYear": pub_year,
                    "titles": [{"title": root_node.get("name", "Untitled Dataset")}],
                    "creators": creator_list,
                    "types": {"resourceTypeGeneral": "Dataset"},
                    "subjects": subject_list if subject_list else None,
                    "contributors": [],
                    "dates": dates_list if dates_list else None,
                    "language": "en",
                    "alternateIdentifiers": [],
                    "relatedIdentifiers": [],
                    "sizes": [],
                    "formats": [],
                    "version": root_node.get("version"),
                    "rightsList": rights_list if rights_list else None,
                    "descriptions": [{"description": root_node.get("description", ""), "descriptionType": "Abstract"}] if root_node.get("description") else None,
                    "geoLocations": [],
                    "fundingReferences": [],
                    "url": root_node.get("url") or root_node.get('@id'),
                    "schemaVersion": "http://datacite.org/schema/kernel-4"
                }
            }
        }
        
        for key, value in list(datacite_payload["data"]["attributes"].items()):
            if value is None or (isinstance(value, list) and not value):
                del datacite_payload["data"]["attributes"][key]

        return datacite_payload

    def publish(self, rocrate_path: Path, username: str, password: str, event: str = 'publish'):
        click.echo(f"Publishing RO-Crate '{rocrate_path.name}' to DataCite ({self.api_url})...")
        root_node = _read_rocrate_root(rocrate_path)
        if not root_node:
            sys.exit(1)

        datacite_metadata = self._transform_metadata(root_node)
        datacite_metadata["data"]["attributes"]["event"] = event

        url = f"{self.api_url}/dois"
        headers = {"Content-Type": "application/vnd.api+json"}
        auth = (username, password)

        try:
            response = requests.post(url, headers=headers, json=datacite_metadata, auth=auth)
            response.raise_for_status()

            if response.status_code == 201:
                result = response.json()
                doi = result.get('data', {}).get('id', 'N/A')
                doi_url = result.get('data', {}).get('attributes', {}).get('url', '')
                click.echo(f"Successfully created DOI on DataCite!")
                click.echo(f"DOI: {doi}")
                click.echo(f"URL: https://doi.org/{doi}")
                if doi_url: click.echo(f"Landing Page: {doi_url}")
                return doi
            else:
                click.echo(f"Error creating DOI. Status: {response.status_code}", err=True)
                click.echo(f"Response: {response.text}", err=True)
                sys.exit(1)

        except requests.exceptions.RequestException as e:
            click.echo(f"Error connecting to DataCite API at {url}: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"An unexpected error occurred during DataCite publishing: {e}", err=True)
            sys.exit(1)
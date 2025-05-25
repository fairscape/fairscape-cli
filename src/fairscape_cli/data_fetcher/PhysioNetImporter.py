import requests
from bs4 import BeautifulSoup, Tag
import pathlib
from datetime import datetime
from typing import List, Optional, Dict, Any
import sys
import urllib.parse
import os
import re

from fairscape_cli.models.rocrate import GenerateROCrate, AppendCrate
from fairscape_cli.models.dataset import GenerateDataset
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid, clean_guid
from fairscape_cli.config import NAAN


class PhysioNetImporter:

    def __init__(self, physionet_url: str, output_dir: pathlib.Path):
        self.physionet_url = self._normalize_url(physionet_url)
        self.output_dir = output_dir
        self.project_id, self.version = self._parse_physionet_url(self.physionet_url)
        
        if not self.project_id or not self.version:
             raise ValueError(f"Could not parse PhysioNet project ID and version from URL: {physionet_url}. Ensure the URL points to a project version page (e.g., https://physionet.org/content/bigp3bci/1.0.0/).")

        self.base_file_download_url = f"https://physionet.org/files/{self.project_id}/{self.version}/"
        self.base_content_url = f"https://physionet.org/content/{self.project_id}/{self.version}/"


    def _normalize_url(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        if not path.endswith('/'):
            path += '/'
        return urllib.parse.urlunparse(parsed._replace(path=path))


    def _parse_physionet_url(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """Find version and project ID in the URL path."""
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        parts = [part for part in path.split('/') if part]

        project_id = None
        version_str = None

        try:
            content_index = parts.index('content')
            if len(parts) > content_index + 2:
                project_id = parts[content_index + 1]
                if len(parts) > content_index + 3 and parts[content_index + 2] == 'files-panel':
                     version_str = parts[content_index + 3]
                else:
                     version_str = parts[content_index + 2]

            if project_id and version_str:
                 return project_id, version_str
        except ValueError:
            print(f"'content' not found in URL path: {url}", file=sys.stderr)
            pass
        return None, None


    def _fetch_and_parse_html(self, url: str) -> BeautifulSoup:
        """"Fetches HTML content from a URL and parses it with BeautifulSoup."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            print(f"Successfully fetched {url}", file=sys.stderr)
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.Timeout):
                print(f"ERROR: Timeout fetching {url}", file=sys.stderr)
            elif isinstance(e, requests.exceptions.HTTPError):
                 print(f"ERROR: HTTP error fetching {url}: {e.response.status_code} {e.response.reason}", file=sys.stderr)
            else:
                 print(f"ERROR: Request error fetching {url}: {e}", file=sys.stderr)
            raise ConnectionError(f"Failed to fetch URL {url}: {e}")
        except Exception as e:
             print(f"ERROR: Error parsing HTML from {url}: {e}", file=sys.stderr)
             raise RuntimeError(f"Error parsing HTML from {url}: {e}")

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Pulls metadata from the HTML soup."""
        metadata: Dict[str, Any] = {}
        
        title_tag = soup.find('h1', class_='form-signin-heading')
        if title_tag:
            metadata['name'] = title_tag.get_text(strip=True)

        abstract_tag = soup.find('h2', id='abstract')
        if abstract_tag and abstract_tag.find_next_sibling(['p', 'div', 'section']):
             content_html = ""
             for sibling in abstract_tag.find_next_siblings():
                 if sibling.name in ['h2', 'hr']: break
                 content_html += str(sibling)
             if content_html.strip():
                 metadata['description'] = content_html.strip()

        author_tags = soup.select('p strong a.author')
        if author_tags:
             authors = [a.get_text(strip=True) for a in author_tags]
             metadata['author'] = ", ".join(authors) 

        published_p_tag = soup.find('p', string=lambda text: text and text.strip().startswith('Published:'))
        if published_p_tag:
            full_text = published_p_tag.get_text(strip=True)
            date_part_str = ""
            version_part_str = ""
            
            version_split_patterns = ['. Version:', 'Version:']
            split_successful = False
            for pattern in version_split_patterns:
                if pattern in full_text:
                    parts = full_text.split(pattern, 1)
                    date_part_str = parts[0].replace('Published:', '').strip()
                    if date_part_str.endswith('.'): date_part_str = date_part_str[:-1].strip()
                    if len(parts) > 1:
                        version_part_str = parts[1].strip()
                    split_successful = True
                    break
            
            if not split_successful:
                 date_part_str = full_text.replace('Published:', '').strip()

            if version_part_str:
                metadata['dataset_version'] = version_part_str
            
            if date_part_str:
                try:
                    parsed_date = None
                    for fmt in ["%B %d, %Y", "%b. %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%fZ"]:
                        try:
                            parsed_date = datetime.strptime(date_part_str, fmt)
                            break
                        except ValueError:
                            continue
                    if parsed_date:
                        metadata['datePublished'] = parsed_date.isoformat()
                    else:
                        print(f"Warning: Could not parse date string '{date_part_str}' from '{full_text}'", file=sys.stderr)
                except Exception as e:
                    print(f"Error parsing date from '{full_text}': {e}", file=sys.stderr)

        if 'dataset_version' not in metadata:
            wfdb_comment = soup.find(string=lambda text: isinstance(text, str) and "wfdb-python:" in text)
            if wfdb_comment:
                comment_text = str(wfdb_comment)
                version_match = re.search(r'Version:\s*([^<\n]+)', comment_text)
                if version_match:
                    metadata['dataset_version'] = version_match.group(1).strip()
            elif self.version: 
                metadata['dataset_version'] = self.version

        citation_alert = soup.find('div', class_='alert alert-secondary')
        if citation_alert:
             citation_entries_strings: List[str] = [] 

             cite_p = citation_alert.find('p', string=lambda text: text and 'When using this resource, please cite:' in text)
             if not cite_p: cite_p = citation_alert.find('p')

             if cite_p:
                  doi_link_tag = cite_p.find('a', href=lambda href: href and 'doi.org' in href)
                  if doi_link_tag and doi_link_tag.get('href'):
                      citation_entries_strings.append(doi_link_tag['href'])
                  else:
                       other_link_tag = cite_p.find('a', href=True)
                       if other_link_tag and other_link_tag.get('href'):
                            if other_link_tag.get_text(strip=True) != "(show more options)":
                                citation_entries_strings.append(other_link_tag['href'])

                  citation_text_elements = []
                  for elem in cite_p.contents:
                      if isinstance(elem, Tag):
                          if elem.name == 'a' and elem.get_text(strip=True) == "(show more options)":
                              continue
                          if doi_link_tag and elem == doi_link_tag:
                               continue
                          citation_text_elements.append(elem.get_text(strip=True))
                      elif isinstance(elem, str):
                          citation_text_elements.append(elem.strip())

                  citation_text = " ".join(citation_text_elements).strip()
                  if citation_text.lower().startswith('when using this resource, please cite:'):
                      citation_text = citation_text[len('when using this resource, please cite:'):].strip()
                  citation_text = citation_text.replace('(show more options)', '').strip()
                  citation_text = ' '.join(citation_text.split())

                  existing_strings = set(citation_entries_strings)
                  if citation_text and citation_text not in existing_strings:
                      citation_entries_strings.append(citation_text)

             if citation_entries_strings:
                  metadata['associatedPublication'] = list(set(citation_entries_strings))

        def extract_section_html(section_id: str) -> Optional[str]:
            header_tag = soup.find('h2', id=section_id)
            if header_tag:
                content_html = ""
                for sibling in header_tag.find_next_siblings():
                    if sibling.name in ['h2', 'hr']: break
                    content_html += str(sibling)
                return content_html.strip() if content_html.strip() else None
            return None

        for section_id, prop_name, is_additional in [
            ('background', "Background", True),
            ('methods', "Methods", True),
            ('usage-notes', "usageInfo", False),
            ('ethics', "ethicalReview", False),
            ('acknowledgements', "Acknowledgements", True),
            ('conflicts-of-interest', "Conflicts of Interest", True)
        ]:
            html_content = extract_section_html(section_id)
            if html_content:
                if not is_additional:
                    metadata[prop_name] = html_content 
                else:
                    metadata.setdefault('additionalProperty', []).append(
                        {"@type": "PropertyValue", "name": prop_name, "value": html_content}
                    )

        discovery_card_body = None
        discovery_header = soup.find('h5', class_='card-header', string='Discovery')
        if discovery_header: discovery_card_body = discovery_header.find_next_sibling('div', class_='card-body')
        
        if discovery_card_body:
            topics_p = discovery_card_body.find('p', string=lambda text: text and text.strip().startswith('Topics:'))
            if topics_p:
                keywords = [span.get_text(strip=True) for span in topics_p.select('a span.badge-pn')]
                if keywords: 
                    metadata['extracted_keywords'] = keywords 

            doi_version_p = discovery_card_body.find('p', string=lambda text: text and text.strip().startswith('DOI (version'))
            if doi_version_p:
                doi_link = doi_version_p.find('a')
                if doi_link and doi_link.get('href'): 
                    metadata['dataset_identifier'] = doi_link['href'] 
            
            latest_doi_p = discovery_card_body.find('p', string=lambda text: text and text.strip().startswith('DOI (latest version'))
            if latest_doi_p and 'dataset_identifier' not in metadata: 
                 latest_doi_link = latest_doi_p.find('a')
                 if latest_doi_link and latest_doi_link.get('href'):
                     metadata['dataset_identifier'] = latest_doi_link['href']

        access_card_body = None
        access_header = soup.find('h5', class_='card-header', string='Access')
        if access_header: access_card_body = access_header.find_next_sibling('div', class_='card-body')
        if access_card_body:
            license_p = access_card_body.find('p', string=lambda text: text and text.strip().startswith('License (for files):'))
            if license_p:
                license_link = license_p.find('a')
                if license_link and license_link.get('href'): 
                    metadata['extracted_license'] = license_link['href']
        return metadata


    def _process_file_table_rows(self, table_body_soup: BeautifulSoup, current_subdir_path: str, all_files_list: List[Dict[str, Any]], subdirs_to_explore: List[str], crate_default_date_published: str):
        """
        Processes rows from a single file table body soup, adding files to the list
        and subdirectories to the exploration queue.
        """
        
        rows_to_process = list(table_body_soup.select('tr'))

        for row in rows_to_process:
            name_cell_a_tag = row.select_one('td a')
            if not name_cell_a_tag:
                continue

            name = name_cell_a_tag.get_text(strip=True)
            
            if name in ['.', '..', '<base>']: 
                continue

            is_directory = 'subdir' in row.get('class', [])
            
            item_relative_path: str = ""
            if is_directory:
                # For directories, the data-dfp-dir attribute provides the path relative to the file panel root
                item_relative_path = name_cell_a_tag.get('data-dfp-dir')
                if not item_relative_path:
                     continue
                print(f"DEBUG: Found directory: {name} (data-dfp-dir: {item_relative_path}) in {current_subdir_path or '<root>'}. Adding to queue.", file=sys.stderr)
                subdirs_to_explore.append(item_relative_path) # Add to queue
            else: 
                item_relative_path = os.path.join(current_subdir_path, name).replace('\\', '/') 


            if not is_directory:
                item_info: Dict[str, Any] = {
                    'name': name,
                    'relative_path': item_relative_path,
                    'datePublished': crate_default_date_published,
                    'is_directory': is_directory 
                }
                
                size_cell = row.select_one('td:nth-of-type(2)')
                if size_cell:
                    size_text = size_cell.get_text(strip=True)
                    if size_text and size_text != '-':
                        item_info['contentSize'] = size_text
                
                item_info['contentUrl'] = f"{self.base_file_download_url}{urllib.parse.quote(item_relative_path)}"
                item_info['format'] = pathlib.Path(name).suffix[1:].lower() if pathlib.Path(name).suffix else "application/octet-stream"
                
                all_files_list.append(item_info)


    def to_rocrate(
        self,
        output_dir: pathlib.Path,
        author: str, 
        crate_name: Optional[str] = None,
        crate_description: Optional[str] = None,
        crate_keywords: Optional[List[str]] = None,
        crate_license: Optional[str] = None,
        crate_version: Optional[str] = None, 
        organization_name: Optional[str] = None,
        project_name: Optional[str] = None,
        associated_publication: Optional[List[Dict[str, Any]]] = None,
        usage_info: Optional[str] = None, 
        ethical_review: Optional[str] = None, 
        additional_properties: Optional[List[Dict[str, Any]]] = None, 
        identifier: Optional[str] = None 
    ) -> str:
        
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = output_dir / 'ro-crate-metadata.json'

        # Step 1: Fetch the initial project page URL
        print(f"Fetching initial project page from: {self.physionet_url}", file=sys.stderr)
        initial_soup = self._fetch_and_parse_html(self.physionet_url)
        
        # Step 2: Extract metadata from the main page content
        extracted_metadata = self._extract_metadata(initial_soup)
        print("Metadata extraction complete.", file=sys.stderr)
        
        physionet_dataset_version = extracted_metadata.get('dataset_version', self.version or "unknown")
        crate_effective_version = crate_version if crate_version is not None else physionet_dataset_version
        crate_default_date_published = extracted_metadata.get('datePublished', datetime.now().isoformat())

        root_guid = f"ark:{NAAN}/{clean_guid(self.project_id)}-{clean_guid(physionet_dataset_version)}-{GenerateDatetimeSquid()}"

        final_name = crate_name if crate_name is not None else extracted_metadata.get('name', f"PhysioNet Project {self.project_id}")
        final_description = crate_description if crate_description is not None else extracted_metadata.get('description', f"Data from PhysioNet project {self.project_id} v{physionet_dataset_version}")
        final_author = author if author else extracted_metadata.get('author', "Unknown Author")
        final_date_published = crate_default_date_published
        final_license = crate_license if crate_license is not None else extracted_metadata.get('extracted_license', "https://creativecommons.org/licenses/by/4.0/")
        final_version = crate_effective_version
        final_organization_name = organization_name
        final_project_name = project_name
        final_identifier = identifier if identifier is not None else extracted_metadata.get('dataset_identifier')

        cli_keywords_list = crate_keywords if crate_keywords is not None else []
        extracted_keywords_list = extracted_metadata.get('extracted_keywords', [])
        final_keywords = list(set(cli_keywords_list + extracted_keywords_list))

        final_associated_publication: List[str] = []
        if associated_publication is not None:
             for pub_dict in associated_publication:
                  if isinstance(pub_dict, dict):
                       if 'identifier' in pub_dict and pub_dict['identifier']: final_associated_publication.append(str(pub_dict['identifier']))
                       elif 'url' in pub_dict and pub_dict['url']: final_associated_publication.append(str(pub_dict['url']))
                       elif 'description' in pub_dict and pub_dict['description']: final_associated_publication.append(str(pub_dict['description']))
                  elif isinstance(pub_dict, str):
                       final_associated_publication.append(pub_dict)
        elif extracted_metadata.get('associatedPublication') is not None:
             final_associated_publication = extracted_metadata['associatedPublication']

        cli_props = additional_properties or []
        extracted_props = extracted_metadata.get('additionalProperty', [])
        
        merged_additional_properties = []
        cli_prop_names = {prop.get('name') for prop in cli_props if isinstance(prop, dict) and prop.get('name')}
        for prop in cli_props:
             if isinstance(prop, dict): merged_additional_properties.append(prop)
        for prop in extracted_props:
             if isinstance(prop, dict) and prop.get('name') and prop.get('name') not in cli_prop_names:
                  merged_additional_properties.append(prop)

        final_usage_info = usage_info if usage_info is not None else extracted_metadata.get('usageInfo')
        final_ethical_review = ethical_review if ethical_review is not None else extracted_metadata.get('ethicalReview')

        root_metadata_params: Dict[str, Any] = {
            "guid": root_guid,
            "name": final_name,
            "description": final_description,
            "author": final_author,
            "datePublished": final_date_published,
            "license": final_license,
            "version": final_version,
            "keywords": final_keywords, 
            "organizationName": final_organization_name,
            "projectName": final_project_name,
            "path": output_dir,
            "associatedPublication": final_associated_publication if final_associated_publication else None,
            "usageInfo": final_usage_info,
            "ethicalReview": final_ethical_review,
            "additionalProperty": merged_additional_properties if merged_additional_properties else None,
            "identifier": final_identifier ,
            "url": self.physionet_url.rstrip('/'),
        }

        root_metadata_params.setdefault("additionalProperty", [])

        try:
             root_crate_dict = GenerateROCrate(**root_metadata_params) 
        except Exception as e:
             print("ERROR: Failed to validate root RO-Crate metadata.", file=sys.stderr)
             print(f"Pydantic errors: {e}", file=sys.stderr)
             raise

        root_crate_guid = root_crate_dict['@id']
        print(f"Root RO-Crate GUID: {root_crate_guid}", file=sys.stderr)

        # Step 3: Find the root file panel table on the initial page
        files_panel_div = initial_soup.select_one('#files-panel')
        if not files_panel_div:
            print("Warning: '#files-panel' div not found on the initial page. Cannot list files.", file=sys.stderr)
            return root_crate_guid

        root_table_body = files_panel_div.select_one('table.files-panel tbody')
        if not root_table_body:
            return root_crate_guid
        
        # Step 4: Initialize lists and process the root file table
        all_file_entries: List[Dict[str, Any]] = []
        subdirs_to_explore: List[str] = []
        self._process_file_table_rows(root_table_body, "", all_file_entries, subdirs_to_explore, crate_default_date_published)

        # Step 5: Iteratively explore subdirectories from the queue
        if subdirs_to_explore:
             print(f"Starting iterative exploration of {len(subdirs_to_explore)} subdirectories...", file=sys.stderr)
             
             while subdirs_to_explore:
                  current_subdir = subdirs_to_explore.pop(0) # Breadth-first traversal

                  subdir_url_to_fetch = urllib.parse.urljoin(self.base_content_url, current_subdir.strip('/') + '/#files-panel')

                  try:
                      subdir_soup = self._fetch_and_parse_html(subdir_url_to_fetch)
                  except (ConnectionError, RuntimeError) as e:
                       print(f"ERROR: Skipping subdirectory {current_subdir} due to fetch/parse error: {e}", file=sys.stderr)
                       continue

                  files_panel_div = subdir_soup.select_one('#files-panel')
                  if not files_panel_div:
                      continue

                  subdir_table_body = files_panel_div.select_one('table.files-panel tbody')
                  if not subdir_table_body:
                      continue
                  
                  self._process_file_table_rows(subdir_table_body, current_subdir, all_file_entries, subdirs_to_explore, crate_default_date_published)

        else:
             print("No subdirectories found to explore from the root.", file=sys.stderr)


        print(f"Total files found: {len(all_file_entries)}", file=sys.stderr)

        # Step 6: Create Dataset entities for all found files
        crate_elements_to_add = []
        
        for item_data in all_file_entries:
            item_path_guid_segment = item_data['relative_path'].replace('/', '_').replace('.', '_').replace(' ', '_').lower()
            item_path_guid_segment = clean_guid(item_path_guid_segment)
            
            sq = GenerateDatetimeSquid()
            guid = f"ark:{NAAN}/file-{clean_guid(self.project_id)}-{clean_guid(physionet_dataset_version)}-{item_path_guid_segment}-{sq}"

            dataset_params: Dict[str, Any] = {
                "guid": guid,
                "name": item_data['relative_path'], 
                "description": f"File '{item_data['name']}' at path '{item_data['relative_path']}' from PhysioNet dataset {self.project_id} v{physionet_dataset_version}",
                "author": final_author,
                "version": physionet_dataset_version, 
                "isPartOf": [{"@id": root_crate_guid}],
                "@type": "Dataset",
                "keywords": final_keywords, 
                "datePublished": item_data['datePublished'],
                "format": item_data.get('format', "application/octet-stream") 
            }
            if 'contentSize' in item_data: dataset_params['contentSize'] = item_data['contentSize']
            if 'contentUrl' in item_data: dataset_params['contentUrl'] = item_data['contentUrl']


            try:
                if 'Directory' in item_data['relative_path']:
                    continue
                dataset_entity = GenerateDataset(**dataset_params)
                crate_elements_to_add.append(dataset_entity)
            except Exception as e:
                print(f"ERROR: Failed to generate Dataset Pydantic model for item path: {item_data.get('relative_path')}", file=sys.stderr)
                print(f"Pydantic error: {e}", file=sys.stderr)
                continue

        if crate_elements_to_add:
             AppendCrate(metadata_path, crate_elements_to_add) 
        
        return root_crate_guid
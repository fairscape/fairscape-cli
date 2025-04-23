import os
import json
from datetime import datetime
from .base import ROCrateProcessor
from .template_engine import TemplateEngine

class PreviewGenerator:
    DEFAULT_TEMPLATE = 'preview.html'
    DESCRIPTION_TRUNCATE_LENGTH = 100

    def __init__(self, processor: ROCrateProcessor, template_engine: TemplateEngine, base_dir: str):
        self.processor = processor
        self.template_engine = template_engine
        self.base_dir = base_dir

    def _prepare_item_data(self, items):
        prepared_items = []
        if not items: 
            return []
        for item in items:
            if not isinstance(item, dict): 
                 continue

            name = item.get("name", item.get("@id", "Unnamed Item"))
            description = item.get("description", "")
            if description is None: 
                 description = ""

            description_display = description
            if len(description) > self.DESCRIPTION_TRUNCATE_LENGTH:
                description_display = description[:self.DESCRIPTION_TRUNCATE_LENGTH] + "..."

            date = item.get("datePublished", "") or \
                   item.get("dateModified", "") or \
                   item.get("dateCreated", "") or \
                   item.get("date", "")

            content_url = item.get("contentUrl", "")
            if isinstance(content_url, list):
                content_url = content_url[0] if content_url else ""

            content_status = "Not specified"
            if content_url == "Embargoed":
                content_status = "Embargoed"
            elif content_url:
                link_target = content_url
                if not link_target.startswith(('http:', 'https:', 'ftp:', '/')):
                     if self.base_dir and link_target:
                         try:
                            abs_link_path = os.path.normpath(os.path.join(self.base_dir, link_target))
                            link_target = os.path.relpath(abs_link_path, self.base_dir)
                         except ValueError:
                            link_target = content_url 
                     else:
                        link_target = content_url 

                content_status = f"<a href='{link_target}'>Access / Download</a>"

            item_type = item.get("@type", "Unknown")
            if isinstance(item_type, list):
                specific_types = [t for t in item_type if t and not t.startswith(('http', 'https'))]
                item_type = specific_types[0] if specific_types else ", ".join(filter(None, item_type))
            elif item_type is None:
                item_type = "Unknown"

            manufacturer_raw = item.get("manufacturer")
            manufacturer_name = "N/A"
            if isinstance(manufacturer_raw, dict):
                manufacturer_name = manufacturer_raw.get("name", "N/A")
            elif isinstance(manufacturer_raw, str):
                manufacturer_name = manufacturer_raw

            schema_properties = None
            if item_type == "EVI:Schema" or "Schema" in str(item_type):
                props = item.get("properties", {})
                if props and isinstance(props, dict):
                    schema_properties = {}
                    for prop_name, prop_details in props.items():
                        if isinstance(prop_details, dict):
                            schema_properties[prop_name] = {
                                "type": prop_details.get("type", "Unknown"),
                                "description": prop_details.get("description", ""),
                                "index": prop_details.get("index", "N/A")
                            }

            prepared_items.append({
                "name": name,
                "description": description,
                "description_display": description_display,
                "date": date or "N/A", 
                "content_status": content_status,
                "id": item.get("@id", ""),
                "type": item_type,
                "identifier": item.get("identifier", item.get("@id", "")),
                "experimentType": item.get("experimentType", "N/A"),
                "manufacturer": manufacturer_name,
                "schema_properties": schema_properties
            })
        return prepared_items

    def generate_preview_html(self):
        root = self.processor.root
        if not root:
            return "<html><body>Error: Could not find root dataset node in RO-Crate.</body></html>"

        title = root.get("name", "Untitled RO-Crate")
        id_value = root.get("@id", "")
        version = root.get("version", "")
        description = root.get("description", "")
        doi = root.get("identifier", "")
        license_value = root.get("license", "")

        release_date = root.get("datePublished", "")
        created_date = root.get("dateCreated", "")
        updated_date = root.get("dateModified", "")

        authors_raw = root.get("author", [])
        authors = ""
        author_names = []
        if isinstance(authors_raw, list):
             for a in authors_raw:
                 if isinstance(a, dict):
                     author_names.append(a.get("name", "Unknown Author"))
                 elif isinstance(a, str):
                     author_names.append(a)
        elif isinstance(authors_raw, dict):
             authors = authors_raw.get("name", "Unknown Author")
        elif isinstance(authors_raw, str):
             authors = authors_raw
        if author_names:
             authors = ", ".join(filter(None, author_names))

        publisher_raw = root.get("publisher", "")
        publisher = ""
        if isinstance(publisher_raw, dict):
            publisher = publisher_raw.get("name", "")
        elif isinstance(publisher_raw, str):
            publisher = publisher_raw

        keywords_raw = root.get("keywords", [])
        keywords = []
        if isinstance(keywords_raw, list):
            keywords = [str(kw) for kw in keywords_raw if kw]
        elif isinstance(keywords_raw, str):
             keywords = [kw.strip() for kw in keywords_raw.split(',') if kw.strip()]

        related_pubs_list = root.get("relatedPublications", [])
        associated_pubs_list = root.get("associatedPublication", [])

        if not isinstance(related_pubs_list, list):
            related_pubs_list = [related_pubs_list] if related_pubs_list else []
        if not isinstance(associated_pubs_list, list):
            associated_pubs_list = [associated_pubs_list] if associated_pubs_list else []

        combined_pubs_raw = related_pubs_list + associated_pubs_list
        related_publications = []
        seen_pubs = set()

        for pub in combined_pubs_raw:
             pub_text = ""
             if isinstance(pub, dict):
                 pub_text = pub.get("name", pub.get("@id", ""))
             elif isinstance(pub, str):
                 pub_text = pub

             if not pub_text: continue

             if pub_text not in seen_pubs:
                 related_publications.append(pub_text)
                 seen_pubs.add(pub_text)

        files, software, instruments, samples, experiments, computations, schemas, other = self.processor.categorize_items()

        datasets = files if isinstance(files, list) else []
        software_list = software if isinstance(software, list) else []
        instruments_list = instruments if isinstance(instruments, list) else []
        samples_list = samples if isinstance(samples, list) else []
        experiments_list = experiments if isinstance(experiments, list) else []
        computations_list = computations if isinstance(computations, list) else []
        schemas_list = schemas if isinstance(schemas, list) else []
        other_list = other if isinstance(other, list) else []

        context = {
            'title': title or "Untitled RO-Crate",
            'id_value': id_value or "N/A",
            'version': version or "N/A",
            'description': description or "No description provided.",
            'doi': doi or "", 
            'license_value': license_value or "", 
            'release_date': release_date or "",
            'created_date': created_date or "",
            'updated_date': updated_date or "",
            'authors': authors or "N/A",
            'publisher': publisher or "N/A",
            'principal_investigator': root.get("principalInvestigator", ""),
            'contact_email': root.get("contactEmail", ""),
            'confidentiality_level': root.get("confidentialityLevel", ""),
            'keywords': keywords, 
            'citation': root.get("citation", ""),
            'related_publications': related_publications,
            'datasets': self._prepare_item_data(datasets),
            'software': self._prepare_item_data(software_list),
            'computations': self._prepare_item_data(computations_list),
            'samples': self._prepare_item_data(samples_list),
            'experiments': self._prepare_item_data(experiments_list),
            'instruments': self._prepare_item_data(instruments_list),
            'schemas': self._prepare_item_data(schemas_list),
            'other_items': self._prepare_item_data(other_list)
        }

        return self.template_engine.render(self.DEFAULT_TEMPLATE, **context)

    def save_preview_html(self, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.base_dir, "ro-crate-preview.html")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        html_content = self.generate_preview_html()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path
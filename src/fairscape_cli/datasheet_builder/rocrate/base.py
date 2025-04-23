from collections import Counter
import json
import os
from fairscape_cli.datasheet_builder.rocrate import prov


class ROCrateProcessor:
    """Base class for processing RO-Crate data"""
    
    def __init__(self, json_data=None, json_path=None, published=False):
        """Initialize with either JSON data or a path to a JSON file"""
        if json_data:
            self.json_data = json_data
        elif json_path:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
        else:
            raise ValueError("Either json_data or json_path must be provided")
        
        self.graph = self.json_data.get("@graph", [])
        self.root = self.find_root_node()
        self.published = published
    
    def find_root_node(self):
        """Find the root node in the RO-Crate graph"""
        for item in self.graph:
            if "@type" in item:
                if isinstance(item["@type"], list) and "Dataset" in item["@type"] and "https://w3id.org/EVI#ROCrate" in item["@type"]:
                    return item
                elif item["@type"] == "Dataset" or "ROCrate" in item["@type"]:
                    return item
        
        for item in self.graph:
            if "@id" in item and not item["@id"].endswith("metadata.json"):
                return item
        
        return self.graph[1] if self.graph else {}
    
    def find_subcrates(self):
        """Find sub-crates referenced in the RO-Crate"""
        subcrates = []
        
        for item in self.graph:
            if "@type" in item and item != self.root:
                item_types = item["@type"] if isinstance(item["@type"], list) else [item["@type"]]
                
                if ("Dataset" in item_types and "https://w3id.org/EVI#ROCrate" in item_types) or "ROCrate" in item_types:
                    if "ro-crate-metadata" in item:
                        subcrates.append({
                            "id": item.get("@id", ""),
                            "name": item.get("name", "Unnamed Sub-Crate"),
                            "description": item.get("description", ""),
                            "metadata_path": item.get("ro-crate-metadata", "")
                        })
        
        return subcrates
    
    def categorize_items(self):
        """Categorize items in a graph into files, software, instruments, samples, experiments, and other"""
        files = []
        software = []
        instruments = []
        samples = []
        experiments = []
        computations = []
        schemas = []
        other = []
        
        for item in self.graph:
            if "@type" not in item:
                continue
                
            item_types = item["@type"] if isinstance(item["@type"], list) else [item["@type"]]
            
            if item == self.root or (item.get("@id", "").endswith("metadata.json")):
                continue
                
            # Skip items that are identified as subcrates
            if "ro-crate-metadata" in item:
                continue
            
            # Categorize by type
            if "Dataset" in item_types or "EVI:Dataset" in item_types or "https://w3id.org/EVI#Dataset" in item_types or item.get("metadataType") == "https://w3id.org/EVI#Dataset" or item.get("additionalType") == "Dataset":
                files.append(item)
            elif "SoftwareSourceCode" in item_types or "EVI:Software" in item_types or "Software" in item_types or "https://w3id.org/EVI#Software" in item_types or item.get("metadataType") == "https://w3id.org/EVI#Software" or item.get("additionalType") == "Software":
                software.append(item)
            elif "Instrument" in item_types or "https://w3id.org/EVI#Instrument" in item_types or item.get("metadataType") == "https://w3id.org/EVI#Instrument":
                instruments.append(item)
            elif "Sample" in item_types or "https://w3id.org/EVI#Sample" in item_types or item.get("metadataType") == "https://w3id.org/EVI#Sample":
                samples.append(item)
            elif "Experiment" in item_types or "https://w3id.org/EVI#Experiment" in item_types or item.get("metadataType") == "https://w3id.org/EVI#Experiment":
                experiments.append(item)
            elif "Computation" in item_types or "https://w3id.org/EVI#Computation" in item_types or item.get("metadataType") == "https://w3id.org/EVI#Computation" or item.get("additionalType") == "Computation":
                computations.append(item)
            elif "Schema" in item_types or "EVI:Schema" in item_types or "https://w3id.org/EVI#Schema" in item_types:
                schemas.append(item)
            else:
                other.append(item)
        
        return files, software, instruments, samples, experiments, computations, schemas, other
    
    def get_formats_summary(self, items):
        """Get a summary of formats in a list of items"""
        formats = [item.get("format", "unknown") for item in items]
        format_counter = Counter(formats)
        return format_counter
    
    def get_access_summary(self, items):
        """Get a summary of content URL types (available, embargoed, etc.)"""
        access_types = []
        for item in items:
            content_url = item.get("contentUrl", "")
            if not content_url:
                access_types.append("No link")
            elif content_url == "Embargoed":
                access_types.append("Embargoed")
            else:
                access_types.append("Available")
        
        access_counter = Counter(access_types)
        return access_counter
    
    def get_date_range(self, items):
        """Get the date range for a list of items"""
        dates = []
        for item in items:
            date = item.get("datePublished", "")
            if not date:
                date = item.get("dateModified", "")
                if not date:
                    date = item.get("dateCreated", "")
            
            if date:
                dates.append(date)
        
        if not dates:
            return "Unknown"
        
        return f"{min(dates)} to {max(dates)}"
    
    def get_property_value(self, property_name, additional_properties=None):
        """Get a property value from root or from additionalProperty if present"""

        if property_name in self.root:
            return self.root[property_name]
        
        if additional_properties is None:
            additional_properties = self.root.get("additionalProperty", [])
            
        for prop in additional_properties:
            if prop.get("name") == property_name or prop.get("propertyID") == property_name:
                return prop.get("value", "")
        
        return ""
        
    def extract_cell_line_info(self, samples):
        """Extract cell line information from samples"""
        cell_lines = {}
        
        for sample in samples:
            # Check if sample has a direct cell line reference or derivedFrom
            ref_id = None
            if "cellLineReference" in sample and isinstance(sample["cellLineReference"], dict) and "@id" in sample["cellLineReference"]:
                ref_id = sample["cellLineReference"]["@id"]
            elif "derivedFrom" in sample and isinstance(sample["derivedFrom"], dict) and "@id" in sample["derivedFrom"]:
                ref_id = sample["derivedFrom"]["@id"]
                
            if ref_id:
                # Find the entity in the graph
                for item in self.graph:
                    if item.get("@id") == ref_id:
                        cell_info = {
                            "name": item.get("name", "Unknown"),
                            "identifier": "",
                            "organism_name": "Unknown"
                        }
                        
                        # Get CVCL identifier
                        identifiers = item.get("identifier", [])
                        if isinstance(identifiers, list):
                            for id_obj in identifiers:
                                if isinstance(id_obj, dict) and "@value" in id_obj and "CVCL" in id_obj["@value"]:
                                    cell_info["identifier"] = id_obj["@value"].split(":")[-1]
                                    break
                        
                        # Get organism name (if directly nested)
                        organism = item.get("organism", {})
                        if isinstance(organism, dict) and "name" in organism:
                            cell_info["organism_name"] = organism["name"]
                        
                        cell_lines[ref_id] = cell_info
                        break
        
        return cell_lines
        
    def extract_sample_species(self, samples):
        """Extract species information from samples by checking cell line references"""
        species = {}
        
        for sample in samples:
            scientific_name = "Unknown"
            
            # Check if sample has a cell line reference
            cell_line_ref = sample.get("cellLineReference", {})
            if cell_line_ref and isinstance(cell_line_ref, dict) and "@id" in cell_line_ref:
                cell_line_id = cell_line_ref.get("@id", "")
                
                # Find the cell line in the graph
                for item in self.graph:
                    if item.get("@id") == cell_line_id:
                        # Get organism information from the cell line
                        organism = item.get("organism", {})
                        if organism and isinstance(organism, dict):
                            org_name = organism.get("name")
                            if org_name:
                                scientific_name = org_name
                                break
            
            if scientific_name == "Unknown":
                additional_properties = sample.get("additionalProperty", [])
                for prop in additional_properties:
                    if prop.get("propertyID") == "scientific_name" and prop.get("value") != "N. A.":
                        scientific_name = prop.get("value", "")
                        break
            
            if scientific_name not in species:
                species[scientific_name] = 1
            else:
                species[scientific_name] += 1
                
        return species
        
    def extract_experiment_types(self, experiments):
        """Extract experiment types"""
        experiment_types = {}
        
        for experiment in experiments:
            exp_type = experiment.get("experimentType", "Unknown")
            
            if exp_type not in experiment_types:
                experiment_types[exp_type] = 1
            else:
                experiment_types[exp_type] += 1
        
        return experiment_types

    def get_dataset_format(self, dataset_id):
        """Get the format of a dataset by its ID"""
        for item in self.graph:
            if item.get("@id") == dataset_id:
                return item.get("format", "unknown")
        
        return "unknown"
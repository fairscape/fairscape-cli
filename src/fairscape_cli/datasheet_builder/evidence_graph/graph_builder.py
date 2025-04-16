from typing import Dict, List, Optional, Any, Union, Set
import json
import pathlib
from pathlib import Path
import click

class EvidenceNode:
    def __init__(self, id: str, type: str):
        self.id = id 
        self.type = type
        # For Computation nodes
        self.usedSoftware: Optional[List[str]] = None 
        self.usedDataset: Optional[List[str]] = None
        self.usedSample: Optional[List[str]] = None
        self.usedInstrument: Optional[List[str]] = None
        # For Dataset/Sample/Instrument nodes  
        self.generatedBy: Optional[str] = None

class EvidenceGraphJSON:
    def __init__(self, guid: str, owner: str, description: str, name: str = "Evidence Graph"):
        self.metadataType = "evi:EvidenceGraph"
        self.guid = guid
        self.owner = owner
        self.description = description
        self.name = name
        self.graph = None
    
    def build_graph(self, node_id: str, json_data: Dict[str, Any]):
        processed = set()
        self.graph = self._build_graph_recursive(node_id, json_data, processed)

    def _build_graph_recursive(self, node_id: str, json_data: Dict[str, Any], processed: Set[str]) -> Dict:
        if node_id in processed:
            return {"@id": node_id}
            
        # Find node in json data graph
        node = None
        for entity in json_data.get("@graph", []):
            if entity.get("@id") == node_id:
                node = entity
                break
                
        if not node:
            return {"@id": node_id}
            
        processed.add(node_id)
        result = self._build_base_node(node)
        
        # Determine node type based on @type
        node_type = None
        if isinstance(node.get("@type"), list):
            for type_entry in node["@type"]:
                if "Dataset" in type_entry:
                    node_type = "Dataset"
                    break
                elif "Computation" in type_entry:
                    node_type = "Computation"
                    break
                elif "Sample" in type_entry:
                    node_type = "Sample"
                    break
                elif "Instrument" in type_entry:
                    node_type = "Instrument"
                    break
                elif "Experiment" in type_entry:
                    node_type = "Experiment"
                    break
        elif isinstance(node.get("@type"), str):
            type_str = node.get("@type")
            if "Dataset" in type_str:
                node_type = "Dataset"
            elif "Computation" in type_str:
                node_type = "Computation"
            elif "Sample" in type_str:
                node_type = "Sample"
            elif "Instrument" in type_str:
                node_type = "Instrument"
            elif "Experiment" in type_str:
                node_type = "Experiment"
        
        if node_type in ["Dataset", "Sample", "Instrument"]:
            if "generatedBy" in node:
                result["generatedBy"] = self._build_computation_node(node, json_data, processed)
        elif node_type in ["Computation", "Experiment"]:
            if "usedDataset" in node:
                result["usedDataset"] = self._build_used_resources(node["usedDataset"], json_data, processed)
            if "usedSoftware" in node:
                result["usedSoftware"] = self._build_software_reference(node["usedSoftware"], json_data)
            if "usedSample" in node:
                result["usedSample"] = self._build_used_resources(node["usedSample"], json_data, processed)
            if "usedInstrument" in node:
                result["usedInstrument"] = self._build_used_resources(node["usedInstrument"], json_data, processed)
                
        return result

    def _build_base_node(self, node: Dict) -> Dict:
        return {
            "@id": node["@id"],
            "@type": node.get("@type"),
            "name": node.get("name"),
            "description": node.get("description")
        }

    def _build_computation_node(self, parent_node: Dict, json_data: Dict[str, Any], processed: Set[str]) -> Dict:
        # If generatedBy is an empty list, don't add anything
        if isinstance(parent_node["generatedBy"], list) and len(parent_node["generatedBy"]) == 0:
            return {}
            
        comp_id = None
        if isinstance(parent_node["generatedBy"], list):
            if parent_node["generatedBy"] and isinstance(parent_node["generatedBy"][0], dict):
                comp_id = parent_node["generatedBy"][0].get("@id")
        elif isinstance(parent_node["generatedBy"], dict):
            comp_id = parent_node["generatedBy"].get("@id")
        
        if not comp_id:
            return {"@id": "unknown-computation"}
            
        comp = None
        for entity in json_data.get("@graph", []):
            if entity.get("@id") == comp_id:
                comp = entity
                break
                
        if not comp:
            return {"@id": comp_id}
            
        return self._build_graph_recursive(comp_id, json_data, processed)

    def _build_used_resources(self, used_resources: Union[Dict, List], json_data: Dict[str, Any], processed: Set[str]) -> List:
        if isinstance(used_resources, dict):
            resource_id = used_resources.get("@id")
            if resource_id:
                return [self._build_graph_recursive(resource_id, json_data, processed)]
            return []
            
        if isinstance(used_resources, list):
            resources = []
            for resource in used_resources:
                if isinstance(resource, dict) and resource.get("@id"):
                    resources.append(self._build_graph_recursive(resource.get("@id"), json_data, processed))
            return resources
            
        return []

    def _build_software_reference(self, used_software: Union[Dict, List], json_data: Dict[str, Any]) -> Union[Dict, List[Dict]]:
        if isinstance(used_software, list):
            if not used_software:
                return []
                
            software_refs = []
            for sw in used_software:
                if isinstance(sw, dict) and sw.get("@id"):
                    software_id = sw.get("@id")
                    software = None
                    for entity in json_data.get("@graph", []):
                        if entity.get("@id") == software_id:
                            software = entity
                            break
                    
                    if software:
                        software_refs.append(self._build_base_node(software))
                    else:
                        software_refs.append({"@id": software_id})
            
            return software_refs
        
        elif isinstance(used_software, dict) and used_software.get("@id"):
            software_id = used_software.get("@id")
            software = None
            for entity in json_data.get("@graph", []):
                if entity.get("@id") == software_id:
                    software = entity
                    break
            
            if software:
                return self._build_base_node(software)
            return {"@id": software_id}
            
        return {"@id": "unknown-software"}
        
    def to_dict(self):
        return {
            "@type": self.metadataType,
            "@id": self.guid,
            "owner": self.owner,
            "description": self.description,
            "name": self.name,
            "@graph": self.graph
        }
        
    def save_to_file(self, file_path: Union[str, pathlib.Path]):
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

def generate_evidence_graph_from_rocrate(
    rocrate_path: Union[str, pathlib.Path], 
    output_path: Optional[Union[str, pathlib.Path]] = None,
    node_id: str = ""
) -> Dict[str, Any]:
    """
    Generate an evidence graph from an RO-Crate JSON file for a specific node ID
    
    Args:
        rocrate_path: Path to the RO-Crate metadata JSON file
        output_path: Optional path to save the evidence graph JSON
        node_id: ID of the node to start building the graph from
        
    Returns:
        The generated evidence graph as a dictionary
    """
    # Load RO-Crate data
    with open(rocrate_path, 'r') as f:
        rocrate_data = json.load(f)
        
    # Find the root entity
    root_entity = None
    for entity in rocrate_data.get("@graph", []):
        if entity.get("@id") == node_id:
            root_entity = entity
            break
            
    if not root_entity:
        raise ValueError(f"Could not find entity with ID {node_id} in RO-Crate")
    
    # Create evidence graph
    graph_id = f"{node_id}-evidence-graph"
    graph = EvidenceGraphJSON(
        guid=graph_id,
        owner=node_id,
        description=f"Evidence graph for {root_entity.get('name', 'Unknown')}",
        name=f"Evidence Graph - {root_entity.get('name', 'Unknown')}"
    )
    
    # Build the graph
    graph.build_graph(node_id, rocrate_data)
    
    # Save to file if output path provided
    if output_path:
        graph.save_to_file(output_path)
        
    return graph.to_dict()

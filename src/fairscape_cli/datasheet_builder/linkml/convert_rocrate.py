from fairscape_models.conversion.mapping.d4d import ROCRATE_TO_D4D_MAPPING
from fairscape_models.rocrate import ROCrateV1_2
import yaml
import json
from typing import Dict, Optional, Any
import pathlib



def load_rocrate_json(filepath: pathlib.Path) -> dict:
    """Load an RO-Crate JSON file and return as dictionary."""
    with filepath.open('r') as f:
        return json.load(f)


def find_root_entity(rocrate_data: dict) -> Optional[dict]:
    """Find the root dataset entity in the RO-Crate."""
    graph = rocrate_data.get("@graph", [])

    # Find the metadata descriptor to get root ID
    metadata_descriptor = None
    for entity in graph:
        if entity.get("@id") == "ro-crate-metadata.json":
            metadata_descriptor = entity
            break

    if not metadata_descriptor:
        return None

    # Get the root ID from about field
    about = metadata_descriptor.get("about", {})
    root_id = about.get("@id") if isinstance(about, dict) else about

    if not root_id:
        return None

    # Find and return the root entity
    for entity in graph:
        if entity.get("@id") == root_id:
            return entity

    return None


def apply_mapping(source_dict: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the mapping configuration to convert ROCrate data to D4D format."""
    result = {}

    for target_key, spec in mapping.items():
        value = None

        if "fixed_value" in spec:
            value = spec["fixed_value"]
        elif "source_key" in spec:
            value = source_dict.get(spec["source_key"])
            if "parser" in spec and value is not None:
                value = spec["parser"](value)
        elif "builder_func" in spec:
            value = spec["builder_func"](source_dict)

        if value is not None:
            result[target_key] = value

    return result


def convert_to_d4d_structure(d4d_flat: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert flat D4D mapping output to proper D4D YAML structure.

    The D4D schema uses nested structures for many properties,
    so this function reorganizes the flat output accordingly.
    """
    result = {}

    # Core metadata fields (direct copy)
    direct_fields = [
        'id', 'name', 'title', 'description', 'page', 'language', 'version',
        'license', 'doi', 'download_url', 'publisher', 'citation',
        'bytes', 'encoding', 'format', 'hash', 'md5', 'sha256',
        'compression', 'conforms_to', 'created_by', 'created_on',
        'last_updated_on', 'was_derived_from'
    ]

    for field in direct_fields:
        if field in d4d_flat and d4d_flat[field] is not None:
            result[field] = d4d_flat[field]

    # Keywords (should be a list)
    if 'keywords' in d4d_flat:
        keywords = d4d_flat['keywords']
        if isinstance(keywords, str):
            result['keywords'] = [k.strip() for k in keywords.split(',') if k.strip()]
        elif isinstance(keywords, list):
            result['keywords'] = keywords

    # Properties that should be lists of objects with description
    list_description_fields = {
        'purposes': 'purposes',
        'tasks': 'tasks',
        'known_biases': 'known_biases',
        'known_limitations': 'known_limitations',
        'sensitive_elements': 'sensitive_elements',
        'collection_mechanisms': 'collection_mechanisms',
        'collection_timeframes': 'collection_timeframes',
        'missing_data_documentation': 'missing_data_documentation',
        'raw_data_sources': 'raw_data_sources',
        'ethical_reviews': 'ethical_reviews',
        'human_subject_research': 'human_subject_research',
        'preprocessing_strategies': 'preprocessing_strategies',
        'labeling_strategies': 'labeling_strategies',
        'raw_sources': 'raw_sources',
        'imputation_protocols': 'imputation_protocols',
        'annotation_analyses': 'annotation_analyses',
        'machine_annotation_tools': 'machine_annotation_tools',
        'future_use_impacts': 'future_use_impacts',
        'discouraged_uses': 'discouraged_uses',
        'intended_uses': 'intended_uses',
        'prohibited_uses': 'prohibited_uses',
        'distribution_formats': 'distribution_formats',
        'creators': 'creators',
        'funders': 'funders',
    }

    for source_key, target_key in list_description_fields.items():
        if source_key in d4d_flat and d4d_flat[source_key] is not None:
            value = d4d_flat[source_key]
            if isinstance(value, list):
                # Already a list, convert each item
                result[target_key] = [
                    {'description': item} if isinstance(item, str) else item
                    for item in value
                ]
            elif isinstance(value, str):
                # Single string value - create list with one item
                result[target_key] = [{'description': value}]
            else:
                result[target_key] = value

    return result


def dict_representer(dumper, data):
    """Custom representer for ordered dictionary output."""
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


def str_representer(dumper, data):
    """Use literal block style for multiline strings."""
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


def convert_rocrate_to_d4d(root_entity: dict) -> dict:
    """Convert RO-Crate dictionary to D4D format."""
    # Apply the mapping
    d4d_flat = apply_mapping(root_entity, ROCRATE_TO_D4D_MAPPING)

    # Convert to proper D4D structure
    d4d_data = convert_to_d4d_structure(d4d_flat)

    return d4d_data

def GenerateLinkML(
    rocrateFilepath: pathlib.Path, 
    outputFilepath: pathlib.Path
    ):

    rocrateDict = load_rocrate_json(rocrateFilepath)
    rootEntity = find_root_entity(rocrateDict)

    if not rootEntity:
        raise Exception("ROOT Element Not Found")
    
    linkmlOutput = convert_rocrate_to_d4d(rootEntity)

    with outputFilepath.open('w') as yamlFile:
        yaml.dump(linkmlOutput, yamlFile)
    
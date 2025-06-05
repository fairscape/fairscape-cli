import pathlib
import json
from typing import List, Tuple, Dict, Any
from rdflib import Graph, URIRef
from rdflib.namespace import OWL

EVI_NAMESPACE = "https://w3id.org/EVI#"

def get_json_key_from_uri(uri_ref: URIRef, base_namespace: str = EVI_NAMESPACE) -> str:
    """
    Converts an RDF URI to a simple JSON key by stripping the base namespace.
    Example: URIRef("https://w3id.org/EVI#generatedBy") -> "generatedBy"
    """
    s_uri = str(uri_ref)
    if s_uri.startswith(base_namespace):
        return s_uri[len(base_namespace):]
    return s_uri.split('/')[-1].split('#')[-1]


def add_or_update_json_link(
    entity: Dict[str, Any],
    prop_key: str,
    link_id_to_add: str,
    ):
    """
    Adds or updates a linked entity (as {"@id": link_id_to_add}) to a property
    in the given entity. Handles cases where the property doesn't exist,
    is a single object, or is already a list. Avoids duplicates.

    Args:
        entity: The JSON entity (dict) to modify.
        prop_key: The JSON key for the property (e.g., "generated").
        link_id_to_add: The "@id" of the entity to link.
        print: Function to use for logging/output (defaults to click.echo).
    """
    link_obj_to_add = {"@id": link_id_to_add}

    if prop_key not in entity:
        entity[prop_key] = [link_obj_to_add]
    else:
        current_val = entity[prop_key]
        if isinstance(current_val, dict):  
            if current_val.get("@id") == link_id_to_add:
                return 
            else:
                entity[prop_key] = [current_val, link_obj_to_add]
        elif isinstance(current_val, list):  
            if not any(isinstance(item, dict) and item.get("@id") == link_id_to_add for item in current_val):
                current_val.append(link_obj_to_add)
        else:
            entity[prop_key] = [link_obj_to_add]


def augment_rocrate_with_inverses(
    rocrate_path: pathlib.Path,
    ontology_path: pathlib.Path,
    default_namespace_prefix: str = EVI_NAMESPACE
) -> bool:
    """
    Augments an RO-Crate by finding owl:inverseOf properties defined in the
    ontology and ensuring both sides of the relationship are present in the
    RO-Crate's JSON-LD metadata.

    Args:
        rocrate_path: Path to the 'ro-crate-metadata.json' file or its parent directory.
        ontology_path: Path to the OWL ontology file (e.g., EVI.owl).
        default_namespace_prefix: The base URI for properties to be treated as primary.

    Returns:
        True if augmentation was successful (or no changes needed), False otherwise.
    """
    if not ontology_path.is_file():
        return False

    # Determine the correct path to ro-crate-metadata.json
    if rocrate_path.is_dir():
        metadata_file_path = rocrate_path / "ro-crate-metadata.json"
    elif rocrate_path.name == "ro-crate-metadata.json":
        metadata_file_path = rocrate_path
    else:
        print(f"Error: Invalid rocrate-path. Must be a directory or 'ro-crate-metadata.json'. Provided: {rocrate_path}")
        return False

    if not metadata_file_path.is_file():
        print(f"Error: 'ro-crate-metadata.json' not found at {metadata_file_path}")
        return False

    # 1. Load EVI ontology
    ont_graph = Graph()
    try:
        ont_graph.parse(str(ontology_path), format="xml") 
    except Exception as e:
        print(f"Error parsing ontology {ontology_path}: {e}")
        return False

    # 2. Identify inverse property pairs from the ontology
    inverse_pairs: List[Tuple[URIRef, URIRef]] = []
    query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?prop1 ?prop2 WHERE { ?prop1 owl:inverseOf ?prop2 . }
    """
    for row in ont_graph.query(query):
        prop1, prop2 = row["prop1"], row["prop2"]
        if str(prop1) < str(prop2):
             inverse_pairs.append((prop1, prop2))
        elif (prop2,prop1) not in inverse_pairs :
             inverse_pairs.append((prop1, prop2))


    if not inverse_pairs:
        print("No owl:inverseOf property pairs found in the ontology.")
        return True

    # 3. Load RO-Crate JSON
    try:
        with open(metadata_file_path, 'r') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"Error loading RO-Crate JSON from {metadata_file_path}: {e}")
        return False

    if "@graph" not in json_data or not isinstance(json_data["@graph"], list):
        print("Error: RO-Crate JSON does not have a valid '@graph' list.")
        return False

    entity_map: Dict[str, Dict[str, Any]] = {
        entity['@id']: entity
        for entity in json_data['@graph']
        if isinstance(entity, dict) and '@id' in entity
    }

    modified_count = 0

    # 4. Iterate and augment based on inverse pairs
    for prop1_uri, prop2_uri in inverse_pairs:
        # Determine JSON keys. Prioritize default_namespace_prefix.
        json_prop1_key = get_json_key_from_uri(prop1_uri, default_namespace_prefix)
        json_prop2_key = get_json_key_from_uri(prop2_uri, default_namespace_prefix)

        for entity_id, source_entity in list(entity_map.items()):
            source_entity_id = source_entity.get("@id")
            if not source_entity_id:
                continue

            # Check forward direction (prop1_uri exists on source_entity)
            if json_prop1_key in source_entity:
                values = source_entity[json_prop1_key]
                if not isinstance(values, list):
                    values = [values] 

                for val_obj in values:
                    if isinstance(val_obj, dict) and "@id" in val_obj:
                        target_id = val_obj["@id"]
                        if target_id in entity_map:
                            target_entity = entity_map[target_id]
                            original_target_prop_val = target_entity.get(json_prop2_key)
                            if original_target_prop_val is not None:
                                original_target_prop_val = json.dumps(original_target_prop_val, sort_keys=True)

                            add_or_update_json_link(target_entity, json_prop2_key, source_entity_id)

                            new_target_prop_val = target_entity.get(json_prop2_key)
                            if new_target_prop_val is not None:
                                new_target_prop_val = json.dumps(new_target_prop_val, sort_keys=True)

                            if original_target_prop_val != new_target_prop_val:
                                modified_count +=1
                        else:
                            print(f"Warning: Dangling reference. Entity '{source_entity_id}' "
                                           f"property '{json_prop1_key}' points to non-existent '@id': '{target_id}'.")

            # Check reverse direction (prop2_uri exists on source_entity)
            if json_prop2_key in source_entity:
                values = source_entity[json_prop2_key]
                if not isinstance(values, list):
                    values = [values] 

                for val_obj in values:
                    if isinstance(val_obj, dict) and "@id" in val_obj:
                        target_id = val_obj["@id"]
                        if target_id in entity_map:
                            target_entity = entity_map[target_id]
                            original_target_prop_val = target_entity.get(json_prop1_key)
                            if original_target_prop_val is not None:
                                original_target_prop_val = json.dumps(original_target_prop_val, sort_keys=True)

                            add_or_update_json_link(target_entity, json_prop1_key, source_entity_id)

                            new_target_prop_val = target_entity.get(json_prop1_key)
                            if new_target_prop_val is not None:
                                new_target_prop_val = json.dumps(new_target_prop_val, sort_keys=True)

                            if original_target_prop_val != new_target_prop_val:
                                modified_count +=1
                        else:
                            print(f"Warning: Dangling reference. Entity '{source_entity_id}' "
                                           f"property '{json_prop2_key}' points to non-existent '@id': '{target_id}'.")
    if modified_count > 0:
        try:
            with open(metadata_file_path, 'w') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print(f"RO-Crate '{metadata_file_path}' augmented with inverse properties. {modified_count} modifications made.")
        except Exception as e:
            print(f"Error saving augmented RO-Crate JSON to {metadata_file_path}: {e}")
            return False
    else:
        print(f"No inverse properties needed to be added or RO-Crate '{metadata_file_path}' is already consistent.")

    return True
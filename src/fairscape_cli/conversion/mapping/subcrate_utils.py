import html
import re
from typing import Any, Dict, List, Optional, Set
from fairscape_cli.conversion.models.FairscapeDatasheet import CompositionDetails
from collections import Counter

# Computation/experiment patterns render as a small "equation": input RO-Crates combine to
# make an output. These build the HTML fragments (rendered with the Jinja `| safe` filter);
# all dynamic text is html-escaped here.
_ARROW = '<strong>&rarr;</strong>'


def _fmt_tokens(fmt: str) -> str:
    """Escape a (possibly comma-joined) format string and join its parts with ' + '."""
    return ' + '.join(html.escape(p.strip()) for p in fmt.split(',') if p.strip())


def _input_fragment(rocrate_name: Optional[str], fmt: str) -> str:
    """One input term: '**RO-Crate name**: fmt' when cross-crate, else just the format(s)."""
    fmt_disp = _fmt_tokens(fmt)
    if rocrate_name:
        return f"<strong>{html.escape(rocrate_name)}</strong>: {fmt_disp}"
    return fmt_disp


def normalize_formats(raw) -> List[str]:
    """Canonicalize a raw format value (str or list) into dotless, lowercase tokens.

    Splits combined values on ``/ , ;`` (e.g. ".cx / .tsv" -> ["cx", "tsv"]), strips
    surrounding whitespace and a leading dot, lowercases, and drops empty/"unknown"
    tokens. This collapses redundant variants like "tsv" / ".tsv" / "TSV" to a single
    canonical "tsv" so the datasheet doesn't list the same format multiple times.
    """
    out: List[str] = []
    for item in (raw if isinstance(raw, list) else [raw]):
        if not isinstance(item, str):
            continue
        for part in re.split(r'[\/,;]', item):
            tok = part.strip().lstrip('.').strip().lower()
            if tok and tok != "unknown":
                out.append(tok)
    return out


def _normalize_format_str(raw) -> str:
    """Return the normalized format token(s) for a single entity as one display string.

    Joins multiple canonical tokens with ", " and returns "unknown" when nothing usable
    remains, so callers that gate on ``!= "unknown"`` keep working.
    """
    tokens = normalize_formats(raw)
    return ", ".join(tokens) if tokens else "unknown"

def build_composition_details(converter_instance, source_entity_model) -> CompositionDetails:
    graph = converter_instance.source_crate.metadataGraph
    global_index = converter_instance.global_index
    
    details = CompositionDetails()
    
    file_formats = []
    model_formats = []
    software_formats = []
    file_access_types = []
    software_access_types = []
    computation_patterns = []
    experiment_patterns = []
    cell_lines = {}
    species_counts = Counter()
    experiment_types_counts = Counter()
    
    for item in graph:
        if item.guid == "ro-crate-metadata.json":
            continue
            
        if hasattr(item, 'ro_crate_metadata'):
            continue
            
        item_type = _normalize_type(item)
        
        if item_type == "Dataset":
            details.files_count += 1
            if _has_provenance(item):
                details.datasets_with_provenance_count += 1
            _process_dataset(item, file_formats, file_access_types)
            
        elif item_type == "MLModel":
            details.models_count += 1
            _process_dataset(item, model_formats, file_access_types)

        elif item_type == "Software":
            details.software_count += 1
            _process_software(item, software_formats, software_access_types)
            
        elif item_type == "Instrument":
            details.instruments_count += 1
            
        elif item_type == "Sample":
            details.samples_count += 1
            _process_sample(item, cell_lines, species_counts, global_index)
            
        elif item_type == "Experiment":
            details.experiments_count += 1
            pattern = _extract_experiment_pattern(item, global_index)
            if pattern:
                experiment_patterns.append(pattern)
            _process_experiment_type(item, experiment_types_counts)
            
        elif item_type == "Computation":
            details.computations_count += 1
            pattern = _extract_computation_pattern(item, global_index)
            if pattern:
                computation_patterns.append(pattern)
                
        elif item_type == "Schema":
            details.schemas_count += 1
            
        else:
            details.other_count += 1
    
    # Drop blank/unknown formats so the Files card only lists real formats.
    details.file_formats = {fmt: count for fmt, count in Counter(file_formats).items() if fmt and fmt != "unknown"}
    details.model_formats = {fmt: count for fmt, count in Counter(model_formats).items() if fmt and fmt != "unknown"}
    details.software_formats = {fmt: count for fmt, count in Counter(software_formats).items() if fmt and fmt != "unknown"}
    details.file_access = dict(Counter(file_access_types))
    details.software_access = dict(Counter(software_access_types))
    details.computation_patterns = list(set(computation_patterns))
    details.experiment_patterns = list(set(experiment_patterns))
    details.cell_lines = cell_lines
    details.species = [f"{species} ({count})" for species, count in species_counts.items()]
    details.experiment_types = dict(experiment_types_counts)
    
    input_dataset_counts = _calculate_input_datasets(graph[1], global_index)
    details.input_datasets = input_dataset_counts
    details.input_datasets_count = sum(input_dataset_counts.values())
    details.inputs_count = details.samples_count + details.input_datasets_count
    
    return details


# Provenance link keys, in the forms they appear on parsed graph entities: the EVI
# generatedBy field (https://w3id.org/EVI#generatedBy) parsed or raw, and PROV-O
# prov:wasGeneratedBy (http://www.w3.org/ns/prov#wasGeneratedBy) aliased or raw.
_PROVENANCE_KEYS = (
    'generatedBy',
    'EVI:generatedBy',
    'evi:generatedBy',
    'https://w3id.org/EVI#generatedBy',
    'wasGeneratedBy',
    'prov:wasGeneratedBy',
    'http://www.w3.org/ns/prov#wasGeneratedBy',
)


def _has_provenance(item) -> bool:
    return any(getattr(item, key, None) for key in _PROVENANCE_KEYS)


def _normalize_type(item) -> str:
    type_field = getattr(item, 'metadataType', None) or getattr(item, '@type', None)
    
    if not type_field:
        return "Other"
    
    if isinstance(type_field, list):
        type_str = " ".join(type_field)
    else:
        type_str = str(type_field)
    
    if "MLModel" in type_str:
        return "MLModel"
    elif "Dataset" in type_str or "EVI:Dataset" in type_str or "https://w3id.org/EVI#Dataset" in type_str:
        return "Dataset"
    elif "Software" in type_str or "EVI:Software" in type_str or "https://w3id.org/EVI#Software" in type_str or "SoftwareSourceCode" in type_str:
        return "Software"
    elif "Instrument" in type_str or "https://w3id.org/EVI#Instrument" in type_str or "EVI:Instrument" in type_str:
        return "Instrument"
    elif "Sample" in type_str or "https://w3id.org/EVI#Sample" in type_str or "EVI:Sample" in type_str:
        return "Sample"
    elif "Experiment" in type_str or "https://w3id.org/EVI#Experiment" in type_str or "EVI:Experiment" in type_str:
        return "Experiment"
    elif "Computation" in type_str or "https://w3id.org/EVI#Computation" in type_str or "EVI:Computation" in type_str:
        return "Computation"
    elif "Schema" in type_str or "EVI:Schema" in type_str or "https://w3id.org/EVI#Schema" in type_str:
        return "Schema"
    else:
        return "Other"


def _process_dataset(item, formats: List[str], access_types: List[str]):
    format_val = getattr(item, 'fileFormat', 'unknown')
    formats.extend(normalize_formats(format_val))
    
    content_url = getattr(item, 'contentUrl', '')
    if not content_url:
        access_types.append("No link")
    elif content_url == "Embargoed":
        access_types.append("Embargoed")
    else:
        access_types.append("Available")


def _process_software(item, formats: List[str], access_types: List[str]):
    format_val = getattr(item, 'fileFormat', 'unknown')
    formats.extend(normalize_formats(format_val))
    
    content_url = getattr(item, 'contentUrl', '')
    if not content_url:
        access_types.append("No link")
    elif content_url == "Embargoed":
        access_types.append("Embargoed")
    else:
        access_types.append("Available")


def _process_sample(item, cell_lines: Dict[str, Dict], species_counts: Counter, global_index: Dict[str, Any]):
    cell_line_ref = getattr(item, 'cellLineReference', None) or getattr(item, 'derivedFrom', None)
    if cell_line_ref:  
        if hasattr(cell_line_ref, 'guid'):
            ref_id = cell_line_ref.guid
        else:
            ref_id = cell_line_ref.get("@id","")
        cell_line_details = global_index.get(ref_id, {})
        
        if ref_id not in cell_lines:
            organism_name = "Unknown"
            if cell_line_details.get("organism", {}).get("name", ""):
                organism_name = cell_line_details["organism"]["name"]
            
            cell_lines[ref_id] = {
                'name': cell_line_details.get('name', ref_id),
                'organism_name': organism_name,
                'identifier': ref_id
            }
            
        scientific_name = cell_lines[ref_id]['organism_name']
    else:
        scientific_name = "Unknown"

    species_counts[scientific_name] += 1


def _process_experiment_type(item, experiment_types_counts: Counter):
    exp_type = getattr(item, 'experimentType', 'Unknown')
    experiment_types_counts[exp_type] += 1


def _extract_experiment_pattern(item, global_index: Dict[str, Any]) -> Optional[str]:
    output_formats = []
    
    generated = getattr(item, 'generated', [])
    if generated:
        if not isinstance(generated, list):
            generated = [generated]
            
        for dataset_ref in generated:
            dataset_id = _get_ref_id(dataset_ref)
            if dataset_id:
                format_val = _normalize_format_str(_lookup_format(dataset_id, global_index))
                if format_val and format_val != "unknown":
                    output_formats.append(format_val)

    if output_formats:
        output_str = " + ".join(sorted(set(_fmt_tokens(f) for f in output_formats)))
        return f"Sample {_ARROW} {output_str}"

    return None


def _extract_computation_pattern(item, global_index: Dict[str, Any]) -> Optional[str]:
    input_formats = []
    output_formats = []
    
    current_rocrate_name = None
    if hasattr(item, 'guid'):
        item_id = item.guid
        if item_id in global_index:
            current_rocrate_name = global_index[item_id].get('rocrateName')
    
    used_datasets = getattr(item, 'usedDataset', [])
    if used_datasets:
        if not isinstance(used_datasets, list):
            used_datasets = [used_datasets]
            
        for dataset_ref in used_datasets:
            dataset_id = _get_ref_id(dataset_ref)
            if dataset_id and dataset_id in global_index:
                dataset_info = global_index[dataset_id]
                format_val = _normalize_format_str(dataset_info.get('fileFormat', 'unknown'))
                dataset_rocrate_name = dataset_info.get('rocrateName')
                
                if format_val and format_val != "unknown":
                    if dataset_rocrate_name and dataset_rocrate_name != current_rocrate_name:
                        input_formats.append(_input_fragment(dataset_rocrate_name, format_val))
                    else:
                        input_formats.append(_input_fragment(None, format_val))
    
    generated = getattr(item, 'generated', [])
    if generated:
        if not isinstance(generated, list):
            generated = [generated]
            
        for dataset_ref in generated:
            dataset_id = _get_ref_id(dataset_ref)
            if dataset_id:
                format_val = _normalize_format_str(_lookup_format(dataset_id, global_index))
                if format_val and format_val != "unknown":
                    output_formats.append(format_val)

    if input_formats and output_formats:
        input_str = " + ".join(sorted(set(input_formats)))
        output_str = " + ".join(sorted(set(_fmt_tokens(f) for f in output_formats)))
        return f"{input_str} {_ARROW} {output_str}"

    return None


def _get_ref_id(ref) -> Optional[str]:
    if isinstance(ref, dict):
        return ref.get('@id') or ref.get('guid')
    elif isinstance(ref, str):
        return ref
    elif hasattr(ref, 'guid'):
        return ref.guid
    return None


def _lookup_format(dataset_id: str, global_index: Dict[str, Any]) -> str:
    if dataset_id in global_index:
        entity_info = global_index[dataset_id]
        return entity_info.get('fileFormat', 'unknown')
    return 'unknown'


def _resolve_ref_entry(ref, global_index: Dict[str, Any], current_rocrate_name: Optional[str] = None,
                       include_format: bool = True) -> Optional[Dict[str, Any]]:
    """Resolve one usedDataset/generated/usedSoftware ref into {id, name, format[, crate]}.

    Unresolvable refs fall back to the raw @id as the name so no input/output is dropped.
    ``crate`` is set only when the referenced entity lives in a different RO-Crate than
    the computation (same convention as _extract_computation_pattern).
    """
    ref_id = _get_ref_id(ref)
    if not ref_id:
        return None
    info = global_index.get(ref_id)
    entry: Dict[str, Any] = {
        'id': ref_id,
        'name': (info.get('name') if info else None) or ref_id,
    }
    if include_format:
        fmt = _normalize_format_str(info.get('fileFormat', 'unknown')) if info else 'unknown'
        entry['format'] = fmt if fmt != 'unknown' else None
        ref_crate = info.get('rocrateName') if info else None
        entry['crate'] = ref_crate if ref_crate and ref_crate != current_rocrate_name else None
    return entry


def _as_ref_list(refs) -> List[Any]:
    if not refs:
        return []
    return refs if isinstance(refs, list) else [refs]


def extract_computation_details(item, global_index: Dict[str, Any]) -> Dict[str, Any]:
    """Structured provenance for one Computation: source crate, inputs, outputs, software, command.

    Unlike _extract_computation_pattern (which reduces to a 'format -> format' string), this
    keeps names and @ids so the preview can render an expandable details view.
    """
    guid = getattr(item, 'guid', None)
    source_crate = None
    if guid and guid in global_index:
        source_crate = global_index[guid].get('rocrateName')

    command = getattr(item, 'command', None)
    if isinstance(command, list):
        command = ' '.join(str(part) for part in command)

    details: Dict[str, Any] = {
        'id': guid,
        'source_crate': source_crate,
        'command': command or None,
        'inputs': [],
        'outputs': [],
        'software': [],
    }

    for ref in _as_ref_list(getattr(item, 'usedDataset', None)):
        entry = _resolve_ref_entry(ref, global_index, source_crate)
        if entry:
            details['inputs'].append(entry)

    for ref in _as_ref_list(getattr(item, 'generated', None)):
        entry = _resolve_ref_entry(ref, global_index, source_crate)
        if entry:
            details['outputs'].append(entry)

    for ref in _as_ref_list(getattr(item, 'usedSoftware', None)):
        entry = _resolve_ref_entry(ref, global_index, source_crate, include_format=False)
        if entry:
            details['software'].append(entry)

    return details


def enrich_preview_computations(preview, source_crate, global_index: Dict[str, Any]) -> None:
    """Attach extract_computation_details() output to each computation PreviewItem.

    PreviewItem allows extra fields, so details land on ``item.computation_details``
    without a schema change. Safe to call with a bare per-crate index (no rocrateName
    stamps): names/formats still resolve within the crate.
    """
    if not preview or not getattr(preview, 'computations', None):
        return

    items_by_id = {item.id: item for item in preview.computations if getattr(item, 'id', None)}
    for entity in source_crate.metadataGraph:
        if _normalize_type(entity) != "Computation":
            continue
        target = items_by_id.get(getattr(entity, 'guid', None))
        if target is not None:
            target.computation_details = extract_computation_details(entity, global_index)


def _calculate_input_datasets(root_dataset, global_index: Dict[str, Any]) -> Dict[str, int]:
    input_counts = Counter()
    
    evi_inputs = getattr(root_dataset, 'EVI:inputs', None) or getattr(root_dataset, 'https://w3id.org/EVI#inputs', None) or getattr(root_dataset, 'inputs', None)
    
    if not isinstance(evi_inputs, list):
        evi_inputs = [evi_inputs]
    
    for input_ref in evi_inputs:
        input_id = _get_ref_id(input_ref)
        if not input_id:
            continue
        
        if input_id in global_index:
            entity_info = global_index[input_id]
            
            entity_type = entity_info.get('@type', entity_info.get('metadataType', ''))
            is_rocrate = False
            if isinstance(entity_type, list):
                is_rocrate = any('ROCrate' in str(t) for t in entity_type)
            else:
                is_rocrate = 'ROCrate' in str(entity_type)
            
            if is_rocrate:
                outputs = entity_info.get('https://w3id.org/EVI#outputs', entity_info.get('EVI:outputs', entity_info.get('outputs', [])))
                if not isinstance(outputs, list):
                    outputs = [outputs] if outputs else []
                
                rocrate_name = entity_info.get('name', 'Unknown RO-Crate')
                
                for output_ref in outputs:
                    output_id = _get_ref_id(output_ref)
                    if output_id and output_id in global_index:
                        output_info = global_index[output_id]
                        format_val = _normalize_format_str(output_info.get('fileFormat', 'unknown'))
                        key = f"{rocrate_name} ({format_val})"
                        input_counts[key] += 1
            else:
                format_val = _normalize_format_str(entity_info.get('fileFormat', 'unknown'))
                if format_val == 'unknown':
                    format_val = 'Sample'
                    
                rocrate_name = entity_info.get('rocrateName', '')
                
                if rocrate_name and rocrate_name != root_dataset.name:
                    key = f"{rocrate_name} ({format_val})"
                else:
                    key = format_val
                
                input_counts[key] += 1
        else:
            input_counts['unknown'] += 1
    
    return dict(input_counts)
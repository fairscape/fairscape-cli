from typing import Any, Dict, List, Optional, Union 
from fairscape_cli.conversion.models.FairscapeDatasheet import OverviewSection, UseCasesSection, DistributionSection, SubCrateItem, Preview, PreviewItem
from fairscape_cli.conversion.mapping.subcrate_utils import build_composition_details
from fairscape_models.conversion.converter import ROCToTargetConverter

def _as_list_str(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        sep = ';' if ';' in value else ','
        return [p.strip() for p in value.split(sep) if p.strip()]
    if isinstance(value, list):
        out: List[str] = []
        for v in value:
            if isinstance(v, str):
                s = v.strip()
                if s:
                    out.append(s)
        return out
    return []

def _related_publications(value: Any) -> List[str]:
    items = value if isinstance(value, list) else ([] if value is None else [value])
    out, seen = [], set()
    for it in items:
        if isinstance(it, dict):
            s = it.get("name") or it.get("@id") or it.get("identifier") or ""
        else:
            s = str(it or "")
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out

def _list_to_str(value: Any) -> str:
    if isinstance(value, list):
        return ', '.join(str(v).strip() for v in value if str(v).strip())
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ''
    return str(value).strip()

def _list_to_str_hyphen(value: Any) -> str:
    if isinstance(value, list):
        return '- '.join(str(v).strip() for v in value if str(v).strip())
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ''
    return str(value).strip()

def from_additional_property(name: str, default: Optional[str] = None):
    def _parser(prop_list: Any) -> Optional[str]:
        if isinstance(prop_list, list):
            for p in prop_list:
                if isinstance(p, dict) and p.get("name") == name:
                    val = p.get("value")
                    return str(val) if val is not None else default
        return default
    return _parser

def _bool_to_yes_no(value: Any) -> str:
    """Convert a boolean to 'Yes'/'No' string for display."""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)

def _irb_passthrough(value: Any) -> Any:
    """Pass IRB value through as-is — string or dict (structured IRB)."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return value
    return None

def _extract_id(value: Any) -> Optional[str]:
    if isinstance(value, dict):
        return value.get("@id")
    return None

def _resolve_authors(converter_instance, source_entity_model) -> List[str]:
    """Resolve the root crate's author field into an ordered list of name strings.

    Authors may be plain name strings or reference stubs ({"@id": "..."}) that
    point to Person entities elsewhere in the @graph (e.g. ORCID URIs). Plain
    strings are kept as-is; reference stubs are resolved to the referenced
    entity's name. References that cannot be resolved from the @graph are
    skipped so they are not dropped silently as blanks.
    """
    raw = source_entity_model.model_dump(by_alias=True).get("author")
    if raw is None:
        return []

    # Build a guid -> name index from the @graph.
    name_by_id: Dict[str, str] = {}
    for item in converter_instance.source_crate.metadataGraph:
        guid = getattr(item, "guid", None)
        name = getattr(item, "name", None)
        if guid and name:
            name_by_id[guid] = name

    entries = raw if isinstance(raw, list) else [raw]
    resolved: List[str] = []
    for entry in entries:
        if isinstance(entry, str):
            s = entry.strip()
            if s:
                resolved.append(s)
        elif isinstance(entry, dict):
            # Inline Person object carries its own name.
            inline_name = entry.get("name")
            if isinstance(inline_name, str) and inline_name.strip():
                resolved.append(inline_name.strip())
                continue
            ref_id = entry.get("@id")
            if ref_id and ref_id in name_by_id:
                resolved.append(name_by_id[ref_id])
            # Unresolved reference: skip per spec (no external lookup).
    return resolved

OVERVIEW_MAPPING: Dict[str, Dict[str, Any]] = {
    
    # identity
    "title":                 {"source_key": "name"},
    "description":           {"source_key": "description"},
    "id_value":              {"source_key": "@id"},
    "doi":                   {"source_key": "identifier"},
    "license_value":         {"source_key": "license"},
    "ethical_review":        {"source_key": "ethicalReview"},

    # dates
    "release_date":          {"source_key": "datePublished"},
    "created_date":          {"source_key": "dateCreated"},
    "updated_date":          {"source_key": "dateModified"},

    # people/orgs
    "authors":               {"builder_func": _resolve_authors},
    "publisher":             {"source_key": "publisher"},
    "principal_investigator":{"source_key": "principalInvestigator"},
    "contact_email":         {"source_key": "contactEmail"},

    # legal/policy
    "copyright":             {"source_key": "copyrightNotice"},
    "terms_of_use":          {"source_key": "conditionsOfAccess"},
    "confidentiality_level": {"source_key": "confidentialityLevel"},
    "citation":              {"source_key": "citation"},

    # versioning / misc
    "version":               {"source_key": "version"},
    "content_size":          {"source_key": "contentSize"},
    "funding":               {"source_key": "funder", "parser": _as_list_str},
    "keywords":              {"source_key": "keywords"},

    # human-subjects & governance — top-level fields with additionalProperty fallback
    "human_subject_research":   {"source_key": "humanSubjectResearch",   "fallback_source_key": "additionalProperty", "fallback_parser": from_additional_property("Human Subject Research", "")},
    "human_subject_exemptions": {"source_key": "humanSubjectExemption",  "fallback_source_key": "additionalProperty", "fallback_parser": from_additional_property("Human Subjects Exemptions", "")},
    "deidentified_samples":     {"source_key": "deidentified", "parser": _bool_to_yes_no, "fallback_source_key": "additionalProperty", "fallback_parser": from_additional_property("De-identified Samples", "")},
    "fda_regulated":            {"source_key": "fdaRegulated", "parser": _bool_to_yes_no, "fallback_source_key": "additionalProperty", "fallback_parser": from_additional_property("FDA Regulated", "")},
    "irb":                      {"source_key": "irb", "parser": _irb_passthrough, "fallback_source_key": "additionalProperty", "fallback_parser": from_additional_property("IRB", "")},
    "irb_protocol_id":          {"source_key": "irbProtocolId",          "fallback_source_key": "additionalProperty", "fallback_parser": from_additional_property("IRB Protocol ID", "")},
    "data_governance":          {"source_key": "dataGovernanceCommittee","fallback_source_key": "additionalProperty", "fallback_parser": from_additional_property("Data Governance Committee")},
    "completeness":             {"source_key": "completeness",           "fallback_source_key": "additionalProperty", "fallback_parser": from_additional_property("Completeness")},

    # related pubs
    "related_publications":        {"source_key": "associatedPublication", "parser": _related_publications},
}

OVERVIEW_MAPPING_CONFIGURATION = {
    "entity_map": {
        # Map the RO-Crate root directly to OverviewSection
        ("ROCrateMetadataElem", "ROOT"): {
            "target_class": OverviewSection,
            "mapping_def": OVERVIEW_MAPPING,
        },
        # no component mappings
        ("Dataset", "COMPONENT"): None,
        ("Schema", "COMPONENT"): None,
        ("Software", "COMPONENT"): None,
        ("Computation", "COMPONENT"): None,
    },
    "sub_mappings": {},
    "assembly_instructions": [],
}


USECASES_MAPPING = {
    "intended_use":          {"source_key": "rai:dataUseCases", "parser": _list_to_str},
    "limitations":           {"source_key": "rai:dataLimitations", "parser": _list_to_str},
    "prohibited_uses":        {"source_key": "prohibitedUses", "fallback_source_key": "additionalProperty", "fallback_parser": from_additional_property("Prohibited Uses")},
    "potential_sources_of_bias": {"source_key": "rai:dataBiases", "parser": _list_to_str},
    "maintenance_plan":      {"source_key": "rai:dataReleaseMaintenancePlan"},

    # Additional RAI fields
    "data_collection":              {"source_key": "rai:dataCollection"},
    "data_collection_type":         {"source_key": "rai:dataCollectionType", "parser": _list_to_str},
    "data_collection_missing_data": {"source_key": "rai:dataCollectionMissingData"},
    "data_collection_raw_data":     {"source_key": "rai:dataCollectionRawData"},
    "data_collection_timeframe":    {"source_key": "rai:dataCollectionTimeframe", "parser": _list_to_str_hyphen},
    "data_imputation_protocol":     {"source_key": "rai:dataImputationProtocol"},
    "data_manipulation_protocol":   {"source_key": "rai:dataManipulationProtocol"},
    "data_preprocessing_protocol":  {"source_key": "rai:dataPreprocessingProtocol", "parser": _list_to_str},
    "data_annotation_protocol":     {"source_key": "rai:dataAnnotationProtocol"},
    "data_annotation_platform":     {"source_key": "rai:dataAnnotationPlatform", "parser": _list_to_str},
    "data_annotation_analysis":     {"source_key": "rai:dataAnnotationAnalysis", "parser": _list_to_str},
    "personal_sensitive_information": {"source_key": "rai:personalSensitiveInformation", "parser": _list_to_str},
    "data_social_impact":           {"source_key": "rai:dataSocialImpact"},
    "annotations_per_item":         {"source_key": "rai:annotationsPerItem"},
    "annotator_demographics":       {"source_key": "rai:annotatorDemographics", "parser": _list_to_str},
    "machine_annotation_tools":     {"source_key": "rai:machineAnnotationTools", "parser": _list_to_str},
}

USECASES_MAPPING_CONFIGURATION = {
    "entity_map": {
        ("ROCrateMetadataElem", "ROOT"): {
            "target_class": UseCasesSection,
            "mapping_def": USECASES_MAPPING,
        },
    },
    "sub_mappings": {},
    "assembly_instructions": [],
}

DISTRIBUTION_MAPPING = {
    "license_value": {"source_key": "license"},
    "publisher":     {"source_key": "publisher"},
    "doi":           {"source_key": "doi"},
    "release_date":  {"source_key": "datePublished"},
    "version":       {"source_key": "version"},
}

DISTRIBUTION_MAPPING_CONFIGURATION = {
    "entity_map": {
        ("ROCrateMetadataElem", "ROOT"): {
            "target_class": DistributionSection,
            "mapping_def": DISTRIBUTION_MAPPING,
        },
    },
    "sub_mappings": {},
    "assembly_instructions": [],
}


SUBCRATE_MAPPING = {
    # direct mappings
    "name": {"source_key": "name"},
    "id": {"source_key": "@id"},
    "description": {"source_key": "description"},
    "authors": {"source_key": "author", "parser": _list_to_str},
    "keywords": {"source_key": "keywords"},
    "metadata_path": {"source_key": "metadata_path"},
    "size": {"source_key": "contentSize"},
    "doi": {"source_key": "identifier"},
    "date": {"source_key": "datePublished"},
    "contact": {"source_key": "contactEmail"},
    "published": {"source_key": "published"},
    "copyright": {"source_key": "copyrightNotice"},
    "license": {"source_key": "license"},
    "terms_of_use": {"source_key": "conditionsOfAccess"},
    "confidentiality": {"source_key": "confidentialityLevel"},
    "funder": {"source_key": "funder"},
    "md5": {"source_key": "MD5"},
    "evidence": {"source_key": "localEvidenceGraph", "parser": _extract_id},

    "composition_details": {"builder_func": build_composition_details},

    # publications
    "related_publications":        {"source_key": "associatedPublication", "parser": _related_publications},
}


SUBCRATE_MAPPING_CONFIGURATION = {
    "entity_map": {
        ("ROCrateMetadataElem", "ROOT"): {
            "target_class": SubCrateItem,
            "mapping_def": SUBCRATE_MAPPING,
        },
    },
    "sub_mappings": {},
    "assembly_instructions": [],
}


def _keywords_as_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        sep = ';' if ';' in v else ','
        return [p.strip() for p in v.split(sep) if p.strip()]
    return []

def _join_authors(value: Any) -> Optional[str]:
    names: List[str] = []
    if isinstance(value, list):
        for v in value:
            if isinstance(v, dict):
                n = v.get("name")
                if n:
                    names.append(str(n))
            elif isinstance(v, str):
                if v.strip():
                    names.append(v.strip())
    elif isinstance(value, dict):
        n = value.get("name")
        if n:
            names.append(str(n))
    elif isinstance(value, str):
        if value.strip():
            names.append(value.strip())
    return ", ".join(names) if names else None

def _publisher_str(v: Any) -> Union[str, None]:
    return v.get("name") if isinstance(v, dict) else (v or None)

def _normalize_type(value: Any) -> str:
    s = " ".join(map(str, value)) if isinstance(value, list) else str(value or "")
    s = s.lower()
    if "dataset" in s: return "dataset"
    if "softwaresourcecode" in s or "software" in s: return "software"
    if "computation" in s: return "computation"
    if "sample" in s: return "sample"
    if "experiment" in s: return "experiment"
    if "instrument" in s: return "instrument"
    if "schema" in s: return "schema"
    return "other"

def _first_url(v: Any) -> Union[str, None]:
    if isinstance(v, list):
        return v[0] if v else None
    return v or None

def _content_status_from_url(v: Any) -> str:
    url = _first_url(v)
    if not url:
        return "No link"
    if str(url).strip().lower() == "embargoed":
        return "Embargoed"
    return f"<a href='{url}'>Access / Download</a>"

def _manufacturer_str(v: Any) -> Union[str, None]:
    return v.get("name") if isinstance(v, dict) else (v or None)

def _schema_properties_compact(v: Any) -> Union[Dict[str, Dict[str, Union[str, int]]], None]:
    if not isinstance(v, dict):
        return None
    compact: Dict[str, Dict[str, Union[str, int]]] = {}
    for prop, spec in v.items():
        if isinstance(spec, dict):
            compact[prop] = {
                "type": spec.get("type", "Unknown"),
                "description": spec.get("description", ""),
                "index": spec.get("index", "N/A"),
            }
    return compact or None

def _summary_stats_name_builder(*, converter_instance, source_entity_model):
    root = source_entity_model.model_dump(by_alias=True)
    ref = root.get("hasSummaryStatistics")
    if isinstance(ref, dict):
        ref_id = ref.get("@id")
    else:
        ref_id = str(ref or "")
    if not ref_id:
        return None

    for e in converter_instance.source_crate.metadataGraph:
        sd = e.model_dump(by_alias=True)
        if sd.get("@id") == ref_id or getattr(e, "guid", None) == ref_id:
            return sd.get("name") or "Quality Control Report"
    return None

def _summary_stats_url_builder(*, converter_instance, source_entity_model):
    root = source_entity_model.model_dump(by_alias=True)
    ref = root.get("hasSummaryStatistics")
    if isinstance(ref, dict):
        ref_id = ref.get("@id")
    else:
        ref_id = str(ref or "")
    if not ref_id:
        return None

    for e in converter_instance.source_crate.metadataGraph:
        sd = e.model_dump(by_alias=True)
        if sd.get("@id") == ref_id or getattr(e, "guid", None) == ref_id:
            cu = sd.get("contentUrl")
            return _first_url(cu)
    return None



PREVIEW_ROOT_MAPPING: Dict[str, Dict[str, Any]] = {
    # identity
    "title":                 {"source_key": "name"},
    "id_value":              {"source_key": "@id"},
    "version":               {"source_key": "version"},
    "description":           {"source_key": "description"},
    "doi":                   {"source_key": "identifier"},
    "license_value":         {"source_key": "license"},

    # dates
    "release_date":          {"source_key": "datePublished"},
    "created_date":          {"source_key": "dateCreated"},
    "updated_date":          {"source_key": "dateModified"},

    # people/orgs
    "authors":               {"source_key": "author", "parser": _join_authors},
    "publisher":             {"source_key": "publisher", "parser": _publisher_str},
    "principal_investigator":{"source_key": "principalInvestigator"},
    "contact_email":         {"source_key": "contactEmail"},
    "confidentiality_level": {"source_key": "confidentialityLevel"},

    # misc
    "keywords":              {"source_key": "keywords", "parser": _keywords_as_list},
    "citation":              {"source_key": "citation"},
    "related_publications":  {"source_key": "associatedPublication", "parser": _related_publications},

    # summary stats link (needs graph context)
    "statistical_summary_name": {"source_key": "hasSummaryStatistics", "builder_func": _summary_stats_name_builder},
    "statistical_summary_url":  {"source_key": "hasSummaryStatistics", "builder_func": _summary_stats_url_builder},
}

# Component -> PreviewItem
PREVIEW_ITEM_MAPPING: Dict[str, Dict[str, Any]] = {
    "id":              {"source_key": "@id"},
    "name":            {"source_key": "name"},
    "description":     {"source_key": "description"},
    "type":            {"source_key": "@type", "parser": _normalize_type},
    "date":            {"source_key": "datePublished"},
    "identifier":      {"source_key": "identifier"},

    # content/access
    "content_url":     {"source_key": "contentUrl", "parser": _first_url},
    "content_status":  {"source_key": "contentUrl", "parser": _content_status_from_url},

    # optional preview fields
    "experimentType":  {"source_key": "experimentType"},
    "manufacturer":    {"source_key": "manufacturer", "parser": _manufacturer_str},

    # schema extras
    "schema_properties": {"source_key": "properties", "parser": _schema_properties_compact},
}

# Full configuration for your converter
PREVIEW_MAPPING_CONFIGURATION: Dict[str, Any] = {
    "entity_map": {
        ("ROCrateMetadataElem", "ROOT"): {
            "target_class": Preview,
            "mapping_def": PREVIEW_ROOT_MAPPING,
        },

        # Components -> PreviewItem (same mapping def; bucketed later)
        ("Dataset", "COMPONENT"):     {"target_class": PreviewItem, "mapping_def": PREVIEW_ITEM_MAPPING},
        ("Software", "COMPONENT"):    {"target_class": PreviewItem, "mapping_def": PREVIEW_ITEM_MAPPING},
        ("Computation", "COMPONENT"): {"target_class": PreviewItem, "mapping_def": PREVIEW_ITEM_MAPPING},
        ("Sample", "COMPONENT"):      {"target_class": PreviewItem, "mapping_def": PREVIEW_ITEM_MAPPING},
        ("Experiment", "COMPONENT"):  {"target_class": PreviewItem, "mapping_def": PREVIEW_ITEM_MAPPING},
        ("Instrument", "COMPONENT"):  {"target_class": PreviewItem, "mapping_def": PREVIEW_ITEM_MAPPING},
        ("Schema", "COMPONENT"):      {"target_class": PreviewItem, "mapping_def": PREVIEW_ITEM_MAPPING},
        ("GenericMetadataElem", "COMPONENT"):       {"target_class": PreviewItem, "mapping_def": PREVIEW_ITEM_MAPPING},
    },

    "sub_mappings": {},

    "assembly_instructions": [
        {
            "parent_type": Preview,
            "parent_attribute": "datasets",
            "child_type": PreviewItem,
            "child_filter": lambda o: (getattr(o, "type", "") or "") == "dataset",
        },
        {
            "parent_type": Preview,
            "parent_attribute": "software",
            "child_type": PreviewItem,
            "child_filter": lambda o: (getattr(o, "type", "") or "") == "software",
        },
        {
            "parent_type": Preview,
            "parent_attribute": "computations",
            "child_type": PreviewItem,
            "child_filter": lambda o: (getattr(o, "type", "") or "") == "computation",
        },
        {
            "parent_type": Preview,
            "parent_attribute": "samples",
            "child_type": PreviewItem,
            "child_filter": lambda o: (getattr(o, "type", "") or "") == "sample",
        },
        {
            "parent_type": Preview,
            "parent_attribute": "experiments",
            "child_type": PreviewItem,
            "child_filter": lambda o: (getattr(o, "type", "") or "") == "experiment",
        },
        {
            "parent_type": Preview,
            "parent_attribute": "instruments",
            "child_type": PreviewItem,
            "child_filter": lambda o: (getattr(o, "type", "") or "") == "instrument",
        },
        {
            "parent_type": Preview,
            "parent_attribute": "schemas",
            "child_type": PreviewItem,
            "child_filter": lambda o: (getattr(o, "type", "") or "") == "schema",
        },
        {
            "parent_type": Preview,
            "parent_attribute": "other_items",
            "child_type": PreviewItem,
            "child_filter": lambda o: (getattr(o, "type", "") or "") not in {
                "dataset", "software", "computation", "sample", "experiment", "instrument", "schema"
            },
        },
    ],
}

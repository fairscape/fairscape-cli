"""
ROCrate to D4D conversion mappings and utility functions.

This module provides the mapping configurations and parser functions needed
to convert ROCrate format data to D4D (Data Sheets for Datasets) format.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import re


# ============================================================================
# Parser Functions - Type Conversions
# ============================================================================

def _parse_iso_to_datetime(dt: Any) -> Optional[datetime]:
    """Convert ISO format strings to datetime objects."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt
    if isinstance(dt, str):
        # Try various formats
        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"]:
            try:
                return datetime.strptime(dt.split(".")[0], fmt)
            except ValueError:
                continue
    return None

def _parse_keywords_to_list(keywords: Any) -> Optional[List[str]]:
    """Convert keywords to list of strings."""
    if not keywords:
        return None
    if isinstance(keywords, str):
        return [kw.strip() for kw in re.split(r'[;,]', keywords) if kw.strip()]
    elif isinstance(keywords, list):
        return [str(item) for item in keywords if item]
    return None


def _parse_size_to_bytes(size_value: Any) -> Optional[int]:
    """Convert human-readable size strings to bytes."""
    if size_value is None:
        return None
    if isinstance(size_value, int):
        return size_value
    if isinstance(size_value, str):
        size_str = size_value.strip().lower()
        if size_str.isdigit():
            return int(size_str)

        units = {
            'b': 1, 'byte': 1, 'bytes': 1,
            'kb': 1024, 'kilobyte': 1024, 'kilobytes': 1024,
            'mb': 1024**2, 'megabyte': 1024**2, 'megabytes': 1024**2,
            'gb': 1024**3, 'gigabyte': 1024**3, 'gigabytes': 1024**3,
            'tb': 1024**4, 'terabyte': 1024**4, 'terabytes': 1024**4
        }

        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                try:
                    number = float(size_str[:-len(unit)].strip())
                    return int(number * multiplier)
                except ValueError:
                    continue
    return None


def _string_to_list(value: Any) -> Optional[List[str]]:
    """Convert a string to a single-item list, or return list as-is."""
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return [str(value)]


# ============================================================================
# Builder Functions - Complex Field Extraction
# ============================================================================



# ============================================================================
# Mapping Configuration
# ============================================================================

ROCRATE_TO_D4D_MAPPING = {
    
    #named thing
    "id": {"source_key": "@id"},
    "name": {"source_key": "name"},
    "title": {"source_key": "name"},
    "description": {"source_key": "description"},
    
    #information
    "compression": {"source_key": "evi:formats"},
    "conforms_to": {"fixed_value": "D4D Schema"},  
    "created_by": {"source_key": "author"},
    "created_on": {"source_key": "dateCreated", "parser": _parse_iso_to_datetime},
    "doi": {"source_key": "identifier"},
    "download_url": {"source_key": "contentUrl"},
    "keywords": {"source_key": "keywords"},
    "language": {"source_key": "language"},
    "last_updated_on": {"source_key": "dateModified", "parser": _parse_iso_to_datetime},
    "license": {"source_key": "license"},
    "page": {"source_key": "url"},
    "publisher": {"source_key": "publisher"},
    "version": {"source_key": "version"},
    "was_derived_from": {"source_key": "generatedBy"},
   
   
    


    # Dataset
    
    "bytes": {"source_key": "contentSize", "parser": _parse_size_to_bytes},
    "encoding":  {"source_key": "evi:formats"},
    "format": {"source_key": "evi:formats"},
    "hash": {"source_key": "MD5"},
    "md5": {"source_key": "MD5"},
    "sha256": {"source_key": "sha256"},
    
    #media_type, path, external_resources, resources
    
    "purposes": {"source_key": "rai:dataUseCases"},
    "tasks": {"source_key": "rai:dataUseCases"},
    #addressing_gaps
    "creators": {"source_key": "author"},
    "funders": {"source_key": "funders"},
    
    #subsets, instances, anomalies
    
    "known_biases": {"source_key": "rai:dataBiases"},
    "known_limitations": {"source_key": "rai:dataLimitations"},
    
    #confidential_elements, content_warnings, subpopulations
    "sensitive_elements": {"source_key": "rai:personalSensitiveInformation"},
    "aquisition_methods": {"source_key": "rai:dataCollection"},
    "collection_mechanisms": {"source_key": "rai:dataCollection"},
    
    #sampling_strategies, data_collectors
    
    "collection_timeframes": {"source_key": "rai:dataCollectionTimeframe"},
    "missing_data_documentation": {"source_key": "rai:dataCollectionMissingData"},
    "raw_data_sources": {"source_key": "rai:dataCollectionRawData"},
    "ethical_reviews": {"source_key": "ethicalReview"},

    #data_protection_impacts
    "human_subject_research": {"source_key": "humanSubject"},
    
    #informed_consent, participant_privacy, participant_compensation, vulnerable_populations
    
    "preprocessing_strategies": {"source_key": "rai:dataPreprocessingProtocol"},
    
    #cleaning_strategies
    
    "labeling_strategies": {"source_key": "rai:dataAnnotationProtocol"},
    "raw_sources": {"source_key":"rai:dataCollectionRawData"},
    "imputation_protocols": {"source_key":"rai:dataImputationProtocol"},
    "annotation_analyses": {"source_key":"rai:dataAnnotationProtocol"},
    "machine_annotation_tools": {"source_key":"rai:machineAnnotationTools"},    
    
    #existing_ueses, use_repostitory, other_tasks
    
    "future_use_impacts": {"source_key":"rai:dataSocialImpact"},
    "discouraged_uses": {"source_key":"prohibitedUses"},
    "intended_uses": {"source_key": "rai:dataUseCases"},
    "prohibited_uses": {"source_key":"prohibitedUses"},
    "distribution_formats": {"source_key":"evi:formats"},
    "license_and_use_terms": {"source_key":"license"},
    
    #ip_restrictions, regional_restrictions, maintainers, errata, version_access, extension_mechanism, variables, is_deidentified, is_tabular
    
    "citation": {"source_key":"citation"},

}

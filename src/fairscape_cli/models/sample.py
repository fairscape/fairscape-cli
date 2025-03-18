from typing import Optional, Dict, Any, List
from pydantic import Field
from fairscape_cli.models.dataset import Dataset
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
from fairscape_cli.config import NAAN

class Sample(Dataset):
    """Extension of Dataset for representing biological samples"""
    metadataType: str = Field(
        alias="@type",
        default="https://w3id.org/EVI#Sample"
    )
    # Biosample metadata fields
    accession: Optional[str] = None
    scientific_name: Optional[str] = None
    taxon_id: Optional[str] = None
    
    # Sample attribute fields
    sample_name: Optional[str] = None
    cell_line: Optional[str] = None
    cell_type: Optional[str] = None
    disease: Optional[str] = None
    health_state: Optional[str] = None
    isolation_source: Optional[str] = None
    sex: Optional[str] = None
    strain: Optional[str] = None
    tissue_type: Optional[str] = None
    breed: Optional[str] = None
    genotype: Optional[str] = None
    age: Optional[str] = None
    collection_date: Optional[str] = None
    body_site: Optional[str] = None
    
    # Cell line reference
    cell_line_reference: Optional[Dict[str, str]] = None
    
    model_config = {
        "extra": "allow"
    }
    
def GenerateSample(
    guid: Optional[str],
    accession: str,
    title: str,
    scientific_name: str,
    taxon_id: str,
    attributes: Dict[str, Any],
    author: str = "Unknown",
    description: str = "",
    keywords: List[str] = None,
    version: str = "1.0",
    file_format: str = "unknown",
    contentUrl: Optional[str] = None,
    cell_line_reference: Optional[Dict[str, str]] = None,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> Sample:
    """Generate a Sample model class from biosample data"""
    if not guid:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/sample-{accession.lower()}-{sq}"
        
    # Ensure we have keywords
    if keywords is None:
        keywords = ["sample", scientific_name]
        
    # Create a description if one isn't provided
    if not description:
        description = f"Biological sample {accession}: {title or scientific_name}"
        if attributes.get("disease"):
            description += f", Disease: {attributes.get('disease')}"
        if attributes.get("tissue_type") or attributes.get("cell_type"):
            tissue = attributes.get("tissue_type") or attributes.get("cell_type")
            description += f", Tissue: {tissue}"
            
    # Create the sample metadata
    sample_metadata = {
        "@id": guid,
        "@type": "https://w3id.org/EVI#Sample",
        "author": author,
        "name": title or f"Sample {accession}",
        "description": description,
        "keywords": keywords,
        "version": version,
        "format": file_format,
        "accession": accession,
        "original_title": title,
        "scientific_name": scientific_name,
        "taxon_id": taxon_id,
        "datePublished": attributes.get("collection_date", "Unknown"),
    }
    
    # Move known attributes to their specific fields
    known_attributes = [
        "sample_name", "cell_line", "cell_type", "disease",
        "health_state", "isolation_source", "sex", "strain",
        "tissue_type", "breed", "genotype", "age",
        "collection_date", "body_site"
    ]
    
    for attr in known_attributes:
        if attr in attributes:
            sample_metadata[attr] = attributes[attr]
            
    # Add cell line reference if provided
    if cell_line_reference:
        sample_metadata['cell_line_reference'] = cell_line_reference
            
    # Add contentUrl if filepath is provided
    if contentUrl:
        sample_metadata['contentUrl'] = contentUrl

    if additional_metadata:
        sample_metadata.update(additional_metadata)
        
    sample_instance = Sample.model_validate(sample_metadata)
    return sample_instance
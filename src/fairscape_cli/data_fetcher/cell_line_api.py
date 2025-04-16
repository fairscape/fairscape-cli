#!/usr/bin/env python3
import sys
import json
import requests
from bs4 import BeautifulSoup

def search_cellosaurus(cell_line):
    """
    Search Cellosaurus for a cell line and return the first result's URL and accession.
    
    Args:
        cell_line (str): The cell line to search for
        
    Returns:
        tuple: (URL, accession) for the first result, or (None, None) if no results
    """
    url = f"https://www.cellosaurus.org/search?query={cell_line}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the first row in the results table
        results_table = soup.find('table', class_='type-1')
        
        if results_table:
            first_row = results_table.find('tr')
            
            if first_row:
                accession_cell = first_row.find('td')
                if accession_cell:
                    accession_link = accession_cell.find('a')
                    if accession_link:
                        accession = accession_link.text
                        url = f"https://www.cellosaurus.org/{accession}"
                        return url, accession
        
        return None, None
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        return None, None

def get_cell_line_metadata(url):
    """
    Retrieve and extract metadata for a cell line from its detail page.
    
    Args:
        url (str): The URL of the cell line detail page
        
    Returns:
        dict: A dictionary containing the cell line metadata
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize metadata dictionary
        metadata = {}
        
        # Find the main table containing cell line data
        table = soup.find('table', {'class': 'type-2'})
        
        if not table:
            return metadata
        
        # Extract key-value pairs from the table
        rows = table.find_all('tr')
        for row in rows:
            header = row.find('th')
            data = row.find('td')
            
            if header and data:
                key = header.text.strip()
                value = data.text.strip()
                
                # Skip large sections to keep the output manageable
                if key in ["Publications", "Gene expression databases"]:
                    continue
                
                # For certain fields, split multiple lines
                if key in ["Synonyms", "Comments"]:
                    value = [v.strip() for v in value.split('\n') if v.strip()]
                
                metadata[key] = value
        
        return metadata
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        return {}

def format_structured_json(metadata, url, accession):
    """
    Format the metadata into a structured JSON format following the schema template.
    
    Args:
        metadata (dict): The metadata dictionary
        url (str): The URL of the cell line
        accession (str): The accession number
        
    Returns:
        dict: A dictionary in the specified format
    """
    # Extract cell line name
    cell_name = metadata.get("Cell line name", "")
    
    # Create ark ID from accession
    ark_id = f"ark:59852/cell-line-{cell_name.replace(' ', '-')}"
    
    # Extract synonyms/alternate names
    alternate_names = []
    if "Synonyms" in metadata and metadata["Synonyms"]:
        if isinstance(metadata["Synonyms"], list):
            raw_synonyms = metadata["Synonyms"][0]
        else:
            raw_synonyms = metadata["Synonyms"]
        
        # Split by semicolons if present
        alternate_names = [name.strip() for name in raw_synonyms.split(';')]
    
    # Extract RRID if available
    rrid = ""
    if "Resource Identification Initiative" in metadata:
        rrid_text = metadata["Resource Identification Initiative"]
        if "RRID:" in rrid_text:
            start_idx = rrid_text.find("RRID:")
            end_idx = rrid_text.find(")", start_idx) if ")" in rrid_text[start_idx:] else len(rrid_text)
            rrid = rrid_text[start_idx:end_idx]
    
    # Extract species/organism information
    species = "Unknown"
    ncbi_taxid = ""
    if "Species of origin" in metadata:
        species_text = metadata["Species of origin"]
        species = species_text.split("(")[0].strip()
        
        # Try to extract NCBI taxonomy ID
        if "NCBI Taxonomy:" in species_text:
            taxid_start = species_text.find("NCBI Taxonomy:") + len("NCBI Taxonomy:")
            taxid_end = species_text.find(")", taxid_start) if ")" in species_text[taxid_start:] else len(species_text)
            ncbi_taxid = species_text[taxid_start:taxid_end].strip()
    
    # Create the structured JSON
    structured_json = {
        "@id": ark_id,
        "@type": "BioChemEntity",
        "name": f"{cell_name} Cell Line",
        "identifier": [
            {
                "@type": "PropertyValue",
                "@value": f"RRID:{accession}" if not rrid else rrid,
                "name": "RRID"
            }
        ],
        "url": url,
        "alternateName": alternate_names,
        "organism": {
            "@id": f"ark:59852/organism-{species.lower().replace(' ', '-')}",
            "name": species,
            "identifier": []
        },
        "EVI:usedBy": []
    }
    
    # Add NCBI taxonomy ID if available
    if ncbi_taxid:
        structured_json["organism"]["identifier"].append({
            "@type": "PropertyValue",
            "name": "NCBI Taxonomy Browser",
            "value": f"NCBI:txid{ncbi_taxid}",
            "url": f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=info&id={ncbi_taxid}"
        })
    
    return structured_json

def get_cell_line_entity(cell_line_name):
    """
    Lookup a cell line in Cellosaurus and return its entity representation.
    
    Args:
        cell_line_name (str): The name of the cell line to look up
        
    Returns:
        dict or None: The cell line entity as a dictionary, or None if not found
    """
    url, accession = search_cellosaurus(cell_line_name)
    
    if url and accession:
        # Get metadata from the cell line detail page
        metadata = get_cell_line_metadata(url)
        
        # Format in structured JSON
        structured_data = format_structured_json(metadata, url, accession)
        return structured_data
    
    return None
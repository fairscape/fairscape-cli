from fairscape_models.instrument import Instrument
from fairscape_cli.config import NAAN
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
from fairscape_cli.models.utils import setRelativeFilepath
import pathlib
from typing import Dict, Any, Optional, List, Tuple

def GenerateInstrument(
    guid: Optional[str] = None,
    name: Optional[str] = None,
    filepath: Optional[str] = None,
    cratePath: Optional[str] = None,
    **kwargs
) -> Instrument:
    """
    Generate an Instrument instance with flexible parameters.
    
    This function creates an Instrument instance with minimal required parameters and
    allows for any additional parameters to be passed through to the Instrument model.
    Validation is handled by the Instrument model itself.
    
    Args:
        guid: Optional identifier. If not provided, one will be generated.
        name: Optional name for the instrument. Used for GUID generation if provided.
        filepath: Optional path to the instrument documentation file.
        cratePath: Optional path to the RO-Crate containing the instrument.
        **kwargs: Additional parameters to pass to the Instrument model.
        
    Returns:
        A validated Instrument instance
    """
    # Generate GUID if not provided
    if not guid and name:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/instrument-{name.lower().replace(' ', '-')}-{sq}"
    elif not guid:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/instrument-{sq}"
    
    instrumentMetadata = {
        "@id": guid,
        "name": name,
        "@type": "https://w3id.org/EVI#Instrument"
    }
    
    if filepath and cratePath:
        instrumentMetadata['contentUrl'] = setRelativeFilepath(cratePath, filepath)
    elif filepath:
        instrumentMetadata['contentUrl'] = filepath
    
    for key, value in kwargs.items():
        if key in ["usedByExperiment"] and value:
            if isinstance(value, str):
                instrumentMetadata[key] = [{"@id": value.strip("\n")}]
            elif (isinstance(value, list) or isinstance(value, tuple)) and len(value) > 0:
                instrumentMetadata[key] = [{"@id": item.strip("\n")} for item in value]
        elif value is not None: 
            instrumentMetadata[key] = value
    
    return Instrument.model_validate(instrumentMetadata)

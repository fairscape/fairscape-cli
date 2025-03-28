from fairscape_models.software import Software
from fairscape_cli.config import NAAN
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
from typing import Dict, Any, Optional, List
import pathlib
from fairscape_cli.models.utils import setRelativeFilepath
from fairscape_cli.models.utils import FileNotInCrateException

def GenerateSoftware(
    guid: Optional[str] = None,
    name: Optional[str] = None,
    filepath: Optional[str] = None,
    cratePath: Optional[str] = None,
    **kwargs
) -> Software:
    """
    Generate a Software instance with flexible parameters.
    
    This function creates a Software instance with minimal required parameters and
    allows for any additional parameters to be passed through to the Software model.
    Validation is handled by the Software model itself.
    
    Args:
        guid: Optional identifier. If not provided, one will be generated.
        name: Optional name for the software. Used for GUID generation if provided.
        filepath: Optional path to the software file.
        cratePath: Optional path to the RO-Crate containing the software.
        **kwargs: Additional parameters to pass to the Software model.
        
    Returns:
        A validated Software instance
    """
    if not guid and name:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/software-{name.lower().replace(' ', '-')}-{sq}"
    elif not guid:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/software-{sq}"
    
    softwareMetadata = {
        "@id": guid,
        "name" : name,
        "@type": "https://w3id.org/EVI#Software"
    }
    
    if filepath and cratePath:
        softwareMetadata['contentUrl'] = setRelativeFilepath(cratePath, filepath)
    elif filepath:
        softwareMetadata['contentUrl'] = filepath
    
    for key, value in kwargs.items():
        if key == "usedByComputation" and value:
            if isinstance(value, str):
                softwareMetadata[key] = [{"@id": value.strip("\n")}]
            elif (isinstance(value, list) or isinstance(value, tuple)) and len(value) > 0:
                softwareMetadata[key] = [{"@id": item.strip("\n")} for item in value]
        elif key == "fileFormat":
            softwareMetadata["format"] = value
        elif value is not None: 
            softwareMetadata[key] = value
    
    return Software.model_validate(softwareMetadata)
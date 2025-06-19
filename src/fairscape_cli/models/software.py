from fairscape_models.software import Software
from fairscape_cli.config import NAAN
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid, clean_guid
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from fairscape_cli.models.utils import setRelativeFilepath, calculate_md5
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
        seg = clean_guid(f"{name.lower().replace(' ', '-')}-{sq}")
        guid = f"ark:{NAAN}/software-{seg}"
    elif not guid:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/software-{sq}"
    
    softwareMetadata = {
        "@id": guid,
        "name" : name,
        "@type": "https://w3id.org/EVI#Software"
    }
    
    content_url = None
    if filepath and cratePath:
        content_url = setRelativeFilepath(cratePath, filepath)
    elif filepath:
        content_url = filepath
    
    if content_url:
        softwareMetadata['contentUrl'] = content_url
        
        if content_url.startswith('file:///'):
            parsed_url = urlparse(content_url)
            local_path = parsed_url.path
            try:
                md5_hash = calculate_md5(local_path)
                softwareMetadata['md5'] = md5_hash
            except (FileNotFoundError, PermissionError, OSError):
                pass
    
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
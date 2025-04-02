from fairscape_models.sample import Sample
from fairscape_cli.config import NAAN
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
from fairscape_cli.models.utils import setRelativeFilepath
import pathlib
from typing import Dict, Any, Optional, List, Tuple

def GenerateSample(
    guid: Optional[str] = None,
    name: Optional[str] = None,
    filepath: Optional[str] = None,
    cratePath: Optional[str] = None,
    **kwargs
) -> Sample:
    """
    Generate a Sample instance with flexible parameters.
    
    This function creates a Sample instance with minimal required parameters and
    allows for any additional parameters to be passed through to the Sample model.
    Validation is handled by the Sample model itself.
    
    Args:
        guid: Optional identifier. If not provided, one will be generated.
        name: Optional name for the sample. Used for GUID generation if provided.
        filepath: Optional path to the sample file.
        cratePath: Optional path to the RO-Crate containing the sample.
        **kwargs: Additional parameters to pass to the Sample model.
        
    Returns:
        A validated Sample instance
    """
    # Generate GUID if not provided
    if not guid and name:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/sample-{name.lower().replace(' ', '-')}-{sq}"
    elif not guid:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/sample-{sq}"
    
    sampleMetadata = {
        "@id": guid,
        "name": name,
        "@type": "https://w3id.org/EVI#Sample"
    }
    
    if filepath and cratePath:
        sampleMetadata['contentUrl'] = setRelativeFilepath(cratePath, filepath)
    elif filepath:
        sampleMetadata['contentUrl'] = filepath
    
    for key, value in kwargs.items():
        if key == "cellLineReference" and value:
            if isinstance(value, str):
                sampleMetadata["cellLineReference"] = {"@id": value}
            else:
                sampleMetadata["cellLineReference"] = {"@id": value}
        elif key in ["generatedBy"] and value:
            if isinstance(value, str):
                sampleMetadata[key] = [{"@id": value.strip("\n")}]
            elif (isinstance(value, list) or isinstance(value, tuple)) and len(value) > 0:
                sampleMetadata[key] = [{"@id": item.strip("\n")} for item in value]
        elif value is not None: 
            sampleMetadata[key] = value
    
    return Sample.model_validate(sampleMetadata)
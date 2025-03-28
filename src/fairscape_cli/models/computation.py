from fairscape_models.computation import Computation
from fairscape_cli.config import NAAN
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
from typing import Dict, Any, Optional, List, Union

def GenerateComputation(
    guid: Optional[str] = None,
    name: Optional[str] = None,
    **kwargs
) -> Computation:
    """
    Generate a Computation instance with flexible parameters.
    
    This function creates a Computation instance with minimal required parameters and
    allows for any additional parameters to be passed through to the Computation model.
    Validation is handled by the Computation model itself.
    
    Args:
        guid: Optional identifier. If not provided, one will be generated.
        name: Optional name for the computation. Used for GUID generation if provided.
        **kwargs: Additional parameters to pass to the Computation model.
        
    Returns:
        A validated Computation instance
    """
    # Generate GUID if not provided
    if not guid and name:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/computation-{name.lower().replace(' ', '-')}-{sq}"
    elif not guid:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/computation-{sq}"
    
    computationMetadata = {
        "@id": guid,
        "name": name,
        "@type": "https://w3id.org/EVI#Computation"
    }
    
    for key, value in kwargs.items():
        if key in ["usedSoftware", "usedDataset", "generated"] and value:
            if isinstance(value, str):
                computationMetadata[key] = [{"@id": value.strip("\n")}]
            elif (isinstance(value, list) or isinstance(value, tuple)) and len(value) > 0:
                computationMetadata[key] = [{"@id": item.strip("\n")} for item in value]
        elif value is not None:
            computationMetadata[key] = value
    
    return Computation.model_validate(computationMetadata)
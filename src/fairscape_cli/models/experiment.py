from fairscape_models.experiment import Experiment
from fairscape_cli.config import NAAN
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
import pathlib
from typing import Dict, Any, Optional, List, Tuple

def GenerateExperiment(
    guid: Optional[str] = None,
    name: Optional[str] = None,
    **kwargs
) -> Experiment:
    """
    Generate an Experiment instance with flexible parameters.
    
    This function creates an Experiment instance with minimal required parameters and
    allows for any additional parameters to be passed through to the Experiment model.
    Validation is handled by the Experiment model itself.
    
    Args:
        guid: Optional identifier. If not provided, one will be generated.
        name: Optional name for the experiment. Used for GUID generation if provided.
        **kwargs: Additional parameters to pass to the Experiment model.
        
    Returns:
        A validated Experiment instance
    """
    # Generate GUID if not provided
    if not guid and name:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/experiment-{name.lower().replace(' ', '-')}-{sq}"
    elif not guid:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/experiment-{sq}"
    
    experimentMetadata = {
        "@id": guid,
        "name": name,
        "@type": "https://w3id.org/EVI#Experiment"
    }
    
    for key, value in kwargs.items():
        if key in ["usedInstrument", "usedSample", "generated","usedStain","usedTreatment"] and value:
            if isinstance(value, str):
                experimentMetadata[key] = [{"@id": value.strip("\n")}]
            elif (isinstance(value, list) or isinstance(value, tuple)) and len(value) > 0:
                if isinstance(value[0], str):
                    experimentMetadata[key] = [{"@id": item.strip("\n")} for item in value]
                else: 
                    experimentMetadata[key] = [item for item in value]
        elif value is not None: 
            experimentMetadata[key] = value
    
    return Experiment.model_validate(experimentMetadata)
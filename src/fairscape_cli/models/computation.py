import re
from datetime import datetime
from typing import Optional, List, Union, Dict

from pydantic import Field, AnyUrl

from fairscape_cli.config import NAAN
from fairscape_cli.models.base import FairscapeBaseModel
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid


class Computation(FairscapeBaseModel):
    guid: Optional[str] = Field(
        default=None, 
        alias="@id", 
        validation_alias="@id"
        )
    metadataType: str = Field(
        default="https://w3id.org/EVI#Computation", 
        alias="@type", 
        validation_alias="@type"
        )
    runBy: str
    dateCreated: str 
    description: str = Field(min_length=10)
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    command: Optional[Union[List[str], str]] = Field(default="")
    usedSoftware: Optional[List[str]] = Field(default=[])
    usedDataset: Optional[List[str]] = Field(default=[])
    generated: Optional[List[str]] = Field(default=[])


def GenerateComputation(
    guid: str,
    name: str,
    runBy: str,
    command: Optional[Union[str, List[str]]],
    dateCreated: str,
    description: str,
    keywords: List[str],
    usedSoftware,
    usedDataset,
    generated
) -> Computation: 
    """ Generate a Computation model class from command line arguments
    """
    
    sq = GenerateDatetimeSquid()
    guid = f"ark:{NAAN}/computation-{name.lower().replace(' ', '-')}-{sq}"

    if generated is None:
        processedGenerated = []
    else:
        processedGenerated = [
                output.strip("\n") for output in generated
            ]


    computation_model = Computation.model_validate(   
        {
        "@id": guid,
        "@type": "https://w2id.org/EVI#Computation",
        "name": name,
        "description": description,
        "keywords": keywords,
        "runBy": runBy,
        "command": command,
        "dateCreated": dateCreated,
        "description": description,
        # sanitize input lists of newline breaks
        "usedSoftware": [
            software.strip("\n") for software in usedSoftware
        ],
        "usedDataset": [
            dataset.strip("\n") for dataset in usedDataset 
        ],
        "generated": processedGenerated
        })
    

    return computation_model

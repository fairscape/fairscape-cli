import re
from datetime import datetime
from typing import Optional, List, Union, Dict
from pydantic import Field, AnyUrl, BaseModel
from fairscape_cli.config import NAAN
from fairscape_cli.models.base import FairscapeBaseModel
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid

class ArkPointer(BaseModel):
    ark: str = Field(
        alias="@id",
        validation_alias="@id"
    )

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
    usedSoftware: Optional[List[ArkPointer]] = Field(default_factory=list)
    usedDataset: Optional[List[ArkPointer]] = Field(default_factory=list)
    generated: Optional[List[ArkPointer]] = Field(default_factory=list)

def GenerateComputation(
    guid: str,
    name: str,
    runBy: str,
    command: Optional[Union[str, List[str]]],
    dateCreated: str,
    description: str,
    keywords: List[str],
    usedSoftware: List[str],
    usedDataset: List[str],
    generated: Optional[List[str]] = None
) -> Computation:
    """ Generate a Computation model class from command line arguments
    """
    sq = GenerateDatetimeSquid()
    guid = f"ark:{NAAN}/computation-{name.lower().replace(' ', '-')}-{sq}"
    
    if generated is None:
        processedGenerated = []
    else:
        processedGenerated = [
            ArkPointer(ark=output.strip("\n")) for output in generated
        ]

    computation_model = Computation.model_validate(
        {
            "@id": guid,
            "@type": "https://w3id.org/EVI#Computation",
            "name": name,
            "description": description,
            "keywords": keywords,
            "runBy": runBy,
            "command": command,
            "dateCreated": dateCreated,
            "description": description,
            # Convert arks to ArkPointer objects
            "usedSoftware": [
                {"@id": software.strip("\n")} for software in usedSoftware
            ],
            "usedDataset": [
                {"@id": dataset.strip("\n")} for dataset in usedDataset
            ],
            "generated": [{"@id": gen.ark} for gen in processedGenerated]
        })
    
    return computation_model
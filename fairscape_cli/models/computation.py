from fairscape_cli.models.base import FairscapeBaseModel
from fairscape_cli.models.utils import GenerateDatetimeSquid
from fairscape_cli.config import NAAN

from typing import (
    Optional,
    List,
    Union,
    Dict,
)
from pydantic import (
    Field,
    AnyUrl
)
import re
from datetime import datetime


class Computation(FairscapeBaseModel):
    metadataType: str = Field(default="https://w3id.org/EVI#Computation")
    runBy: str
    dateCreated: str 
    description: str = Field(min_length=10, max_length=2056)
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    command: Optional[Union[List[str], str]] = Field(default="")
    usedSoftware: Optional[List[str]] = Field(default=[])
    usedDataset: Optional[Union[List[str], str]] = Field(default=[])
    generated: Optional[Union[str,List[str]]] = Field(default=[])

    def generate_guid(self):
        if self.guid is None:
            sq = GenerateDatetimeSquid()
            self.guid = f"ark:{NAAN}/computation-{self.name.lower().replace(' ', '-')}-{sq}"
        return self.guid


def GenerateComputation(
    name: str,
    run_by: str,
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
    computation_model = Computation.model_validate(   
        {
        "@type": "https://w2id.org/EVI#Computation",
        "name": name,
        "description": description,
        "keywords": keywords,
        "runBy": run_by,
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
        "generated": [
            output.strip("\n") for output in generated
        ],
    })

    # generate computation guid
    computation_model.generate_guid()
    return computation_model

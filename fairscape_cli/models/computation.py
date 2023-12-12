from fairscape_cli.models.base import FairscapeBaseModel
from fairscape_cli.models.utils import GenerateGUID

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


def GenerateComputation(
    name: str,
    run_by: str,
    command: Optional[Union[str, List[str]]],
    date_created: str,
    description: str,
    keywords: List[str],
    used_software,
    used_dataset,
    generated
) -> Computation: 
    """ Generate a Computation model class from command line arguments
    """
    computation_model = Computation(   
        **{
        "@type": "https://w2id.org/EVI#Computation",
        "name": name,
        "description": description,
        "keywords": keywords,
        "runBy": run_by,
        "command": command,
        "dateCreated": date_created,
        "description": description,
        # sanitize input lists of newline breaks
        "usedSoftware": [
            software.strip("\n") for software in used_software
        ],
        "usedDataset": [
            dataset.strip("\n") for dataset in used_dataset 
        ],
        "generated": [
            output.strip("\n") for output in generated
        ],
    })
    return computation_model

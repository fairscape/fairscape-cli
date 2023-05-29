from fairscape_cli.models.base import FairscapeBaseModel

from typing import (
    Optional,
    List,
    Union,
    Dict,
)
from pydantic import (
    constr,
    AnyUrl
)
import re


class Computation(FairscapeBaseModel):
    metadataType: Optional[str] = "https://w3id.org/EVI#Computation"
    runBy: str
    dateCreated: str
    description: constr(min_length=10, max_length=2056)
    associatedPublication: Optional[Union[str, AnyUrl]]
    additionalDocumentation: Optional[Union[str, AnyUrl]]
    command: Optional[Union[List[str], str]] 
    usedSoftware: Optional[List[str]]
    calledBy: Optional[str]
    usedDataset: Optional[Union[List[str], str]]
    generated: Optional[Union[str,List[str]]]

from fairscape_cli.models.base import FairscapeBaseModel
from pydantic import (
    Field,
    AnyUrl,
    ConfigDict
)
from datetime import datetime
from typing import (
    Optional,
    Union,
    Dict,
    List 
)


class Software(FairscapeBaseModel): 
    metadataType: str = "https://w3id.org/EVI#Software"
    author: str = Field(min_length=4, max_length=64)
    dateModified: str
    version: str
    description: str =  Field(min_length=10)
    associatedPublication: Optional[str]
    additionalDocumentation: Optional[str]
    fileFormat: str = Field(title="fileFormat", alias="format")
    usedByComputation: Optional[List[str]]
    contentUrl: Optional[str] = Field(default=None)
 

from fairscape_cli.models.base import FairscapeBaseModel
from pydantic import (
    constr,
    AnyUrl
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
    author: constr(max_length=64)
    dateModified: str
    version: str
    description: constr(min_length=10)
    associatedPublication: Optional[str]
    additionalDocumentation: Optional[str]
    fileFormat: str
    usedByComputation: Optional[List[str]]
    contentUrl: Optional[str]

    class Config:
       fields={
        "fileFormat":
            {
                "title": "fileFormat",
                "alias": "format"
            }
        } 
 

from fairscape_cli.models.base import FairscapeBaseModel

from typing import (
    Optional,
    List,
    Union,
    Dict
)

from pydantic import (
    BaseModel,
    constr,
    AnyUrl
)



class Dataset(FairscapeBaseModel):
    metadataType: Optional[str] = "https://w3id.org/EVI#Dataset"
    author: constr(max_length=64)
    datePublished: str
    version: str
    description: constr(min_length=10)
    associatedPublication: Optional[str]
    additionalDocumentation: Optional[str]
    fileFormat: str
    dataSchema: Optional[Union[str, dict]]
    generatedBy: Optional[List[str]]
    derivedFrom: Optional[List[str]]
    usedBy: Optional[List[str]]
    contentUrl: Optional[str]

    class Config:
        fields={
            "fileFormat": {
                "title": "fileFormat",
                "alias": "format"
            },
            "dataSchema": {
                "title": "dataSchema",
                "alias": "schema"
            }
        }

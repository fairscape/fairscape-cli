from fairscape_cli.models.base import (
    FairscapeBaseModel,
    Identifier
)

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
    generatedBy: Optional[List[Union[str, Identifier]]]
    derivedFrom: Optional[List[Union[str, Identifier]]]
    usedBy: Optional[List[Union[str, Identifier]]]
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


class DatasetContainer(FairscapeBaseModel): 
    guid: str
    metadataType: Optional[str] = "https://w3id.org/EVI#Dataset"
    name: str
    description: constr(min_length=10)
    hasPart: Optional[List[Union[str, Identifier]]] = []
    isPartOf: Optional[List[Union[str, Identifier]]] = []


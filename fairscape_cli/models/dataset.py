from fairscape_cli.models.base import (
    FairscapeBaseModel,
    Identifier
)
from fairscape_cli.models.utils import GenerateGUID
from fairscape_cli.models.schema.tabular import (
    TabularValidationSchema
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
    Field,
    AnyUrl
)
from datetime import datetime


class Dataset(FairscapeBaseModel):
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Dataset")
    author: str = Field(max_length=64)
    datePublished: str = Field(...)
    version: str
    description: str = Field(min_length=10)
    keywords: List[str] = Field(...)
    associatedPublication: Optional[str] = None
    additionalDocumentation: Optional[str] = None
    fileFormat: str = Field(alias="format")
    dataSchema: Optional[Union[str, TabularValidationSchema]] = Field(alias="schema", default=None)
    generatedBy: Optional[List[str]] = Field(default=[])
    derivedFrom: Optional[List[str]] = Field(default=[])
    usedBy: Optional[List[str]] = Field(default=[])
    contentUrl: Optional[str] = None



class DatasetContainer(FairscapeBaseModel): 
    guid: str = Field(alias="@id")
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Dataset", alias="@type")
    name: str
    description: str = Field(min_length=10)
    keywords: List[str] = Field(...)
    generatedBy: Optional[List[str]] = Field(default=[])
    derivedFrom: Optional[List[str]] = Field(default=[])
    usedBy: Optional[List[str]] = Field(default = [])
    hasPart: Optional[List[str]] = Field(default=[])
    isPartOf: Optional[List[str]] = Field(default=[])


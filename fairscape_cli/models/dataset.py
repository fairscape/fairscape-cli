from fairscape_cli.models.base import (
    FairscapeBaseModel,
    Identifier
)
from fairscape_cli.config import (
    NAAN
)
from fairscape_cli.models.utils import GenerateDatetimeSquid
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
    guid: Optional[str] = Field(alias="@id", default=None)
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

    def generate_guid(self) -> str:
        if self.guid is None:
            sq = GenerateDatetimeSquid()
            self.guid = f"ark:{NAAN}/dataset-{self.name.lower().replace(' ', '-')}-{sq}"
        return self.guid



class DatasetContainer(FairscapeBaseModel): 
    guid: Optional[str] = Field(alias="@id", default=None)
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Dataset", alias="@type")
    name: str
    description: str = Field(min_length=10)
    keywords: List[str] = Field(...)
    generatedBy: Optional[List[str]] = Field(default=[])
    derivedFrom: Optional[List[str]] = Field(default=[])
    usedBy: Optional[List[str]] = Field(default = [])
    hasPart: Optional[List[str]] = Field(default=[])
    isPartOf: Optional[List[str]] = Field(default=[])

    def generate_guid(self)-> str:
        if self.guid is None:
            sq = GenerateDatetimeSquid()
            self.guid = f"ark:{NAAN}/datasetcontainer-{self.name.lower().replace(' ', '-')}-{sq}"
        return self.guid

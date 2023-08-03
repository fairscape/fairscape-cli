from typing import (
    Optional,
    List,
    Union,
    Dict
)

from pydantic import (
    BaseModel,
    constr,
    AnyUrl,
    Field,
    ConfigDict
)

default_context = {
    "@vocab": "https://schema.org/",
    "evi": "https://w3id.org/EVI#"
}


class Identifier(BaseModel):
    guid: str = Field(
        title="guid",
        alias="@id" 
    )
    metadataType: str = Field(
        title="metadataType",
        alias="@type" 
    )
    name: str


class FairscapeBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name = True,
        validate_assignment = True,  
    )
    guid: str = Field(
        title="guid",
        alias="@id"
    )
    context: Dict[str,str] = Field(
        default=default_context,
        title="context",
        alias="@context"
    )
    metadataType: str = Field(
        title="metadataType",
        alias="@type"
    )
    url: Optional[AnyUrl] = Field(default=None)
    name: str = Field(max_length=64)
    keywords: List[str] = Field(default=[])


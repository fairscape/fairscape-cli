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


class Identifier(BaseModel):
    guid: str
    metadataType: str
    name: str

    class Config:
        fields = {
            "guid": {
                "title": "guid",
                "alias": "@id"
            },
            "metadataType": {
                "title": "metadataType",
                "alias": "@type"
            },
            "name": {
                "title": "name"
            }
        }


class FairscapeBaseModel(BaseModel):
    guid: str
    context: Union[str, Dict[str,str]] = {
                "@vocab": "https://schema.org/",
                "evi": "https://w3id.org/EVI#"
            }
    metadataType: str
    url: Optional[AnyUrl]
    name: constr(max_length=64)
    keywords: List[str] = []

    class Config:
        allow_population_by_field_name = True
        validate_assignment = True    
        fields={
            "context": {
                "title": "context",
                "alias": "@context"
            },
            "guid": {
                "title": "guid",
                "alias": "@id"
            },
            "metadataType": {
                "title": "metadataType",
                "alias": "@type"
            },
            "name": {
                "title": "name"
            }
        }


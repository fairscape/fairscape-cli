from fairscape_cli.models.base import (
    FairscapeBaseModel,
    Identifier
)
from fairscape_cli.models.utils import GenerateGUID

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
    dataSchema: Optional[dict] = Field(alias="schema", default={})
    generatedBy: Optional[List[str]] = Field(default=[])
    derivedFrom: Optional[List[str]] = Field(default=[])
    usedBy: Optional[List[str]] = Field(default=[])
    contentUrl: Optional[str] = None


def GenerateDataset(
    name: str,
    url: str,
    author: str,
    description: str,
    keywords: List[str],
    date_published: str,
    version: str,
    associated_publication: Optional[str],
    additional_documentation: Optional[List[str]],
    data_format: str,
    filepath: str,
    derived_from: Optional[List[str]],
    used_by: Optional[List[str]],
) -> Dataset:
    """ Generate a Dataset model class
    """
    dataset_metadata = {
            "@type": "https://w2id.org/EVI#Dataset",
            "url": url,
            "author": author,
            "name": name,
            "description": description,
            "keywords": keywords,
            "datePublished": date_published,
            "version": version,
            "associatedPublication": associated_publication,
            "additionalDocumentation": additional_documentation,
            "format": data_format,
            # sanitize input lists of newline breaks
            "derivedFrom": [
                derived.strip("\n") for derived in derived_from
            ],
            "usedBy": [
                used.strip("\n") for used in used_by 
            ],
            }

    if filepath != "" and filepath is not None:
        dataset_metadata["contentUrl"] = f"file://{str(filepath)}" 

    dataset_model = Dataset(**dataset_metadata)
    return dataset_model


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


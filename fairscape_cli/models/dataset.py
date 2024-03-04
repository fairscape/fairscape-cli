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

import pathlib
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
    metadataType: Optional[str] = Field(alias="@type", default="https://w3id.org/EVI#Dataset")
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
        else:
            # TODO ensure ark is formatted correctly
            pass
        return self.guid

def GenerateDataset(
        guid, 
        url,
        author,
        description,
        name,
        keywords,
        datePublished,
        version,
        associatedPublication,
        additionalDocumentation,
        dataFormat,
        schema,
        derivedFrom,
        usedBy,
        filepath,
        cratePath
        ):
    
    datasetMetadata = {
            "@id": guid,
            "@type": "https://w3id.org/EVI#Dataset",
            "url": url,
            "author": author,
            "name": name,
            "description": description,
            "keywords": keywords,
            "datePublished": datePublished,
            "version": version,
            "associatedPublication": associatedPublication,
            "additionalDocumentation": additionalDocumentation,
            "format": dataFormat,
            "schema": schema,
            # sanitize input lists of newline breaks
            "derivedFrom": [
                derived.strip("\n") for derived in derivedFrom
            ],
            "usedBy": [
                used.strip("\n") for used in usedBy 
            ],
        }

    # set relative filepath
    if filepath is not None:
        # if filepath is a url        
        if 'http' in  filepath:
            datasetMetadata['contentUrl'] = filepath

        # if filepath is a path that exists
        else:
            if 'ro-crate-metadata.json' in cratePath:
                rocratePath = pathlib.Path(cratePath).parent
            else:
                rocratePath = pathlib.Path(cratePath)

            datasetPath = pathlib.Path(filepath)
            if datasetPath.exists() and datasetPath.is_relative_to(rocratePath):
                # create a relative filepath to the ro-crate
                datasetMetadata['contentUrl'] = f"file:///{str(datasetPath.relative_to(rocratePath))}"
            else:
                raise Exception('Software File Not Found in RO-Crate')

    datasetInstance = Dataset.model_validate(datasetMetadata)

    # generate guid
    datasetInstance.generate_guid()

    return datasetInstance


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

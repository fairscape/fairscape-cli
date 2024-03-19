from fairscape_cli.models.base import (
    FairscapeBaseModel,
    Identifier
)
from fairscape_cli.config import (
    NAAN
)
from fairscape_cli.models.utils import GenerateDatetimeSquid, FileNotInCrateException
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
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    fileFormat: str = Field(alias="format")
    dataSchema: Optional[Union[str, TabularValidationSchema]] = Field(alias="schema", default=None)
    generatedBy: Optional[List[str]] = Field(default=[])
    derivedFrom: Optional[List[str]] = Field(default=[])
    usedBy: Optional[List[str]] = Field(default=[])
    contentUrl: Optional[str] = None


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
   
    if guid is None or guid=="":
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/dataset-{name.lower().replace(' ', '-')}-{sq}"
    
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
            if 'ro-crate-metadata.json' in str(cratePath):
                rocratePath = pathlib.Path(cratePath).parent.absolute()
            else:
                rocratePath = pathlib.Path(cratePath).absolute()
            
            datasetPath = pathlib.Path(filepath).absolute()
            if datasetPath.exists():
                try:
                    relativePath = datasetPath.relative_to(rocratePath)
                    datasetMetadata['contentUrl'] = f"file:///{str(relativePath)}"
                except:
                    raise FileNotInCrateException(cratePath=cratePath, filePath=datasetPath)

            else:
                raise Exception(f"Dataset File Does Not Exist: {str(datasetPath)}")

    datasetInstance = Dataset.model_validate(datasetMetadata)

    return datasetInstance

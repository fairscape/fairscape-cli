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
    AnyUrl,
    field_serializer
)
from datetime import datetime


class Dataset(FairscapeBaseModel):
    guid: Optional[str] = Field(alias="@id", default=None)
    metadataType: Optional[str] = Field(alias="@type", default="https://w3id.org/EVI#Dataset")
    author: str = Field(max_length=64)
    datePublished: Optional[str] = Field()
    version: str
    description: str = Field(min_length=10)
    keywords: List[str] = Field(...)
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    fileFormat: str = Field(alias="format")
    dataSchema: Optional[str] = Field(alias="schema", default=None)
    generatedBy: Optional[List[str]] = Field(default=[])
    derivedFrom: Optional[List[str]] = Field(default=[])
    usedBy: Optional[List[str]] = Field(default=[])
    contentUrl: Optional[str] = Field(default=None)

    #@field_serializer('datePublished')
    #def serialize_date_published(self, datePublished: datetime):
    #    return datePublished.timestamp()



def GenerateDataset(
    guid: Optional[str],
    url: Optional[str],
    author: str,
    description: str,
    name: str,
    keywords: List[str],
    datePublished: str,
    version: str,
    associatedPublication: Optional[str],
    additionalDocumentation: Optional[str],
    dataFormat: str,
    schema: Optional[str],
    derivedFrom: Optional[List[str]],
    usedBy: Optional[List[str]],
    generatedBy: Optional[List[str]],
    filepath: Optional[str],
    cratePath
    ):
   
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
            "generatedBy": [
                gen.strip("\n") for gen in generatedBy
            ]
        }

    datasetMetadata['contentURL'] = setRelativeFilepath(cratePath, filepath)

    datasetInstance = Dataset.model_validate(datasetMetadata)

    return datasetInstance


def setRelativeFilepath(cratePath, filePath):
    ''' Modify the filepath specified in metadata s.t. 
    '''

    if filePath is None:
        return None

    # if filepath is a url        
    if 'http' in  filePath:
        return filePath

    # if a relative file uri to the crate 
    if 'file:///' in filePath:
        # TODO: search within crate to determine file is relative to crate
        # filePath = filePath.replace("file:///", "")

        return filePath

    # set relative filepath
    # if filepath is a path that exists
    if 'ro-crate-metadata.json' in str(cratePath):
        rocratePath = pathlib.Path(cratePath).parent.absolute()
    else:
        rocratePath = pathlib.Path(cratePath).absolute()

            
    # if relative filepath
    datasetPath = pathlib.Path(filePath).absolute()
    relativePath = datasetPath.relative_to(rocratePath)
    return f"file:///{str(relativePath)}"
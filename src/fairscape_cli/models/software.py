from fairscape_cli.models.base import FairscapeBaseModel
from fairscape_cli.models.utils import GenerateDatetimeSquid, FileNotInCrateException
from fairscape_cli.config import NAAN
import pathlib

from pydantic import (
    Field,
    AnyUrl,
    ConfigDict
)
from datetime import datetime
from typing import (
    Optional,
    Union,
    Dict,
    List 
)



class Software(FairscapeBaseModel): 
    guid: Optional[str] = Field( alias='@id', default=None,)
    metadataType: Optional[str] = Field(alias="@id", default="https://w3id.org/EVI#Software")
    author: str = Field(min_length=4, max_length=64)
    dateModified: str
    version: str
    description: str =  Field(min_length=10)
    associatedPublication: Optional[str]
    additionalDocumentation: Optional[str]
    fileFormat: str = Field(title="fileFormat", alias="format")
    usedByComputation: Optional[List[str]]
    contentUrl: Optional[str] = Field(default=None)

    def generate_guid(self):
        if self.guid is None:
            sq = GenerateDatetimeSquid()
            self.guid = f"ark:{NAAN}/software-{self.name.lower().replace(' ', '-')}-{sq}"
        return self.guid
 

def GenerateSoftware(    
    guid,
    name,
    author,
    version,
    description, 
    keywords,
    fileFormat,
    url,
    dateModified,
    filepath,
    usedByComputation,
    associatedPublication,
    additionalDocumentation,
    cratePath
) -> Software:
    """ Generate a Software Model Class
    """

    softwareMetadata = {
            "@id": guid,
            "@type": "https://w2id.org/EVI#Software",
            "url": url,
            "name": name,
            "author": author,
            "dateModified": dateModified,
            "description": description,
            "keywords": keywords,
            "version": version,
            "associatedPublication": associatedPublication,
            "additionalDocumentation": additionalDocumentation,
            "format": fileFormat,
            # sanitize new line characters for multiple inputs
            "usedByComputation": [
                computation.strip("\n") for computation in usedByComputation
            ],
        }

    if filepath is not None:

        # if filepath is a url        
        if 'http' in  filepath:
            softwareMetadata['contentUrl'] = filepath

        # if filepath is a path that exists
        else:
            if 'ro-crate-metadata.json' in str(cratePath):
                rocratePath = pathlib.Path(cratePath).parent
            else:
                rocratePath = pathlib.Path(cratePath)
            softwarePath = pathlib.Path(filepath)
            if softwarePath.exists() and softwarePath.is_relative_to(rocratePath):
                # create a relative filepath to the ro-crate
                softwareMetadata['contentUrl'] = f"file:///{str(softwarePath.relative_to(rocratePath))}"
            else:
                raise FileNotInCrateException(cratePath=cratePath, filePath=softwarePath)

    # validate metadata
    softwareModel = Software.model_validate(softwareMetadata)

    # generate guid for software model
    softwareModel.generate_guid()

    return softwareModel



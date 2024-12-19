import pathlib
from datetime import datetime
from typing import Optional, Union, Dict, List

from pydantic import Field, AnyUrl, ConfigDict

from fairscape_cli.config import NAAN
from fairscape_cli.models.base import FairscapeBaseModel
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid


class Software(FairscapeBaseModel): 
    guid: Optional[str] = Field( alias='@id', default=None)
    metadataType: Optional[str] = Field(alias="@type", default="https://w3id.org/EVI#Software")
    author: str = Field(min_length=4, max_length=64)
    dateModified: str
    version: str
    description: str =  Field(min_length=10)
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    fileFormat: str = Field(title="fileFormat", alias="format")
    usedByComputation: Optional[List[str]]
    contentUrl: Optional[str] = Field(default=None)
 

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

    sq = GenerateDatetimeSquid()
    guid = f"ark:{NAAN}/software-{name.lower().replace(' ', '-')}-{sq}"

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
                rocratePath = pathlib.Path(cratePath).parent.absolute()
            else:
                rocratePath = pathlib.Path(cratePath).absolute()

            softwarePath = pathlib.Path(filepath).absolute()

            if softwarePath.exists():
                try:
                    relativePath = softwarePath.relative_to(rocratePath)
                    softwareMetadata['contentUrl'] = f"file:///{str(relativePath)}"
                except:
                    raise FileNotInCrateException(cratePath=cratePath, filePath=softwarePath)
            else:
                raise Exception(f"Software File Does Not Exist: {str(softwarePath)}")


    # validate metadata
    softwareModel = Software.model_validate(softwareMetadata)


    return softwareModel



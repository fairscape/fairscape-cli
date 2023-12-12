from fairscape_cli.models.base import FairscapeBaseModel
from fairscape_cli.models.utils import GenerateGUID

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
    metadataType: str = "https://w3id.org/EVI#Software"
    author: str = Field(min_length=4, max_length=64)
    dateModified: str
    version: str
    description: str =  Field(min_length=10)
    associatedPublication: Optional[str]
    additionalDocumentation: Optional[str]
    fileFormat: str = Field(title="fileFormat", alias="format")
    usedByComputation: Optional[List[str]]
    contentUrl: Optional[str] = Field(default=None)
 

def GenerateSoftware(    
    name,
    author,
    version,
    description, 
    keywords,
    file_format,
    url,
    date_modified,
    filepath,
    used_by_computation,
    associated_publication,
    additional_documentation
) -> Software:
    """ Generate a Software Model Class
    """

    software_metadata = {
            "@type": "https://w2id.org/EVI#Software",
            "url": url,
            "name": name,
            "author": author,
            "dateModified": date_modified,
            "description": description,
            "keywords": keywords,
            "version": version,
            "associatedPublication": associated_publication,
            "additionalDocumentation": additional_documentation,
            "format": file_format,
            # sanitize new line characters for multiple inputs
            "usedByComputation": [
                computation.strip("\n") for computation in used_by_computation
            ],
        }

    if filepath is not None:
        if type(filepath) == str:
            # TODO if URL just set
            software_metadata["contentUrl"] = filepath 
        if type(filepath) == pathlib.Path:
            # TODO if pathlike object
            pass
    
    software_model = Software(**software_metadata)
    return software_model



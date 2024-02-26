from fairscape_cli.models.base import FairscapeBaseModel
from fairscape_cli.models.utils import GenerateDatetimeSquid
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

    def generate_guid(self):
        if self.guid is None:
            sq = GenerateDatetimeSquid()
            self.guid = f"ark:{NAAN}/software-{self.name.lower().replace(' ', '-')}-{sq}"
        return self.guid
 

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
    additional_documentation,
    crate_path
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
        # if filepath is a url        
        if 'http' in  filepath:
            software_metadata['contentUrl'] = filepath

        # if filepath is a path that exists
        else:
            software_path = pathlib.Path(filepath)
            rocrate_path = pathlib.Path(crate_path)
            if software_path.exists() and software_path.is_relative_to(rocrate_path):
                # create a relative filepath to the ro-crate
                software_metadata['contentUrl'] = f"file:///{str(software_path.relative_to(rocrate_path))}"
            else:
                raise Exception('Software File is not inside of RO-Crate')

    # validate metadata
    software_model = Software.model_validate(software_metadata)

    # generate guid for software model
    software_model.generate_guid()

    return software_model



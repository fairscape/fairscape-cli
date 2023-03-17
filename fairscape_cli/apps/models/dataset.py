from pydantic import BaseModel, validator
from urllib.parse import urlparse
from typing import (
    Optional,
    List
)

import fairscape_models
from fairscape_cli.apps.utils import get_sha256_remote, compute_sha256
from pathlib import Path


class Dataset(fairscape_models.Dataset):
    name: str
    description: str
    author: str
    version: str
    generatedBy: Optional[List[str]] = []
    usedBy: Optional[List[str]] = []

"""
    @validator('name', pre=True, always=True)
    def name_must_be_string(cls, v):
        if not isinstance(v, str):
            raise ValueError(f"Unable to validate \"{v}\". Must be string")
        return v

    @validator('description', pre=True, always=True)
    def description_must_be_string(cls, v):
        if not isinstance(v, str):
            raise ValueError(f"Unable to validate \"{v}\". Must be string")
        return v

    @validator('author', pre=True, always=True)
    def author_must_be_string(cls, v):
        if not isinstance(v, str):
            raise ValueError(f"Unable to validate \"{v}\". Must be string")
        return v

    @validator('version')
    def version_must_contain_a_digit(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError(f"Unable to validate \"{v}\". Must contain at least one digit")
        return v

    @validator('contentUrl', pre=True, always=True)
    def content_url_must_be_uri(cls, v):
        if not v.startswith("http"):
            path = Path(v)
            if not path.exists():
                raise ValueError(f"Unable to find document at: \"{path}\"")
            elif path.is_dir():
                raise ValueError(f"Expecting a file but got a directory at: \"{path}\"")
            elif path.is_file():
                compute_sha256(path)
            return v
        else:
            o = urlparse(v)
            if not (o.scheme and o.netloc):
                raise ValueError(f"Unable to validate \"{v}\". contentUrl is malformed")
            #elif len(get_sha256_remote(v)) > 0:
            #    raise ValueError(f"Unable to validate \"{v}\". contentUrl is malformed")
            github_prefix = "https://github.com"
            if v.startswith(github_prefix):
                url_wihtout_blob = v.replace("blob/", "")
                url_raw_content = url_wihtout_blob.replace("github", "raw.githubusercontent")
                get_sha256_remote(url_raw_content)
            else:
                raise ValueError(f"Unable to validate \"{v}\". Cannot process Non-github contentUrl")
            return v
"""

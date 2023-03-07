from pydantic import BaseModel, validator
from apps.utils import *
from typing import List, Optional


class Computation(BaseModel):
    name: str
    description: str
    runBy: str
    version: Optional[str]
    usedSoftware: str
    usedDataset: List[str]
    generated: Optional[str]

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

    @validator('runBy', pre=True, always=True)
    def executor_must_be_string(cls, v):
        if not isinstance(v, str):
            raise ValueError(f"Unable to validate \"{v}\". Must be string")
        return v

    @validator('version')
    def version_must_contain_a_digit(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError(f"Unable to validate \"{v}\". Must contain at least one digit")
        return v


    @validator('usedSoftware')
    def software_must_be_file_or_uri(cls, v):
        if valid_remote_repo_prefix(v):
            if url_has_content(v):
                return v
            else:
                raise ValueError(f"Unable to read content from \"{v}\". ")
        else:
            path = Path(v)
            if valid_path(path):
                content = path.read_text().strip(' ');
                if not (len(compute_sha256(path)) == 64 and len(content) > 0):
                    raise ValueError(f"Unable to read content from \"{v}\". ")
            return v

    @validator('usedDataset')
    def dataset_must_be_file_or_uri(cls, v):
        for dataset in v:
            #print(dataset, v)
            if valid_remote_repo_prefix(dataset):
                if not url_has_content(dataset):
                    #return v
                #else:
                    raise ValueError(f"Unable to read content from \"{v}\". ")
            else:
                path = Path(dataset)
                if valid_path(path):
                    content = path.read_text().strip(' ');
                    if not (len(compute_sha256(path)) == 64 and len(content) > 0):
                        raise ValueError(f"Unable to read content from \"{v}\". ")
                #return v

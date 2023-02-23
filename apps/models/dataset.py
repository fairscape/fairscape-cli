from pydantic import BaseModel, validator

import re


class Dataset(BaseModel):
    type: str
    name: str
    author: str
    version: str
    format: str
    contentUrl: str

    @validator('type')
    def must_be_software(cls, v):
        if v != 'Dataset':
            raise ValueError('must be of type Dataset')
        return v

    @validator('name')
    def name_must_contain_space(cls, v):
        if ' ' in v:
            raise ValueError('must not contain space')
        return v

    @validator('author')
    def author_must_contain_space(cls, v):
        if ' ' not in v:
            raise ValueError('must contain a space')
        return v

    @validator('version')
    def version_must_contain_a_digit(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('must contain at least one digit')
        return v

    @validator('format')
    def format_must_be_string_without_space(cls, v):
        format_types = ["csv", "tsv"]
        if not v in format_types:
            raise ValueError('format must be one of ', format_types)
        return v

    @validator('contentUrl')
    def contenturl_must_be_uri(cls, v):
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if re.match(regex, v) is None:
            raise ValueError('Illformed contentUrl')
        return v

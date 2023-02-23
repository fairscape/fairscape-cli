from pydantic import BaseModel, ValidationError, validator
import re


class Software(BaseModel):
    type: str
    name: str
    author: str
    version: str
    contentUrl: str

    @validator('type')
    def must_be_software(cls, v):
        if v != 'Software':
            raise ValueError('must be of type Software')
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

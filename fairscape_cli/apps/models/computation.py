from pydantic import BaseModel, ValidationError, validator
import re


class Computation(BaseModel):
    name: str
    description: str
    author: str
    version: str
    usedSoftware: str
    usedDataset: str
    generated: str

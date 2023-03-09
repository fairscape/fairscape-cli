from pydantic import BaseModel, ValidationError, validator
import fairscape_models
import re


class Computation(fairscape_models.Computation):
    name: str
    description: str
    author: str
    version: str
    usedSoftware: str
    usedDataset: str
    generated: str

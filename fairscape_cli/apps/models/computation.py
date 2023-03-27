from pydantic import BaseModel, ValidationError, validator
from typing import (
    Optional,
    List
)
import fairscape_models
import re


class Computation(fairscape_models.Computation):
    name: str
    description: str
    usedSoftware: Optional[List[str]] = []
    usedDataset: Optional[List[str]] = []
    generated: List[str] = []

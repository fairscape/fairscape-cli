from typing import (
    Optional,
    List
)
import fairscape_models

class Dataset(fairscape_models.Dataset):
    name: str
    generatedBy: Optional[List[str]] = []
    usedBy: Optional[List[str]] = []

from fairscape_models.model_card import ModelCard
from fairscape_cli.config import NAAN
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid, clean_guid
from fairscape_cli.models.utils import setRelativeFilepath, calculate_md5
import pathlib
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse

def GenerateModel(
    guid: Optional[str] = None,
    name: Optional[str] = None,
    filepath: Optional[str] = None,
    cratePath: Optional[str] = None,
    **kwargs
) -> ModelCard:
    if not guid and name:
        sq = GenerateDatetimeSquid()
        seg = clean_guid(f"{name.lower().replace(' ', '-')}-{sq}")
        guid = f"ark:{NAAN}/model-{seg}"
    elif not guid:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/model-{sq}"
    
    modelMetadata = {
        "@id": guid,
        "name": name,
    }
    
    content_url = None
    if filepath and cratePath:
        content_url = setRelativeFilepath(cratePath, filepath)
    elif filepath:
        content_url = filepath
    
    if content_url:
        modelMetadata['contentUrl'] = content_url
        
        if content_url.startswith('file:///'):
            parsed_url = urlparse(content_url)
            local_path = parsed_url.path
            try:
                md5_hash = calculate_md5(local_path)
                modelMetadata['md5'] = md5_hash
            except (FileNotFoundError, PermissionError, OSError):
                pass
    
    for key, value in kwargs.items():
        if key == "trainingDataset" and value:
            if isinstance(value, str):
                modelMetadata["trainingDataset"] = [{"@id": value.strip("\n")}]
            elif (isinstance(value, list) or isinstance(value, tuple)) and len(value) > 0:
                modelMetadata["trainingDataset"] = [{"@id": item.strip("\n")} for item in value]
        elif key == "generatedBy" and value:
            if isinstance(value, str):
                modelMetadata["generatedBy"] = {"@id": value.strip("\n")}
            elif isinstance(value, dict):
                modelMetadata["generatedBy"] = value
        elif value is not None:
            modelMetadata[key] = value
    
    return ModelCard.model_validate(modelMetadata)
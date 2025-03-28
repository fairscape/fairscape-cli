from pathlib import Path
from typing import Set, Dict, List, Optional, Tuple
import subprocess
import pathlib

from pydantic import ValidationError

from fairscape_cli.models.base import FairscapeBaseModel

def setRelativeFilepath(cratePath, filePath):
    '''Modify the filepath specified in metadata to be relative to the crate'''
    if filePath is None:
        return None

    if 'http' in filePath:
        return filePath

    if 'file:///' in filePath:
        return filePath

    if 'ro-crate-metadata.json' in str(cratePath):
        rocratePath = pathlib.Path(cratePath).parent.absolute()
    else:
        rocratePath = pathlib.Path(cratePath).absolute()
            
    datasetPath = pathlib.Path(filePath).absolute()
    relativePath = datasetPath.relative_to(rocratePath)
    return f"file:///{str(relativePath)}"

def InstantiateModel(ctx, metadata: dict, modelInstance):
    try:
        modelInstance.model_validate(metadata)
        return modelInstance
    except ValidationError as metadataError:
        print('ERROR: MetadataValidationError', end='')
        for validationFailure in metadataError.errors():
            print(f'loc: {validationFailure.loc}\tinput: {validationFailure.input}\tmsg: {validationFailure.msg}', end='')
        ctx.exit(code=1)

class FileNotInCrateException(Exception):
    def __init__(self, cratePath, filePath):
        self.message = f"Error: FileNotFound inside ro crate\ncratePath: {str(cratePath)}\tfilePath{str(filePath)}"
        super().__init__(self.message)

def getDirectoryContents(directory: Path) -> Set[Path]:
    """Get set of all files in directory recursively"""
    return set(p for p in directory.rglob('*') if p.is_file())

def run_command(command: str) -> Tuple[bool, str, str]:
    """Execute command and return success status with output"""
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)
    
def getEntityFromCrate(crate_instance, entity_id: str) -> Optional[FairscapeBaseModel]:
    """Get entity from crate by ID"""
    for entity in crate_instance.metadataGraph:
        if entity.guid == entity_id:
            return entity.dict()
    return None
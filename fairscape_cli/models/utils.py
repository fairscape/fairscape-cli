#  Python Interface for Registering Unique GUIDS
from sqids import Sqids
from pydantic import (
    ValidationError
)
from typing import (
    List
    )
import datetime
from fairscape_cli.config import (
    NAAN
    )

squids = Sqids(min_length=6)


def IntTimestampSquid():
    try:
        timestamp_int = int(datetime.datetime.now(datetime.UTC).timestamp())
        return squids.encode([timestamp_int])
    except: 
        timestamp_int = int(datetime.datetime.utcnow().timestamp())
        return squids.encode([timestamp_int])


def GenerateDatetimeGUID(prefix: str)->str:
    datetime_squid = IntTimestampSquid()
    return f"ark:{NAAN}/{prefix}-{datetime_squid}"

def GenerateGUID(data: List[int], prefix: str)-> str:
    squid_encoded = squids.encode(data)
    return f"ark:{NAAN}/{prefix}-{squid_encoded}"


def InstantiateModel(ctx, metadata: dict, modelInstance):
    try:
        modelInstance.model_validate(metadata)
        return modelInstance
    
    except ValidationError as metadataError:
        print('ERROR: MetadataValidationError', end='')
        for validationFailure in metadataError.errors():
            print(f'loc: {validationFailure.loc}\tinput: {validationFailure.input}\tmsg: {validationFailure.msg}', end='')
        ctx.exit(code=1)



def ValidateGUID(ctx, param, value):
    """ Make sure a GUID reference is reachable return JSON Metadata
    """
    # validate fairscape ARK

    # validate DOI

    # validate url
    pass

from sqids import Sqids
import random
import datetime

from typing import Set, Dict, List, Optional, Tuple

from fairscape_cli.config import NAAN

squids = Sqids(min_length=6)

def GenerateDatetimeSquid():
    try:
        timestamp_int = int(datetime.datetime.now(datetime.UTC).timestamp())
        sq = squids.encode([timestamp_int, random.randint(0, 10000)])
    except:
        timestamp_int = int(datetime.datetime.utcnow().timestamp())
        sq = squids.encode([timestamp_int])
    return sq

def GenerateDatetimeGUID(prefix: str)->str:
    try:
        timestamp_int = int(datetime.datetime.now(datetime.UTC).timestamp())
        sq = squids.encode([timestamp_int])
    except:
        timestamp_int = int(datetime.datetime.utcnow().timestamp())
        sq = squids.encode([timestamp_int])
    return f"ark:{NAAN}/{prefix}-{sq}"

def GenerateGUID(data: List[int], prefix: str)-> str:
    squid_encoded = squids.encode(data)
    return f"ark:{NAAN}/{prefix}-{squid_encoded}"

import re

def clean_guid(segment: str) -> str:
    """
    Cleans a string segment intended for use in a GUID.
    Removes unwanted characters and replaces spaces/multiple dashes with single dashes.
    Allows letters, numbers, single dashes, and forward slashes.
    Converts to lowercase.

    Args:
        segment: The string segment to clean.

    Returns:
        A cleaned string segment suitable for GUID construction.
    """
    if not isinstance(segment, str):
        try:
            segment = str(segment)
        except:
            return "invalid-segment" 

    segment = segment.lower()
    segment = re.sub(r'\s+', ' ', segment)
    segment = segment.replace('.', '-')
    segment = re.sub(r'[^a-z0-9\-/]', '', segment)
    segment = re.sub(r'-+', '-', segment)

    if not segment:
        return "cleaned-empty-segment"

    return segment
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
#  Python Interface for Registering Unique GUIDS
from sqids import Sqids
squids = Sqids(min_length=6)

# TODO set to configuration
NAAN = "ark:59852"

def GenerateGUID(data, prefix):
    squid_encoded = squids.encode(data)
    return f"ark:{NAAN}/{prefix}-{squid_encoded}"
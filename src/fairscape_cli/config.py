from sqids import Sqids

# remote URI for default fairscape requests
FAIRSCAPE_URI = 'https://fairscape.pods.uvarc.io'

# default NAAN for generated GUIDs
NAAN = "59852"

# default context for json-ld
DEFAULT_CONTEXT = { 
    "@vocab": "https://schema.org/",
    "EVI": "https://w3id.org/EVI#"
}

DEFAULT_SCHEMA_TYPE = "EVI:Schema"
DEFAULT_ROCRATE_TYPE = "EVI:ROCrate" 

DEFAULT_SQUIDS = Sqids(min_length=6)
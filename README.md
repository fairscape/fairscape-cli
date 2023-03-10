# fairscape-cli
Data Validation and Packaging utility for sending evidence graphs to FAIRSCAPE

## Functional Description

The fairscape-cli tool is used for client side remote teams to validate and assemble
metadata. 
This tool is a command line interface for use in a command prompt or bash scripts.
It will be used to construct RO crates with full providence preserved in the EVI ontology,
and then transfer them into the fairscape ecosystem.
This requires reserving identifiers, and authenticating against fairscape.

All installation requires is python 3 and using pip to install.
An additional dependancy is sqlite as the tool will maintain a local cached record 
of all metadata records and RO crates assembled.

## User interface

### Validation
```

# take any class or list of objects
# and validate against pydantic
fairscape validate json ./path_to_json.json
```

```
from fairscape-models import Dataset, Computation, Software
import json

def validate_json(filepath):
        """
        expecting just a path to a file
        """

        try:
                json_metadata = json.loads(filepath)
        except Exception as e:
                # handle exception if json file is invalid
                print(e)
                return "error message"

        # is it a list of contents of mixed types
        # handling JSON-LD in multiple forms 
        # example_graph = [
        #        {"@id": "ark:9999/max-levinson", ...},
        #        {"@id": "ark:9999/UVA", ...},
        #        {"@id": "ark:9999/UVA/b2ai", ...},
        # ]

        # handling "@graph" encapsulation
        # example_graph = { "@graph": 
        #   {[
        #        {"@id": "ark:9999/max-levinson", ...},
        #        {"@id": "ark:9999/UVA", ...},
        #        {"@id": "ark:9999/UVA/b2ai", ...},
        #   ]}
        # }
        

        # may want to use jsonld library to fully expand 
        object_type = json_metadata.get("@type")

        
        if object_type is None:
                # cause an error
                pass
        if object_type == "EVI:Computation":
                pass

        # TODO NEXT WEEK: ensure the references are valid
        # for a single object
        # for multiple just iterate

        # check that identifiers exist first looking at the cache 
        # if not in the cache check the network 

        return None
```


```

fairscape validate dataset
fairscape validate software
fairscape validate computation
```

### ROcrate functionality
```
# create a new ROcrate
fairscape rocrate create \
        --id "ark:5982/UVA/b2ai/examplecrate" \
        --name "b2ai example rocrate" \
        --organization "ark:5982/UVA" \
        --project "ark:5982/UVA/b2ai" \
        --path "./"

# remote paths examples
# for github domain
# https://raw.githubusercontent.com/idekerlab/MuSIC/master/Examples/APMS_embedding.MuSIC.csv


# S3
# s3://example-bucket/path/to/object
# http(s)://<bucket>.s3.amazonaws.com/<object>
# http(s)://s3.amazonaws.com/<bucket>/<object>

# local s3

# identifier
# e.g. Zenodo DOI

# external filesystems i.e. RIVANNA project storage
# smb://qumulo.rc.virginia.edu/
```

```

import pathlib.Path as Path 
from fairscape-models import rocrate

def getsqliteconn():
        pass

def create_ro_crate(*args, **kwargs):

        name=kargs.get("name")


        try: 
                rocrate_model = rocrate(
                        name=name,
                )

        except ValidationError as e:
                # pretty print the validation errors
                print(e)

        rocrate_path = kwargs.get("path")
        Path(rocrate_path).mkdir()

        # persist in the sqlite cache
        sqlite_connection = getsqliteconn()
        
        # insert one record into rocrate table
        

        return None
         
```


```

fairscape rocrate add dataset \
        --crateid "ark:5982/UVA/b2ai/examplecrate" \
        --id "ark:5982/UVA/b2ai/examplecrate/test-dataset" \
        --name "MuSIC software" \
        --source <PATH>

fairscape rocrate add software \
        --crateid "ark:5982/UVA/b2ai/examplecrate" \
        --id "ark:5982/UVA/b2ai/examplecrate/MuSIC" \
        --name "MuSIC software" \
        --source "https://github.com/idekerlab/MuSIC" 

fairscape rocrate add computation \
        --crateid "ark:5982/UVA/b2ai/examplecrate" \
        --id "ark:5982/UVA/b2ai/examplecrate/test-computation" \
        --name "b2ai computation" \
        --usedSoftware "ark:5982/UVA/b2ai/examplecrate/MuSIC" \
        --usedDataset "ark:5982/UVA/b2ai/examplecrate/test-dataset" \
        --generated "ark:5982/UVA/b2ai/examplecrate/test-results"

fairscape rocrate dumpmetadata

fairscape rocrate hash --id <CRATEID>

# creating gzipped output of full ROcrate with metadata
fairscape rocrate package --output-path ./

# list ROcrates
fairscape list ROcrate
fairscape describe ROcrate --id --name


# describe identifier metadata
fairscape describe --id "ark:5982/UVA/b2ai"
fairscape describe --name "b2ai computation"
```

Improving UX by removing arguments from previous commands

```
fairscape rocrate create ... --path ./myrocrate

cd myrocrate

# there is a hidden file created
# ./myrocrate/.metadata.sqlite
# it could be on another path
# has metadata on the following
#  - organization
#  - project
#  - author

fairscape add dataset ... --path /mnt/results/mytestfile.csv

# fairscape has every enough to auto generate identifiers
# ark:5982/<ORGANIZATION>/<PROJECT>/<ROCRATE>/postfix

fairscape setcontext crateid --id <CRATEID>

fairscape rocrate add compution/dataset/software/etc... 
```



## Milestones

- 02-23
  - [ ] validate json command
  - [ ] pypi package for classes based on linkml description


- 02-25
  - [ ] validate software
  - [ ] validate dataset
  - [ ] validate computation

- 02-27
  - [ ] ROcrate create
  - [ ] ROcrate add software
  - [ ] ROcrate add dataset
  - [ ] ROcrate add computation

- 02-28
  - [ ] ROcrate hash
  - [ ] list ROcrate
  - [ ] describe ROcrate

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


### Validating Individual Classes
```
fairscape validate dataset ./tests/data/dataset.json
fairscape validate software ./tests/data/software.json
fairscape validate computation ./tests/data/computation.json
```

## ROCrate
```
# create a new ROcrate
fairscape rocrate create \
        --id "ark:5982/UVA/b2ai/examplecrate" \
        --name "b2ai example rocrate" \
        --organization "ark:5982/UVA" \
        --project "ark:5982/UVA/b2ai" \
        --path "./tests/example_rocrate"

```

### Adding Contents 

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

# fairscape has every parameter required to auto generate identifiers
# ark:5982/<ORGANIZATION>/<PROJECT>/<ROCRATE>/postfix

fairscape setcontext crateid --id <CRATEID>

fairscape rocrate add compution/dataset/software/etc... 
```

### Design Considerations

#### Dealing with Remote Content

remote paths examples
1. github domain
  - https://raw.githubusercontent.com/idekerlab/MuSIC/master/Examples/APMS_embedding.MuSIC.csv

2. S3
- s3://example-bucket/path/to/object
- `http(s)://<bucket>.s3.amazonaws.com/<object>`
- http(s)://s3.amazonaws.com/<bucket>/<object>

3. Local File URI

4. identifier
- Zenodo DOI

5. external filesystems 
- RIVANNA project storage smb://qumulo.rc.virginia.edu/
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

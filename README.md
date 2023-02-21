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
fairscape validate json ./path_to_json.json

fairscape validate dataset
fairscape validate software
fairscape validate computation
```

### ROcrate functionality
```
# create a new ROcrate
fairscape ROcrate create \
        --id "ark:5982/UVA/b2ai/examplecrate" \
        --name "b2ai example rocrate" \
        --organization "ark:5982/UVA" \
        --project "ark:5982/UVA/b2ai" \
        --path "./"


fairscape ROcrate add dataset \
        --crateid "ark:5982/UVA/b2ai/examplecrate" \
        --id "ark:5982/UVA/b2ai/examplecrate/test-dataset" \
        --name "MuSIC software" \
        --source "https://github.com/idekerlab/MuSIC" 

fairscape ROcrate add software \
        --crateid "ark:5982/UVA/b2ai/examplecrate" \
        --id "ark:5982/UVA/b2ai/examplecrate/MuSIC" \
        --name "MuSIC software" \
        --source "https://github.com/idekerlab/MuSIC" 

fairscape ROcrate add computation \
        --crateid "ark:5982/UVA/b2ai/examplecrate" \
        --id "ark:5982/UVA/b2ai/examplecrate/test-computation" \
        --name "b2ai computation" \
        --usedSoftware "ark:5982/UVA/b2ai/examplecrate/MuSIC" \
        --usedDataset "ark:5982/UVA/b2ai/examplecrate/test-dataset" \
        --generated "ark:5982/UVA/b2ai/examplecrate/test-results"

fairscape ROcrate hash --id <CRATEID>

# list ROcrates
fairscape list ROcrate
fairscape describe ROcrate --id --name


# describe identifier metadata
fairscape describe --id "ark:5982/UVA/b2ai"
fairscape describe --name "b2ai computation"
```

## Milestones

- [ ] 02-23
        - [ ] validate json command
        - [ ] pypi package for classes based on linkml description
- [ ] 02-25
        - [ ] validate software
        - [ ] validate dataset
        - [ ] validate computation
- [ ] 02-27
        - [ ] ROcrate create
        - [ ] ROcrate add software
        - [ ] ROcrate add dataset
        - [ ] ROcrate add computation
- [ ] 02-28
        - [ ] ROcrate hash
        - [ ] list ROcrate
        - [ ] describe ROcrate

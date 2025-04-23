# fairscape-cli

A utility for packaging objects and validating metadata for FAIRSCAPE.

---

## **Documentation**: [https://fairscape.github.io/fairscape-cli/](https://fairscape.github.io/fairscape-cli/)

## Features

fairscape-cli provides a Command Line Interface (CLI) that allows the client side to create, manage, and publish scientific data packages:

- **RO-Crate Management:** Create and manipulate [RO-Crate](https://www.researchobject.org/ro-crate/) packages locally.
  - Initialize RO-Crates in new or existing directories.
  - Add data, software, and computation metadata.
  - Copy files into the crate structure alongside metadata registration.
- **Schema Handling:** Define, infer, and validate data schemas (Tabular, HDF5).
  - Create schema definition files.
  - Add properties with constraints.
  - Infer schemas directly from data files.
  - Validate data files against specified schemas.
  - Register schemas within RO-Crates.
- **Data Import:** Fetch data from external sources and convert them into RO-Crates.
  - Import NCBI BioProjects.
  - Convert Portable Encapsulated Projects (PEPs) to RO-Crates.
- **Build Artifacts:** Generate derived outputs from RO-Crates.
  - Create detailed HTML datasheets summarizing crate contents.
  - Generate provenance evidence graphs (JSON and HTML).
- **Release Management:** Organize multiple related RO-Crates into a cohesive release package.
  - Initialize a release structure.
  - Automatically link sub-crates and propagate metadata.
  - Build a top-level datasheet for the release.
- **Publishing:** Publish RO-Crate metadata to external repositories.
  - Upload RO-Crate directories or zip files to Fairscape.
  - Create datasets on Dataverse instances.
  - Mint or update DOIs on DataCite.

## Requirements

Python 3.8+

## Installation

```console
$ pip install fairscape-cli
```

## Command Overview

The CLI is organized into several top-level commands:

    rocrate: Core local RO-Crate manipulation (create, add files/metadata).

    schema: Operations on data schemas (create, infer, add properties, add to crate).

    validate: Validate data against schemas.

    import: Fetch external data into RO-Crate format (e.g., bioproject, pep).

    build: Generate outputs from RO-Crates (e.g., datasheet, evidence-graph).

    release: Manage multi-part RO-Crate releases (e.g., create, build).

    publish: Publish RO-Crates to repositories (e.g., fairscape, dataverse, doi).

Use --help for details on any command or subcommand:

```console
$ fairscape-cli --help
$ fairscape-cli rocrate --help
$ fairscape-cli rocrate add --help
$ fairscape-cli schema create --help
```

## Examples

### Creating an RO-Crate

Create an RO-Crate in a specified directory:

```console
$ fairscape-cli rocrate create \
    --name "My Analysis Crate" \
    --description "RO-Crate containing analysis scripts and results" \
    --organization-name "My Org" \
    --project-name "My Project" \
    --keywords "analysis" \
    --keywords "python" \
    --author "Jane Doe" \
    --version "1.1.0" \
    ./my_analysis_crate
```

Initialize an RO-Crate in the current working directory:

```console
# Navigate to an empty directory first if desired
# mkdir my_analysis_crate && cd my_analysis_crate

$ fairscape-cli rocrate init \
    --name "My Analysis Crate" \
    --description "RO-Crate containing analysis scripts and results" \
    --organization-name "My Org" \
    --project-name "My Project" \
    --keywords "analysis" \
    --keywords "python"
```

### Adding Content and Metadata to an RO-Crate

These commands support adding both the file and its metadata (add) or just the metadata (register).

Add a dataset file and its metadata:

```console
$ fairscape-cli rocrate add dataset \
    --name "Raw Measurements" \
    --author "John Smith" \
    --version "1.0" \
    --date-published "2023-10-27" \
    --description "Raw sensor measurements from Experiment A." \
    --keywords "raw-data" \
    --keywords "sensors" \
    --data-format "csv" \
    --source-filepath "./source_data/measurements.csv" \
    --destination-filepath "data/measurements.csv" \
    ./my_analysis_crate
```

Add a software script file and its metadata:

```console
$ fairscape-cli rocrate add software \
    --name "Analysis Script" \
    --author "Jane Doe" \
    --version "1.1.0" \
    --description "Python script for processing raw measurements." \
    --keywords "analysis" \
    --keywords "python" \
    --file-format "py" \
    --source-filepath "./scripts/process_data.py" \
    --destination-filepath "scripts/process_data.py" \
    ./my_analysis_crate
```

Register computation metadata (metadata only):

```console
# Assuming the script and dataset were added previously and have GUIDs:
# Dataset GUID: ark:59852/dataset-raw-measurements-xxxx
# Software GUID: ark:59852/software-analysis-script-yyyy

$ fairscape-cli rocrate register computation \
    --name "Data Processing Run" \
    --run-by "Jane Doe" \
    --date-created "2023-10-27T14:30:00Z" \
    --description "Execution of the analysis script on the raw measurements." \
    --keywords "processing" \
    --used-dataset "ark:59852/dataset-raw-measurements-xxxx" \
    --used-software "ark:59852/software-analysis-script-yyyy" \
    --generated "ark:59852/dataset-processed-results-zzzz" \
    ./my_analysis_crate

# Note: You would typically register the generated dataset ('processed-results') separately.
```

Register dataset metadata (metadata only, file assumed present or external):

```console
$ fairscape-cli rocrate register dataset \
    --name "Processed Results" \
    --guid "ark:59852/dataset-processed-results-zzzz" \
    --author "Jane Doe" \
    --version "1.0" \
    --description "Processed results from the analysis script." \
    --keywords "results" \
    --data-format "csv" \
    --filepath "results/processed.csv" \
    --generated-by "ark:59852/computation-data-processing-run-wwww" \
    ./my_analysis_crate
```

### Schema Management

Create a tabular schema definition file:

```console
$ fairscape-cli schema create \
    --name 'Measurement Schema' \
    --description 'Schema for raw sensor measurements' \
    --schema-type tabular \
    --separator ',' \
    --header true \
    ./measurement_schema.json
```

Add properties to the tabular schema file:

```console
# Add a string property (column 0)
$ fairscape-cli schema add-property string \
    --name 'Timestamp' \
    --index 0 \
    --description 'Measurement time (ISO8601)' \
    ./measurement_schema.json

# Add a number property (column 1)
$ fairscape-cli schema add-property number \
    --name 'Value' \
    --index 1 \
    --description 'Sensor reading' \
    --minimum 0 \
    ./measurement_schema.json
```

Infer a schema from an existing data file:

```console
$ fairscape-cli schema infer \
    --name "Inferred Results Schema" \
    --description "Schema inferred from processed results" \
    ./my_analysis_crate/results/processed.csv \
    ./processed_schema.json
```

Add an existing schema file to an RO-Crate:

```console
$ fairscape-cli schema add-to-crate \
    ./measurement_schema.json \
    ./my_analysis_crate
```

### Validation

Validate a data file against a schema file:

```console
# Successful validation
$ fairscape-cli validate schema \
    --schema-path ./measurement_schema.json \
    --data-path ./my_analysis_crate/data/measurements.csv

# Example failure
$ fairscape-cli validate schema \
    --schema-path ./measurement_schema.json \
    --data-path ./source_data/measurements_invalid.csv
```

### Importing Data

Import an NCBI BioProject into a new RO-Crate:

```console
$ fairscape-cli import bioproject \
    --accession PRJNA123456 \
    --author "Importer Name" \
    --output-dir ./bioproject_prjna123456_crate \
    --crate-name "Imported BioProject PRJNA123456"
```

Convert a PEP project to an RO-Crate:

```console
$ fairscape-cli import pep \
    ./path/to/my_pep_project \
    --output-path ./my_pep_rocrate \
    --crate-name "My PEP Project Crate"
```

### Building Outputs

Generate an HTML datasheet for an RO-Crate:

```console
$ fairscape-cli build datasheet ./my_analysis_crate
# Output will be ./my_analysis_crate/ro-crate-datasheet.html by default
```

Generate a provenance graph for a specific item within the crate:

```console
# Assuming 'ark:59852/dataset-processed-results-zzzz' is the item of interest
$ fairscape-cli build evidence-graph \
    ./my_analysis_crate \
    ark:59852/dataset-processed-results-zzzz \
    --output-json ./my_analysis_crate/prov/results_prov.json \
    --output-html ./my_analysis_crate/prov/results_prov.html
```

### Release Management

Create the structure for a multi-part release:

```console
$ fairscape-cli release create \
    --name "My Big Release Q4 2023" \
    --description "Combined release of Experiment A and Experiment B crates" \
    --organization-name "My Org" \
    --project-name "Overall Project" \
    --keywords "release" \
    --keywords "experiment-a" \
    --keywords "experiment-b" \
    --version "2.0" \
    --author "Release Manager" \
    --publisher "My Org Publishing" \
    ./my_big_release

# Manually copy or move your individual RO-Crate directories (e.g., experiment_a_crate, experiment_b_crate)
# into the ./my_big_release directory now.
```

Build the release (link sub-crates, update metadata, generate datasheet):

```console
$ fairscape-cli release build ./my_big_release
```

### Publishing

Upload an RO-Crate to Fairscape:

```console
# Ensure FAIRSCAPE_USERNAME and FAIRSCAPE_PASSWORD are set as environment variables or use options
$ fairscape-cli publish fairscape \
    --rocrate ./my_analysis_crate \
    --username <your_username> \
    --password <your_password>

# Works with either directories or zip files
$ fairscape-cli publish fairscape \
    --rocrate ./my_analysis_crate.zip \
    --username <your_username> \
    --password <your_password> \
    --api-url https://fairscape.example.edu/api
```

Publish RO-Crate metadata to Dataverse:

```console
# Ensure DATAVERSE_API_TOKEN is set as an environment variable or use --token
$ fairscape-cli publish dataverse \
    --rocrate ./my_analysis_crate/ro-crate-metadata.json \
    --url https://my.dataverse.instance.edu \
    --collection my_collection_alias \
    --token <your_api_token>
```

Mint a DOI using DataCite:

```console
# Ensure DATACITE_USERNAME and DATACITE_PASSWORD are set or use options
$ fairscape-cli publish doi \
    --rocrate ./my_analysis_crate/ro-crate-metadata.json \
    --prefix 10.1234 \
    --username MYORG.MYREPO \
    --password <your_api_password> \
    --event publish # or 'register' for draft
```

## Contribution

If you'd like to request a feature or report a bug, please create a GitHub Issue using one of the templates provided.

## License

This project is licensed under the terms of the MIT license.

# RO-Crate Commands

This document provides detailed information about the RO-Crate commands available in fairscape-cli.

## Overview

The `rocrate` command group provides operations for creating and manipulating Research Object Crates (RO-Crates). RO-Crates are a lightweight approach to packaging research data with their metadata, making them more FAIR (Findable, Accessible, Interoperable, and Reusable).

```bash
fairscape-cli rocrate [COMMAND] [OPTIONS]
```

## Available Commands

- [`create`](#create) - Create a new RO-Crate in a specified directory
- [`init`](#init) - Initialize an RO-Crate in the current working directory
- [`register`](#register) - Add metadata to an existing RO-Crate
    - [`dataset`](#register-dataset) - Register dataset metadata
    - [`software`](#register-software) - Register software metadata
    - [`computation`](#register-computation) - Register computation metadata
    - [`sample`](#register-sample) - Register sample metadata
    - [`instrument`](#register-instrument) - Register instrument metadata
    - [`experiment`](#register-experiment) - Register experiment metadata
    - [`subrocrate`](#register-subrocrate) - Register a new RO-Crate within an existing RO-Crate
- [`add`](#add) - Add a file to the RO-Crate and register its metadata
    - [`dataset`](#add-dataset) - Add a dataset file and its metadata
    - [`software`](#add-software) - Add a software file and its metadata

## Command Details

### `create`

Create a new RO-Crate in a specified directory.

```bash
fairscape-cli rocrate create [OPTIONS] ROCRATE_PATH
```

**Options:**

- `--guid TEXT` - Optional custom identifier for the RO-Crate
- `--name TEXT` - Name of the RO-Crate [required]
- `--organization-name TEXT` - Name of the organization [required]
- `--project-name TEXT` - Name of the project [required]
- `--description TEXT` - Description of the RO-Crate [required]
- `--keywords TEXT` - Keywords (can be specified multiple times) [required]
- `--license TEXT` - License URL (default: "https://creativecommons.org/licenses/by/4.0/")
- `--date-published TEXT` - Publication date (ISO format)
- `--author TEXT` - Author name (default: "Unknown")
- `--version TEXT` - Version number (default: "1.0")
- `--associated-publication TEXT` - Associated publication
- `--conditions-of-access TEXT` - Conditions of access
- `--copyright-notice TEXT` - Copyright notice
- `--custom-properties TEXT` - JSON string with additional properties to include

**Example:**

```bash
fairscape-cli rocrate create \
  --name "test rocrate" \
  --description "Example RO Crate for Tests" \
  --organization-name "UVA" \
  --project-name "B2AI"  \
  --keywords "b2ai" \
  --keywords "cm4ai" \
  "./test_rocrate"
```

### `init`

Initialize an RO-Crate in the current working directory.

```bash
fairscape-cli rocrate init [OPTIONS]
```

**Options:**
The same options as for the `create` command are available. The difference is that `init` creates the RO-Crate in the current working directory.

**Example:**

```bash
fairscape-cli rocrate init \
  --name "test rocrate" \
  --description "Example RO Crate for Tests" \
  --organization-name "UVA" \
  --project-name "B2AI"  \
  --keywords "b2ai" \
  --keywords "cm4ai"
```

### `register`

Add metadata to an existing RO-Crate. This command has several subcommands depending on the type of metadata to register.

#### `register dataset`

Register dataset metadata with an existing RO-Crate.

```bash
fairscape-cli rocrate register dataset [OPTIONS] ROCRATE_PATH
```

**Options:**

- `--guid TEXT` - Optional custom identifier for the dataset
- `--name TEXT` - Name of the dataset [required]
- `--author TEXT` - Author of the dataset [required]
- `--version TEXT` - Version of the dataset [required]
- `--description TEXT` - Description of the dataset [required]
- `--keywords TEXT` - Keywords (can be specified multiple times) [required]
- `--data-format TEXT` - Format of the dataset (e.g., csv, json) [required]
- `--filepath TEXT` - Path to the dataset file (relative to crate root)
- `--content-url TEXT` - URL to the dataset file (if hosted externally)
- `--embargoed` - Flag indicating the dataset is embargoed (default: false)
- `--url TEXT` - URL reference for the dataset
- `--date-published TEXT` - Publication date of the dataset (ISO format) [required]
- `--schema TEXT` - Schema identifier for the dataset
- `--used-by TEXT` - Identifiers of computations that use this dataset (can be specified multiple times)
- `--derived-from TEXT` - Identifiers of datasets this one is derived from (can be specified multiple times)
- `--generated-by TEXT` - Identifiers of computations that generated this dataset (can be specified multiple times)
- `--summary-statistics-filepath TEXT` - Path to summary statistics file
- `--associated-publication TEXT` - Associated publication identifier
- `--additional-documentation TEXT` - Additional documentation
- `--custom-properties TEXT` - JSON string with additional properties to include

**File Location Options:**
You must specify exactly one of the following options to indicate where the dataset is located:

- `--filepath` - For datasets stored within the RO-Crate
- `--content-url` - For datasets hosted externally at a URL
- `--embargoed` - For datasets that are embargoed/restricted

If multiple options are provided, they are prioritized in this order: `filepath` > `content-url` > `embargoed`.

**Example:**

```bash
# Register a dataset file within the crate
fairscape-cli rocrate register dataset \
  --name "AP-MS embeddings" \
  --author "Krogan lab" \
  --version "1.0" \
  --date-published "2023-04-23" \
  --description "APMS embeddings for each protein" \
  --keywords "proteomics" \
  --data-format "CSV" \
  --filepath "./test_rocrate/embeddings.csv" \
  "./test_rocrate"

# Register an external dataset
fairscape-cli rocrate register dataset \
  --name "External Dataset" \
  --author "External Provider" \
  --version "1.0" \
  --date-published "2023-04-23" \
  --description "Dataset hosted externally" \
  --keywords "external" \
  --data-format "CSV" \
  --content-url "https://example.com/dataset.csv" \
  "./test_rocrate"

# Register an embargoed dataset
fairscape-cli rocrate register dataset \
  --name "Embargoed Dataset" \
  --author "Research Team" \
  --version "1.0" \
  --date-published "2023-04-23" \
  --description "Dataset under embargo" \
  --keywords "embargoed" \
  --data-format "CSV" \
  --embargoed \
  "./test_rocrate"
```

#### `register software`

Register software metadata with an existing RO-Crate.

```bash
fairscape-cli rocrate register software [OPTIONS] ROCRATE_PATH
```

**Options:**

- `--guid TEXT` - Optional custom identifier for the software
- `--name TEXT` - Name of the software [required]
- `--author TEXT` - Author of the software [required]
- `--version TEXT` - Version of the software [required]
- `--description TEXT` - Description of the software [required]
- `--keywords TEXT` - Keywords (can be specified multiple times) [required]
- `--file-format TEXT` - Format of the software (e.g., py, js) [required]
- `--url TEXT` - URL reference for the software
- `--date-modified TEXT` - Last modification date of the software (ISO format)
- `--filepath TEXT` - Path to the software file (relative to crate root)
- `--content-url TEXT` - URL to the software file (if hosted externally)
- `--embargoed` - Flag indicating the software is embargoed (default: false)
- `--used-by-computation TEXT` - Identifiers of computations that use this software (can be specified multiple times)
- `--associated-publication TEXT` - Associated publication identifier
- `--additional-documentation TEXT` - Additional documentation
- `--custom-properties TEXT` - JSON string with additional properties

**File Location Options:**
You must specify exactly one of the following options to indicate where the software is located:

- `--filepath` - For software stored within the RO-Crate
- `--content-url` - For software hosted externally at a URL
- `--embargoed` - For software that is embargoed/restricted

If multiple options are provided, they are prioritized in this order: `filepath` > `content-url` > `embargoed`.

**Example:**

```bash
# Register software file within the crate
fairscape-cli rocrate register software \
  --name "calibrate pairwise distance" \
  --author "Qin, Y." \
  --version "1.0" \
  --description "script written in python to calibrate pairwise distance." \
  --keywords "b2ai" \
  --file-format "py" \
  --filepath "./test_rocrate/calibrate_pairwise_distance.py" \
  --date-modified "2023-04-23" \
  "./test_rocrate"

# Register external software
fairscape-cli rocrate register software \
  --name "External Analysis Tool" \
  --author "External Developer" \
  --version "2.1" \
  --description "Analysis tool hosted on GitHub" \
  --keywords "analysis" \
  --file-format "py" \
  --content-url "https://github.com/user/repo/blob/main/analysis.py" \
  --date-modified "2023-04-23" \
  "./test_rocrate"

# Register embargoed software
fairscape-cli rocrate register software \
  --name "Proprietary Algorithm" \
  --author "Research Team" \
  --version "1.0" \
  --description "Proprietary analysis algorithm" \
  --keywords "proprietary" \
  --file-format "py" \
  --embargoed \
  --date-modified "2023-04-23" \
  "./test_rocrate"
```

#### `register computation`

Register computation metadata with an existing RO-Crate.

```bash
fairscape-cli rocrate register computation [OPTIONS] ROCRATE_PATH
```

**Options:**

- `--guid TEXT` - Optional custom identifier for the computation
- `--name TEXT` - Name of the computation [required]
- `--run-by TEXT` - Person or entity that ran the computation [required]
- `--command TEXT` - Command used to run the computation (string or JSON list)
- `--date-created TEXT` - Date the computation was run (ISO format) [required]
- `--description TEXT` - Description of the computation [required]
- `--keywords TEXT` - Keywords (can be specified multiple times) [required]
- `--used-software TEXT` - Software identifiers used by this computation (can be specified multiple times)
- `--used-dataset TEXT` - Dataset identifiers used by this computation (can be specified multiple times)
- `--generated TEXT` - Dataset/Software identifiers generated by this computation (can be specified multiple times)
- `--associated-publication TEXT` - Associated publication identifier
- `--additional-documentation TEXT` - Additional documentation
- `--custom-properties TEXT` - JSON string with additional properties

**Example:**

```bash
fairscape-cli rocrate register computation \
  --name "calibrate pairwise distance" \
  --run-by "Qin, Y." \
  --date-created "2023-05-23" \
  --description "Average the predicted proximities" \
  --keywords "b2ai" \
  --keywords "cm4ai" \
  "./test_rocrate"
```

#### `register sample`

Register sample metadata with an existing RO-Crate.

```bash
fairscape-cli rocrate register sample [OPTIONS] ROCRATE_PATH
```

**Options:**

- `--guid TEXT` - Optional custom identifier for the sample
- `--name TEXT` - Name of the sample [required]
- `--author TEXT` - Author or creator of the sample [required]
- `--description TEXT` - Description of the sample [required]
- `--keywords TEXT` - Keywords (can be specified multiple times) [required]
- `--filepath TEXT` - Path to the sample documentation file
- `--cell-line-reference TEXT` - Reference to the cell line used
- `--custom-properties TEXT` - JSON string with additional properties

**Example:**

```bash
fairscape-cli rocrate register sample \
  --name "HeLa Cell Sample" \
  --author "Lab Technician" \
  --description "HeLa cells prepared for proteomics analysis" \
  --keywords "cell-culture" \
  --keywords "proteomics" \
  --cell-line-reference "ATCC CCL-2" \
  "./test_rocrate"
```

#### `register instrument`

Register instrument metadata with an existing RO-Crate.

```bash
fairscape-cli rocrate register instrument [OPTIONS] ROCRATE_PATH
```

**Options:**

- `--guid TEXT` - Optional custom identifier for the instrument
- `--name TEXT` - Name of the instrument [required]
- `--manufacturer TEXT` - Manufacturer of the instrument [required]
- `--model TEXT` - Model number/name of the instrument [required]
- `--description TEXT` - Description of the instrument [required]
- `--filepath TEXT` - Path to instrument documentation file
- `--used-by-experiment TEXT` - Identifiers of experiments using this instrument (can be specified multiple times)
- `--associated-publication TEXT` - Associated publication identifier
- `--additional-documentation TEXT` - Additional documentation
- `--custom-properties TEXT` - JSON string with additional properties

**Example:**

```bash
fairscape-cli rocrate register instrument \
  --name "Mass Spectrometer MS-1000" \
  --manufacturer "Thermo Fisher Scientific" \
  --model "Orbitrap Fusion Lumos" \
  --description "High-resolution mass spectrometer for proteomics" \
  --filepath "./instruments/ms1000_manual.pdf" \
  "./test_rocrate"
```

#### `register experiment`

Register experiment metadata with an existing RO-Crate.

```bash
fairscape-cli rocrate register experiment [OPTIONS] ROCRATE_PATH
```

**Options:**

- `--guid TEXT` - Optional custom identifier for the experiment
- `--name TEXT` - Name of the experiment [required]
- `--experiment-type TEXT` - Type of experiment conducted [required]
- `--run-by TEXT` - Person or entity that ran the experiment [required]
- `--description TEXT` - Description of the experiment [required]
- `--date-performed TEXT` - Date the experiment was performed (ISO format) [required]
- `--used-instrument TEXT` - Instrument identifiers used in this experiment (can be specified multiple times)
- `--used-sample TEXT` - Sample identifiers used in this experiment (can be specified multiple times)
- `--used-treatment TEXT` - Treatment identifiers used in this experiment (can be specified multiple times)
- `--used-stain TEXT` - Stain identifiers used in this experiment (can be specified multiple times)
- `--generated TEXT` - Identifiers of entities generated by this experiment (can be specified multiple times)
- `--protocol TEXT` - Protocol identifier or description
- `--associated-publication TEXT` - Associated publication identifier
- `--custom-properties TEXT` - JSON string with additional properties

**Example:**

```bash
fairscape-cli rocrate register experiment \
  --name "Proteomics Analysis Experiment" \
  --experiment-type "Mass Spectrometry" \
  --run-by "Research Team" \
  --description "Comprehensive proteomics analysis of cell samples" \
  --date-performed "2023-05-15" \
  --used-instrument "ark:/12345/instrument-1" \
  --used-sample "ark:/12345/sample-1" \
  --protocol "Standard MS Protocol v2.1" \
  "./test_rocrate"
```

#### `register subrocrate`

Register a new RO-Crate within an existing RO-Crate directory.

```bash
fairscape-cli rocrate register subrocrate [OPTIONS] ROCRATE_PATH SUBROCRATE_PATH
```

**Options:**

- `--guid TEXT` - Optional custom identifier for the sub-crate
- `--name TEXT` - Name of the sub-crate [required]
- `--organization-name TEXT` - Name of the organization [required]
- `--project-name TEXT` - Name of the project [required]
- `--description TEXT` - Description of the sub-crate [required]
- `--keywords TEXT` - Keywords (can be specified multiple times) [required]
- `--author TEXT` - Author name (default: "Unknown")
- `--version TEXT` - Version number (default: "1.0")
- `--license TEXT` - License URL (default: "https://creativecommons.org/licenses/by/4.0/")

**Example:**

```bash
fairscape-cli rocrate register subrocrate \
  --name "Sub-Crate Example" \
  --organization-name "UVA" \
  --project-name "B2AI" \
  --description "A sub-crate within the main RO-Crate" \
  --keywords "sub-crate" \
  "./test_rocrate" "./test_rocrate/sub_crate"
```

### `add`

Add a file to the RO-Crate and register its metadata. This command copies local files into the RO-Crate directory structure and registers their metadata.

#### `add dataset`

Add a dataset file and its metadata to an RO-Crate.

```bash
fairscape-cli rocrate add dataset [OPTIONS] ROCRATE_PATH
```

**Options:**

- `--guid TEXT` - Optional custom identifier for the dataset
- `--name TEXT` - Name of the dataset [required]
- `--author TEXT` - Author of the dataset [required]
- `--version TEXT` - Version of the dataset (default: "1.0")
- `--description TEXT` - Description of the dataset [required]
- `--keywords TEXT` - Keywords (can be specified multiple times) [required]
- `--data-format TEXT` - Format of the dataset (e.g., csv, json) [required]
- `--source-filepath TEXT` - Path to the source dataset file on your local filesystem [required]
- `--destination-filepath TEXT` - Path where the dataset file will be copied in the RO-Crate [required]
- `--url TEXT` - URL reference for the dataset
- `--date-published TEXT` - Publication date of the dataset (ISO format)
- `--schema TEXT` - Schema identifier for the dataset
- `--used-by TEXT` - Identifiers of computations that use this dataset (can be specified multiple times)
- `--derived-from TEXT` - Identifiers of datasets this one is derived from (can be specified multiple times)
- `--generated-by TEXT` - Identifiers of computations that generated this dataset (can be specified multiple times)
- `--summary-statistics-source TEXT` - Path to source summary statistics file on your local filesystem
- `--summary-statistics-destination TEXT` - Path where summary statistics file will be copied in the RO-Crate
- `--associated-publication TEXT` - Associated publication identifier
- `--additional-documentation TEXT` - Additional documentation
- `--custom-properties TEXT` - JSON string with additional properties

**Example:**

```bash
fairscape-cli rocrate add dataset \
  --name "AP-MS embeddings" \
  --author "Krogan lab" \
  --version "1.0" \
  --date-published "2023-04-23" \
  --description "APMS embeddings for each protein" \
  --keywords "proteomics" \
  --data-format "CSV" \
  --source-filepath "./data/embeddings.csv" \
  --destination-filepath "./test_rocrate/embeddings.csv" \
  "./test_rocrate"
```

#### `add software`

Add a software file and its metadata to an RO-Crate.

```bash
fairscape-cli rocrate add software [OPTIONS] ROCRATE_PATH
```

**Options:**

- `--guid TEXT` - Optional custom identifier for the software
- `--name TEXT` - Name of the software [required]
- `--author TEXT` - Author of the software [required]
- `--version TEXT` - Version of the software [required]
- `--description TEXT` - Description of the software [required]
- `--keywords TEXT` - Keywords (can be specified multiple times) [required]
- `--file-format TEXT` - Format of the software (e.g., py, js) [required]
- `--url TEXT` - URL reference for the software
- `--source-filepath TEXT` - Path to the source software file on your local filesystem [required]
- `--destination-filepath TEXT` - Path where the software file will be copied in the RO-Crate [required]
- `--date-modified TEXT` - Last modification date of the software (ISO format)
- `--used-by-computation TEXT` - Identifiers of computations that use this software (can be specified multiple times)
- `--associated-publication TEXT` - Associated publication identifier
- `--additional-documentation TEXT` - Additional documentation
- `--custom-properties TEXT` - JSON string with additional properties

**Example:**

```bash
fairscape-cli rocrate add software \
  --name "calibrate pairwise distance" \
  --author "Qin, Y." \
  --version "1.0" \
  --description "script written in python to calibrate pairwise distance." \
  --keywords "b2ai" \
  --file-format "py" \
  --source-filepath "./scripts/calibrate_pairwise_distance.py" \
  --destination-filepath "./test_rocrate/calibrate_pairwise_distance.py" \
  --date-modified "2023-04-23" \
  "./test_rocrate"
```

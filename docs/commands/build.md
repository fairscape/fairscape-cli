# Build Commands

This document provides detailed information about the build commands available in fairscape-cli.

## Overview

The `build` command group provides operations for generating derived artifacts from RO-Crates and creating release packages. These artifacts include datasheets, visualizations, evidence graphs, and release RO-Crates that make the content more accessible and understandable.

```bash
fairscape-cli build [COMMAND] [OPTIONS]
```

## Available Commands

- [`datasheet`](#datasheet) - Generate an HTML datasheet for an RO-Crate
- [`evidence-graph`](#evidence-graph) - Generate a provenance graph for a specific ARK identifier
- [`release`](#release) - Build a release RO-Crate from a directory containing multiple RO-Crates

## Command Details

### `datasheet`

Generate an HTML datasheet for an RO-Crate, providing a human-readable summary of its content.

```bash
fairscape-cli build datasheet [OPTIONS] ROCRATE_PATH
```

**Arguments:**

- `ROCRATE_PATH` - Path to the RO-Crate directory or metadata file [required]

**Options:**

- `--output PATH` - Output HTML file path (defaults to ro-crate-datasheet.html in crate directory)
- `--template-dir PATH` - Custom template directory
- `--published` - Indicate if the crate is considered published (may affect template rendering)

**Example:**

```bash
fairscape-cli build datasheet ./my_rocrate
```

This command:

1. Reads the RO-Crate metadata
2. Processes any subcrates
3. Generates a comprehensive HTML datasheet
4. Saves the datasheet in the specified location (or default location)

The datasheet includes:

- General metadata (title, authors, description)
- Datasets included in the crate
- Software included in the crate
- Computations documented in the crate
- Provenance relationships between elements
- References to external resources
- Information about subcrates (if any)

### `evidence-graph`

Generate a provenance graph for a specific ARK identifier within an RO-Crate.

```bash
fairscape-cli build evidence-graph [OPTIONS] ROCRATE_PATH ARK_ID
```

**Arguments:**

- `ROCRATE_PATH` - Path to the RO-Crate directory or metadata file [required]
- `ARK_ID` - ARK identifier for which to build the evidence graph [required]

**Options:**

- `--output-file PATH` - Path to save the JSON evidence graph (defaults to provenance-graph.json in the RO-Crate directory)

**Example:**

```bash
fairscape-cli build evidence-graph \
    ./my_rocrate \
    ark:59852/dataset-output-dataset-xDNPTmwoHl
```

This command:

1. Reads the RO-Crate metadata
2. Identifies all relationships involving the specified ARK identifier
3. Builds a graph representing the provenance of the entity
4. Generates both JSON and HTML visualizations of the graph
5. Updates the RO-Crate metadata to reference the evidence graph

The evidence graph shows:

- Inputs used to create the entity
- Software used in the computations
- Computations that generated or used the entity
- Derived datasets or outputs
- All relevant metadata for each node in the graph

The HTML visualization provides an interactive graph that can be viewed in a web browser, making it easy to explore the provenance of datasets, software, and computations in the RO-Crate.

### `release`

Build a release RO-Crate in a directory, scanning for and linking existing sub-RO-Crates. This creates a parent RO-Crate that references and contextualizes the sub-crates. For more details see [workflow documentation](release_creation.md)

```bash
fairscape-cli build release [OPTIONS] RELEASE_DIRECTORY
```

**Arguments:**

- `RELEASE_DIRECTORY` - Directory where the release RO-Crate will be built [required]

**Options:**

- `--guid TEXT` - GUID for the parent release RO-Crate (generated if not provided)
- `--name TEXT` - Name for the parent release RO-Crate [required]
- `--organization-name TEXT` - Organization name associated with the release [required]
- `--project-name TEXT` - Project name associated with the release [required]
- `--description TEXT` - Description of the release RO-Crate [required]
- `--keywords TEXT` - Keywords for the release RO-Crate (can be used multiple times) [required]
- `--license TEXT` - License URL for the release (default: "https://creativecommons.org/licenses/by/4.0/")
- `--date-published TEXT` - Publication date (ISO format, defaults to current date)
- `--author TEXT` - Author(s) of the release (defaults to combined authors from subcrates)
- `--version TEXT` - Version of the release (default: "1.0")
- `--associated-publication TEXT` - Associated publications for the release (can be used multiple times)
- `--conditions-of-access TEXT` - Conditions of access for the release
- `--copyright-notice TEXT` - Copyright notice for the release
- `--doi TEXT` - DOI identifier for the release
- `--publisher TEXT` - Publisher of the release
- `--principal-investigator TEXT` - Principal investigator for the release
- `--contact-email TEXT` - Contact email for the release
- `--confidentiality-level TEXT` - Confidentiality level for the release
- `--citation TEXT` - Citation for the release
- `--funder TEXT` - Funder of the release
- `--usage-info TEXT` - Usage information for the release
- `--content-size TEXT` - Content size of the release
- `--completeness TEXT` - Completeness information for the release
- `--maintenance-plan TEXT` - Maintenance plan for the release
- `--intended-use TEXT` - Intended use of the release
- `--limitations TEXT` - Limitations of the release
- `--prohibited-uses TEXT` - Prohibited uses of the release
- `--potential-sources-of-bias TEXT` - Potential sources of bias in the release
- `--human-subject TEXT` - Human subject involvement information
- `--ethical-review TEXT` - Ethical review information
- `--rai-data-collection TEXT` - RAI: Description of the data collection process
- `--rai-data-collection-type TEXT` - RAI: Type of data collection (e.g., 'Web Scraping', 'Surveys') (can be used multiple times)
- `--rai-missing-data-desc TEXT` - RAI: Description of missing data in the dataset
- `--rai-raw-data-source TEXT` - RAI: Description of the raw data source
- `--rai-collection-start-date TEXT` - RAI: Start date of the data collection process (ISO format)
- `--rai-collection-end-date TEXT` - RAI: End date of the data collection process (ISO format)
- `--rai-imputation-protocol TEXT` - RAI: Description of the data imputation process
- `--rai-manipulation-protocol TEXT` - RAI: Description of the data manipulation process
- `--rai-preprocessing-protocol TEXT` - RAI: Steps taken to preprocess the data for ML use (can be used multiple times)
- `--rai-annotation-protocol TEXT` - RAI: Description of the annotation process (e.g., workforce, tasks)
- `--rai-annotation-platform TEXT` - RAI: Platform or tool used for human annotation (can be used multiple times)
- `--rai-annotation-analysis TEXT` - RAI: Analysis of annotations (e.g., disagreement resolution) (can be used multiple times)
- `--rai-sensitive-info TEXT` - RAI: Description of any personal or sensitive information (can be used multiple times)
- `--rai-social-impact TEXT` - RAI: Discussion of the dataset's potential social impact
- `--rai-annotations-per-item TEXT` - RAI: Number of human labels per dataset item
- `--rai-annotator-demographics TEXT` - RAI: Demographic specifications about the annotators (can be used multiple times)
- `--rai-machine-annotation-tools TEXT` - RAI: Software used for automated data annotation (can be used multiple times)
- `--additional-properties TEXT` - JSON string with additional property values
- `--custom-properties TEXT` - JSON string with additional properties for the parent crate

**Example:**

```bash
fairscape-cli build release ./my_release \
    --guid "ark:59852/example-release-2023" \
    --name "SRA Genomic Data Example Release - 2023" \
    --organization-name "Example Research Institute" \
    --project-name "Genomic Data Analysis Project" \
    --description "This dataset contains genomic data from multiple sources prepared as AI-ready datasets in RO-Crate format." \
    --keywords "Genomics" \
    --keywords "SRA" \
    --keywords "RNA-seq" \
    --license "https://creativecommons.org/licenses/by/4.0/" \
    --publisher "University Example Dataverse" \
    --principal-investigator "Dr. Example PI" \
    --contact-email "example@example.org" \
    --confidentiality-level "HL7 Unrestricted" \
    --funder "Example Agency" \
    --citation "Example Research Institute (2023). Genomic Data Example Release." \
    --rai-data-collection "Data collected via automated web scraping of public repositories" \
    --rai-data-collection-type "Web Scraping" \
    --rai-data-collection-type "API Access" \
    --rai-collection-start-date "2023-01-01T00:00:00Z" \
    --rai-collection-end-date "2023-12-31T23:59:59Z" \
    --rai-preprocessing-protocol "Quality filtering removed low-quality sequences" \
    --rai-preprocessing-protocol "Normalization applied to expression values"
```

This command:

1. Creates a new parent RO-Crate in the specified directory
2. Scans the directory for existing RO-Crates to include as subcrates
3. Links the subcrates to the parent crate
4. Combines metadata from subcrates and the provided options
5. Outputs the ARK identifier of the created release RO-Crate

## Release Workflow

A typical release workflow involves:

1. **Create individual RO-Crates** for specific datasets, software, and computations
2. **Place these RO-Crates** in a common directory structure
3. **Build a release** using the `build release` command to create a parent RO-Crate
4. **Generate a datasheet** using the `build datasheet` command
5. **Publish the release** using the `publish` commands

The parent release RO-Crate provides context and relationships between the individual RO-Crates, making it easier to understand and work with complex datasets that span multiple files, processes, and research objects.

## RAI (Responsible AI) Metadata

The release command supports extensive RAI metadata properties following the Croissant RAI Specification v1.0 (http://mlcommons.org/croissant/RAI/1.0). These properties enable comprehensive documentation of dataset lifecycle, annotation processes, and responsible use considerations.

### Data Lifecycle Properties

**Collection Process:**

- `--rai-data-collection` - Description of the data collection process
- `--rai-data-collection-type` - Collection method types (multiple values). Recommended values: Surveys, Secondary Data analysis, Physical data collection, Direct measurement, Document analysis, Manual Human Curator, Software Collection, Experiments, Web Scraping, Web API, Focus groups, Self-reporting, Customer feedback data, User-generated content data, Passive Data Collection, Others
- `--rai-missing-data-desc` - Description of missing data in structured/unstructured form
- `--rai-raw-data-source` - Description of the raw data source
- `--rai-collection-start-date` / `--rai-collection-end-date` - Timeframe in terms of start and end date of the collection process (ISO format)

**Data Processing:**

- `--rai-imputation-protocol` - Description of data imputation process if applicable
- `--rai-manipulation-protocol` - Description of data manipulation process if applicable
- `--rai-preprocessing-protocol` - Description of steps required to bring collected data to a state processable by ML models/algorithms (multiple values)

### Annotation and Labeling Properties

**Annotation Process:**

- `--rai-annotation-protocol` - Description of annotations (labels, ratings) produced, including creation process - Annotation Workforce Type, Characteristics, Descriptions, Tasks, Distributions
- `--rai-annotation-platform` - Platform, tool, or library used to collect annotations by human annotators (multiple values)
- `--rai-annotation-analysis` - Considerations for converting "raw" annotations into final dataset labels, including uncertainty/disagreement analysis, systematic differences between annotator groups (multiple values)
- `--rai-annotations-per-item` - Number of human labels per dataset item
- `--rai-annotator-demographics` - List of demographic specifications about the annotators (multiple values)
- `--rai-machine-annotation-tools` - List of software used for data annotation (e.g., concept extraction, NER) to enable replication or extension (multiple values)

### Safety and Fairness Properties

**Responsible Use:**

- `--rai-social-impact` - Discussion of social impact, if applicable
- `--potential-sources-of-bias` - Description of biases in dataset, if applicable (multiple values)
- `--limitations` - Known limitations - Data generalization limits and non-recommended uses (multiple values)
- `--intended-use` - Dataset uses - Training, Testing, Validation, Development, Production, Fine Tuning, Others. Usage Guidelines and recommended uses (multiple values)
- `--rai-sensitive-info` - Sensitive Human Attributes - Gender, Socio-economic status, Geography, Language, Age, Culture, Experience or Seniority, Others (multiple values)

### Compliance and Maintenance Properties

**Dataset Management:**

- `--maintenance-plan` - Versioning information including updating timeframe, maintainers, and deprecation policies (multiple values)

These RAI properties align with use cases including data lifecycle documentation, annotation transparency, participatory data practices, AI safety evaluation, and regulatory compliance requirements.

## Metadata Inheritance

When building a release, metadata is handled in the following ways:

- **Author information** is combined from all subcrates unless explicitly provided
- **Keywords** include both the specified keywords and those from subcrates
- **Version** defaults to "1.0" unless specified
- **License** defaults to CC-BY 4.0 unless specified
- **Publication date** defaults to the current date unless specified
- **RAI properties** are only included when explicitly provided

All other metadata must be explicitly provided through the command options.

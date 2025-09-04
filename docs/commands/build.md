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

Build a release RO-Crate in a directory, scanning for and linking existing sub-RO-Crates. This creates a parent RO-Crate that references and contextualizes the sub-crates.

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
    --citation "Example Research Institute (2023). Genomic Data Example Release."
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

## Metadata Inheritance

When building a release, metadata is handled in the following ways:

- **Author information** is combined from all subcrates unless explicitly provided
- **Keywords** include both the specified keywords and those from subcrates
- **Version** defaults to "1.0" unless specified
- **License** defaults to CC-BY 4.0 unless specified
- **Publication date** defaults to the current date unless specified

All other metadata must be explicitly provided through the command options.

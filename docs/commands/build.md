# Build Commands

This document provides detailed information about the build commands available in fairscape-cli.

## Overview

The `build` command group provides operations for generating derived artifacts from RO-Crates. These artifacts include datasheets, visualizations, and evidence graphs that make the RO-Crate content more accessible and understandable.

```bash
fairscape-cli build [COMMAND] [OPTIONS]
```

## Available Commands

- [`datasheet`](#datasheet) - Generate an HTML datasheet for an RO-Crate
- [`evidence-graph`](#evidence-graph) - Generate a provenance graph for a specific ARK identifier

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

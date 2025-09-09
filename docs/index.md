# fairscape-cli

A utility for packaging objects and validating metadata for FAIRSCAPE.

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

```bash
pip install fairscape-cli
```

## Command Overview

The CLI is organized into several top-level commands:

| Command      | Description                                                               |
| ------------ | ------------------------------------------------------------------------- |
| **rocrate**  | Core local RO-Crate manipulation (create, add files/metadata).            |
| **schema**   | Operations on data schemas (create, infer, add properties, add to crate). |
| **import**   | Fetch external data into RO-Crate format (e.g., bioproject, pep).         |
| **build**    | Generate outputs from RO-Crates (e.g., datasheet, evidence-graph, release).        |
| **publish**  | Publish RO-Crates to repositories (e.g., fairscape, dataverse, mint dois).      |

Use `--help` for details on any command or subcommand:

```bash
fairscape-cli --help
fairscape-cli rocrate --help
fairscape-cli rocrate create --help
fairscape-cli schema create-tabular --help
```

### Learn More

For more detailed examples and a complete workflow demonstration, see the [Complete Workflow Demo](workflows/complete-demo.md).

## Documentation

- [Installation](setup.md)
- [Command Reference](commands/rocrate.md)
- [Complete Workflow Demo](workflows/complete-demo.md)

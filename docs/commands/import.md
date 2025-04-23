# Import Commands

This document provides detailed information about the import commands available in fairscape-cli.

## Overview

The `import` command group provides operations for importing external data into RO-Crate format. These commands fetch data from external repositories and convert them to well-structured RO-Crates with appropriate metadata.

```bash
fairscape-cli import [COMMAND] [OPTIONS]
```

## Available Commands

- [`bioproject`](#bioproject) - Import data from an NCBI BioProject
- [`pep`](#pep) - Import a Portable Encapsulated Project (PEP)

## Command Details

### `bioproject`

Import data from an NCBI BioProject into an RO-Crate.

```bash
fairscape-cli import bioproject [OPTIONS]
```

**Options:**

- `--accession TEXT` - NCBI BioProject accession (e.g., PRJNA12345) [required]
- `--output-dir PATH` - Directory to create the RO-Crate in [required]
- `--author TEXT` - Author name to associate with generated metadata [required]
- `--api-key TEXT` - NCBI API key (optional)
- `--name TEXT` - Override the default RO-Crate name
- `--description TEXT` - Override the default RO-Crate description
- `--keywords TEXT` - Override the default RO-Crate keywords (can be used multiple times)
- `--license TEXT` - Override the default RO-Crate license URL
- `--version TEXT` - Override the default RO-Crate version
- `--organization-name TEXT` - Set the organization name for the RO-Crate
- `--project-name TEXT` - Set the project name for the RO-Crate

**Example:**

```bash
fairscape-cli import bioproject \
    --accession "PRJDB2884" \
    --output-dir "./bioproject_crate" \
    --author "Jane Smith" \
    --keywords "genomics" \
    --keywords "sequencing"
```

This command:

1. Fetches metadata from the NCBI BioProject database
2. Creates an RO-Crate with the BioProject metadata
3. Registers datasets, samples, and other relevant data from the BioProject
4. Outputs the ARK identifier of the created RO-Crate

### `pep`

Import a Portable Encapsulated Project (PEP) into an RO-Crate.

```bash
fairscape-cli import pep [OPTIONS] PEP_PATH
```

**Arguments:**

- `PEP_PATH` - Path to the PEP directory or config file [required]

**Options:**

- `--output-path PATH` - Path for the generated RO-Crate (defaults to PEP directory)
- `--name TEXT` - Name for the RO-Crate (overrides PEP metadata)
- `--description TEXT` - Description (overrides PEP metadata)
- `--author TEXT` - Author (overrides PEP metadata)
- `--organization-name TEXT` - Organization name
- `--project-name TEXT` - Project name
- `--keywords TEXT` - Keywords (overrides PEP metadata, can be used multiple times)
- `--license TEXT` - License URL (default: "https://creativecommons.org/licenses/by/4.0/")
- `--date-published TEXT` - Publication date
- `--version TEXT` - Version string (default: "1.0")

**Example:**

```bash
fairscape-cli import pep \
    ./my_pep_project \
    --output-path ./pep_rocrate \
    --author "John Doe" \
    --organization-name "University Example" \
    --project-name "My PEP Project"
```

This command:

1. Reads the PEP project configuration
2. Creates an RO-Crate with metadata from the PEP
3. Outputs the ARK identifier of the created RO-Crate

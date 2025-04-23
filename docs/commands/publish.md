# Publish Commands

This document provides detailed information about the publish commands available in fairscape-cli.

## Overview

The `publish` command group provides operations for publishing RO-Crates to external repositories and registering persistent identifiers. These commands help make your research data FAIR (Findable, Accessible, Interoperable, and Reusable) by connecting it to wider research data ecosystems.

```bash
fairscape-cli publish [COMMAND] [OPTIONS]
```

## Available Commands

- [`fairscape`](#fairscape) - Upload RO-Crate directory or zip file to Fairscape
- [`dataverse`](#dataverse) - Publish RO-Crate metadata as a new dataset to Dataverse
- [`doi`](#doi) - Mint or update a DOI on DataCite using RO-Crate metadata

## Command Details

### `fairscape`

Upload an RO-Crate directory or zip file to a Fairscape repository.

```bash
fairscape-cli publish fairscape [OPTIONS]
```

**Options:**

- `--rocrate PATH` - Path to the RO-Crate directory or zip file [required]
- `--username TEXT` - Fairscape username (can also be set via FAIRSCAPE_USERNAME env var) [required]
- `--password TEXT` - Fairscape password (can also be set via FAIRSCAPE_PASSWORD env var) [required]
- `--api-url TEXT` - Fairscape API URL (default: "https://fairscape.net/api")

**Example:**

```bash
fairscape-cli publish fairscape \
    --rocrate ./my_rocrate \
    --username "your_username" \
    --password "your_password" \
    --api-url "https://fairscape.example.org/api"
```

This command:

1. Authenticates with the Fairscape repository
2. Uploads the RO-Crate directory or zip file
3. Registers the metadata in the repository
4. Returns a URL to access the published RO-Crate

### `dataverse`

Publish RO-Crate metadata as a new dataset to a Dataverse repository.

```bash
fairscape-cli publish dataverse [OPTIONS]
```

**Options:**

- `--rocrate PATH` - Path to the ro-crate-metadata.json file [required]
- `--prefix TEXT` - Your DataCite DOI prefix (e.g., "10.1234") [required]
- `--username TEXT` - DataCite API username (repository ID, e.g., "MEMBER.REPO") (can use DATACITE_USERNAME env var) [required]
- `--password TEXT` - DataCite API password (can use DATACITE_PASSWORD env var) [required]
- `--api-url TEXT` - DataCite API URL (default: "https://api.datacite.org", use "https://api.test.datacite.org" for testing)
- `--event TEXT` - DOI event type: 'publish' (make public), 'register' (create draft), 'hide' (make findable but hide metadata) [default: "publish"]

**Example:**

```bash
fairscape-cli publish doi \
    --rocrate ./my_rocrate/ro-crate-metadata.json \
    --prefix "10.1234" \
    --username "MYORG.MYREPO" \
    --password "your_datacite_password" \
    --event "publish"
```

This command:

1. Reads the RO-Crate metadata
2. Transforms it into DataCite metadata
3. Mints or updates a DOI on DataCite
4. Returns the DOI URL

## Working with DOIs

When working with DOIs, keep in mind:

1. **DOI States**:

   - `register`: Creates a draft DOI that is not yet publicly resolvable
   - `publish`: Makes the DOI and its metadata public and resolvable
   - `hide`: Makes the DOI resolvable but hides its metadata

2. **Testing**: Use the test DataCite API URL before working with the production system:

   ```bash
   --api-url "https://api.test.datacite.org"
   ```

3. **Updating**: To update an existing DOI, ensure the RO-Crate metadata contains the DOI in the `identifier` field.

## Integrating with Dataverse

After minting a DOI, you can update your RO-Crate metadata with the DOI and then publish to Dataverse:

```bash
# First mint a DOI
fairscape-cli publish doi --rocrate ./my_rocrate/ro-crate-metadata.json ...

# Then update your RO-Crate with the DOI
# (This would typically be done programmatically)

# Then publish to Dataverse
fairscape-cli publish dataverse --rocrate ./my_rocrate/ro-crate-metadata.json ...
```

This workflow ensures your research data is both persistently identified and accessible through established research data repositories.
json file [required]

- `--url TEXT` - Base URL of the target Dataverse instance (e.g., "https://dataverse.example.edu") [required]
- `--collection TEXT` - Alias of the target Dataverse collection to publish into [required]
- `--token TEXT` - Dataverse API token (can also be set via DATAVERSE_API_TOKEN env var) [required]
- `--authors-csv PATH` - Optional CSV file with author details (name, affiliation, orcid). Requires "name" column header.

**Example:**

```bash
fairscape-cli publish dataverse \
    --rocrate ./my_rocrate/ro-crate-metadata.json \
    --url "https://dataverse.example.edu" \
    --collection "my_collection" \
    --token "your_dataverse_api_token"
```

This command:

1. Reads the RO-Crate metadata
2. Transforms it into Dataverse dataset metadata
3. Creates a new dataset in the specified Dataverse collection
4. Returns the DOI of the created dataset

### `doi`

Mint or update a DOI on DataCite using RO-Crate metadata.

```bash
fairscape-cli publish doi [OPTIONS]
```

**Options:**

- `--rocrate PATH` - Path to the ro-crate-metadata.json file [required]
- `--prefix TEXT` - Your DataCite DOI prefix (e.g., "10.1234") [required]
- `--username TEXT` - DataCite API username (repository ID, e.g., "MEMBER.REPO") (can use DATACITE_USERNAME env var) [required]
- `--password TEXT` - DataCite API password (can use DATACITE_PASSWORD env var) [required]
- `--api-url TEXT` - DataCite API URL (default: "https://api.datacite.org", use "https://api.test.datacite.org" for testing)
- `--event TEXT` - DOI event type: 'publish' (make public), 'register' (create draft), 'hide' (make findable but hide metadata) [default: "publish"]

**Example:**

```bash
fairscape-cli publish doi \
    --rocrate ./my_rocrate/ro-crate-metadata.
```

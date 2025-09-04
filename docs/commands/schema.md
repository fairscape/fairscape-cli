# Schema Commands

This document provides detailed information about the schema commands available in fairscape-cli.

## Overview

The `schema` command group provides operations for creating, modifying, working with data schemas, and validating data against schemas. Schemas describe the structure and constraints of datasets, enabling validation and improved interoperability.

```bash
fairscape-cli schema [COMMAND] [OPTIONS]
```

## Available Commands

- [`create-tabular`](#create-tabular) - Create a new tabular schema definition
- [`add-property`](#add-property) - Add a property to an existing schema
    - [`string`](#add-property-string) - Add a string property
    - [`number`](#add-property-number) - Add a number property
    - [`integer`](#add-property-integer) - Add an integer property
    - [`boolean`](#add-property-boolean) - Add a boolean property
    - [`array`](#add-property-array) - Add an array property
- [`infer`](#infer) - Infer a schema from a data file
- [`add-to-crate`](#add-to-crate) - Add a schema to an RO-Crate
- [`validate`](#validate) - Validate a dataset against a schema definition

## Command Details

### `create-tabular`

Create a new tabular schema definition.

```bash
fairscape-cli schema create-tabular [OPTIONS] SCHEMA_FILE
```

**Options:**

- `--name TEXT` - Name of the schema [required]
- `--description TEXT` - Description of the schema [required]
- `--guid TEXT` - Optional custom identifier for the schema
- `--separator TEXT` - Field separator character (e.g., `,` for CSV) [required]
- `--header BOOLEAN` - Whether the data file has a header row (default: False)

**Example:**

```bash
fairscape-cli schema create-tabular \
    --name 'APMS Embedding Schema' \
    --description 'Tabular format for APMS music embeddings' \
    --separator ',' \
    --header False \
    ./schema_apms_music_embedding.json
```

### `add-property`

This command group allows you to add different types of properties to an existing schema.

#### `add-property string`

Add a string property to a schema.

```bash
fairscape-cli schema add-property string [OPTIONS] SCHEMA_FILE
```

**Options:**

- `--name TEXT` - Name of the property [required]
- `--index INTEGER` - Column index in the data (0-based) [required]
- `--description TEXT` - Description of the property [required]
- `--value-url TEXT` - URL to a vocabulary term
- `--pattern TEXT` - Regular expression pattern for validation

**Example:**

```bash
fairscape-cli schema add-property string \
    --name 'Gene Symbol' \
    --index 1 \
    --description 'Gene Symbol for the APMS bait protein' \
    --pattern '^[A-Za-z0-9\-]*$' \
    --value-url 'http://edamontology.org/data_1026' \
    ./schema_apms_music_embedding.json
```

#### `add-property number`

Add a number property to a schema.

```bash
fairscape-cli schema add-property number [OPTIONS] SCHEMA_FILE
```

**Options:**

- `--name TEXT` - Name of the property [required]
- `--index INTEGER` - Column index in the data (0-based) [required]
- `--description TEXT` - Description of the property [required]
- `--maximum FLOAT` - Maximum allowed value
- `--minimum FLOAT` - Minimum allowed value
- `--value-url TEXT` - URL to a vocabulary term

**Example:**

```bash
fairscape-cli schema add-property number \
    --name 'Measurement' \
    --index 2 \
    --description 'Sensor reading in units of X' \
    --minimum 0.0 \
    --maximum 100.0 \
    ./schema_apms_music_embedding.json
```

#### `add-property integer`

Add an integer property to a schema.

```bash
fairscape-cli schema add-property integer [OPTIONS] SCHEMA_FILE
```

**Options:**

- `--name TEXT` - Name of the property [required]
- `--index INTEGER` - Column index in the data (0-based) [required]
- `--description TEXT` - Description of the property [required]
- `--maximum INTEGER` - Maximum allowed value
- `--minimum INTEGER` - Minimum allowed value
- `--value-url TEXT` - URL to a vocabulary term

**Example:**

```bash
fairscape-cli schema add-property integer \
    --name 'Count' \
    --index 3 \
    --description 'Count of observations' \
    --minimum 0 \
    ./schema_apms_music_embedding.json
```

#### `add-property boolean`

Add a boolean property to a schema.

```bash
fairscape-cli schema add-property boolean [OPTIONS] SCHEMA_FILE
```

**Options:**

- `--name TEXT` - Name of the property [required]
- `--index INTEGER` - Column index in the data (0-based) [required]
- `--description TEXT` - Description of the property [required]
- `--value-url TEXT` - URL to a vocabulary term

**Example:**

```bash
fairscape-cli schema add-property boolean \
    --name 'IsValid' \
    --index 4 \
    --description 'Whether the observation is valid' \
    ./schema_apms_music_embedding.json
```

#### `add-property array`

Add an array property to a schema.

```bash
fairscape-cli schema add-property array [OPTIONS] SCHEMA_FILE
```

**Options:**

- `--name TEXT` - Name of the property [required]
- `--index TEXT` - Column index or range in the data (e.g., "5" or "2::") [required]
- `--description TEXT` - Description of the property [required]
- `--value-url TEXT` - URL to a vocabulary term
- `--items-datatype TEXT` - Datatype of items in the array (`string`, `number`, `integer`, `boolean`) [required]
- `--min-items INTEGER` - Minimum number of items in the array
- `--max-items INTEGER` - Maximum number of items in the array
- `--unique-items BOOLEAN` - Whether items must be unique

**Example:**

```bash
fairscape-cli schema add-property array \
    --name 'MUSIC APMS Embedding' \
    --index '2::' \
    --description 'Embedding Vector values' \
    --items-datatype 'number' \
    --unique-items False \
    --min-items 1024 \
    --max-items 1024 \
    ./schema_apms_music_embedding.json
```

### `infer`

Infer a schema from a data file.

```bash
fairscape-cli schema infer [OPTIONS] INPUT_FILE SCHEMA_FILE
```

**Options:**

- `--name TEXT` - Name for the schema [required]
- `--description TEXT` - Description for the schema [required]
- `--guid TEXT` - Optional custom identifier for the schema
- `--rocrate-path PATH` - Optional path to an RO-Crate to append the schema to

**Example:**

```bash
fairscape-cli schema infer \
    --name 'Output Dataset Schema' \
    --description 'Inferred schema for output data' \
    --rocrate-path ./my_rocrate \
    ./my_rocrate/output.csv \
    ./my_rocrate/output_schema.json
```

### `add-to-crate`

Add a schema to an RO-Crate.

```bash
fairscape-cli schema add-to-crate ROCRATE_PATH SCHEMA_FILE
```

**Arguments:**

- `ROCRATE_PATH` - Path to the RO-Crate to add the schema to
- `SCHEMA_FILE` - Path to the schema file

**Example:**

```bash
fairscape-cli schema add-to-crate \
    ./my_rocrate \
    ./schema_apms_music_embedding.json
```

### `validate`

Validate a dataset against a schema definition.

```bash
fairscape-cli schema validate [OPTIONS]
```

**Options:**

- `--schema TEXT` - Path to the schema file or ARK identifier [required]
- `--data TEXT` - Path to the data file to validate [required]

**Example:**

```bash
fairscape-cli schema validate \
    --schema ./music_apms_embedding_schema.json \
    --data ./APMS_embedding_MUSIC.csv
```

When validation succeeds, you'll see:

```
Validation Success
```

If validation fails, you'll see a table of errors:

```
+-----+-----------------+----------------+-------------------------------------------------------+
| row |    error_type   | failed_keyword |                        message                        |
+-----+-----------------+----------------+-------------------------------------------------------+
|  3  |   ParsingError  |      None      | ValueError: Failed to Parse Attribute embed for Row 3 |
|  4  |   ParsingError  |      None      | ValueError: Failed to Parse Attribute embed for Row 4 |
|  0  | ValidationError |    pattern     |        'APMS_A' does not match '^APMS_[0-9]*$'        |
+-----+-----------------+----------------+-------------------------------------------------------+
```

## Error Types

Errors are categorized into two main types:

1. **ParsingError**: Occurs when the data cannot be parsed according to the schema structure. This often happens when:

   - The number of columns doesn't match the schema
   - A value cannot be converted to the expected datatype

2. **ValidationError**: Occurs when the data can be parsed but fails validation constraints like:
   - String values not matching the specified pattern
   - Numeric values outside the min/max range
   - Array length not within specified bounds

## Working with Different File Types

The validation command automatically detects the file type based on its extension:

- **CSV/TSV files**: Tabular validation with field separators
- **Parquet files**: Tabular validation with columnar storage
- **HDF5 files**: Hierarchical validation with nested structures

# Schema Commands

This document provides detailed information about the schema commands available in fairscape-cli.

## Overview

The `schema` command group provides operations for creating, modifying, and working with data schemas. Schemas describe the structure and constraints of datasets, enabling validation and improved interoperability.

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
    ./schema_sensor_data.json
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
    ./schema_count_data.json
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
    ./schema_validation_data.json
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

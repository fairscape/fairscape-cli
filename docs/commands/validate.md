# Validation Commands

This document provides detailed information about the validation commands available in fairscape-cli.

## Overview

The `validate` command group provides operations for validating data against schemas. This ensures that datasets conform to their expected structure and constraints.

```bash
fairscape-cli validate [COMMAND] [OPTIONS]
```

## Available Commands

- [`schema`](#schema) - Validate a dataset against a schema definition

## Command Details

### `schema`

Validate a dataset against a schema definition.

```bash
fairscape-cli validate schema [OPTIONS]
```

**Options:**

- `--schema TEXT` - Path to the schema file or ARK identifier [required]
- `--data TEXT` - Path to the data file to validate [required]

**Example:**

```bash
fairscape-cli validate schema \
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

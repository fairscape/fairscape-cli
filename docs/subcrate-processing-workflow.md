# Subcrate Processing Workflow

This document describes how `process_all_subcrates` works in the `build release` command and how its steps map to individual CLI commands for flexible workflow support.

## Overview

The `build release` command can operate in two modes:
1. **Full processing** (default): Processes all subcrates, then creates the release crate
2. **Skip processing** (`--skip-subcrate-processing`): Creates the release crate without processing subcrates. But the sub-crates would need to be later linked and the top-level ro-crate is missing aggreagated metrics. 

## What `process_all_subcrates` Does

Located in `src/fairscape_cli/utils/build_utils.py`, this function performs five steps on each subcrate found in the release directory:

| Step | Function | Description |
|------|----------|-------------|
| 1 | `process_link_inverses()` | Adds OWL inverse properties using the EVI ontology |
| 2 | `process_add_io()` | Calculates and adds `EVI:inputs` and `EVI:outputs` to the root dataset |
| 3 | `process_evidence_graph()` | Generates provenance graph JSON and HTML visualization |
| 4 | `process_croissant()` | Converts RO-Crate metadata to Croissant JSON-LD format |
| 5 | `process_preview()` | Generates `ro-crate-preview.html` for browser viewing |

## Mapping to CLI Commands

Each processing step can be executed individually using existing CLI commands:

| Processing Step | Equivalent CLI Command |
|-----------------|------------------------|
| `process_link_inverses()` | `fairscape augment link-inverses <rocrate-path>` |
| `process_add_io()` | `fairscape augment add-io <rocrate-path>` |
| `process_evidence_graph()` | `fairscape build evidence-graph <rocrate-path> <ark-id>` |
| `process_croissant()` | `fairscape build croissant <rocrate-path>` |
| `process_preview()` | `fairscape build preview <rocrate-path>` |

**All-in-one command:** Use `fairscape build subcrate <path>` to run all five steps on a single subcrate.

## Supported Workflows

### Workflow 1: Subcrates First, Then Release (Default)

This is the current default behavior. Subcrates are processed automatically before the release crate is created.

```bash
# Single command handles everything
fairscape build release ./my-release \
  --name "My Release" \
  --organization-name "My Org" \
  --project-name "My Project" \
  --description "Release description" \
  --keywords "keyword1" --keywords "keyword2"
```

**What happens internally:**
1. `process_all_subcrates()` finds and processes all subcrates in `./my-release`
2. Subcrate metadata is collected (authors, keywords)
3. Release RO-Crate is created with aggregated metadata
4. Subcrates are linked to the release via `LinkSubcrates()`
5. Release-level Croissant and datasheet are generated

### Workflow 2: Release First, Then Subcrates Later

Use this when you need to create the release crate structure first and add/process subcrates afterward.

```bash
# Step 1: Create release crate without processing subcrates
fairscape build release ./my-release \
  --name "My Release" \
  --organization-name "My Org" \
  --project-name "My Project" \
  --description "Release description" \
  --keywords "keyword1" \
  --skip-subcrate-processing

# Step 2: Add subcrates to the release directory
# (manually copy or create subcrate directories)

# Step 3: Process each subcrate (all-in-one command)
fairscape build subcrate ./my-release/subcrate1 --release-directory ./my-release
fairscape build subcrate ./my-release/subcrate2 --release-directory ./my-release

# Or process each step individually if needed:
# fairscape augment link-inverses ./my-release/subcrate1
# fairscape augment add-io ./my-release/subcrate1
# fairscape build evidence-graph ./my-release/subcrate1 <ark-id>
# fairscape build croissant ./my-release/subcrate1
# fairscape build preview ./my-release/subcrate1
```

## Potential Enhancements

### 1. Batch Subcrate Processing Command

A new command to process all subcrates in an existing release:

```bash
fairscape augment subcrates <release-directory>
```

This would call `process_all_subcrates()` on an existing release, enabling:
1. Build release first with `--skip-subcrate-processing`
2. Add subcrates to the release directory
3. Run batch processing on all subcrates

### 2. Re-link Subcrates Command

A command to update the release's `hasPart` references after adding new subcrates:

```bash
fairscape augment link-subcrates <release-directory>
```

This would call `LinkSubcrates()` to update the release metadata with references to any newly added subcrates.

### 3. Combined Post-Processing Command

A single command to both process subcrates and re-link them:

```bash
fairscape augment finalize-release <release-directory>
```

This would:
1. Run `process_all_subcrates()` to process all subcrates
2. Run `LinkSubcrates()` to update release references
3. Regenerate release-level Croissant and datasheet

## Command Reference

### `augment link-inverses`

Adds OWL inverse properties to an RO-Crate based on the EVI ontology.

```bash
fairscape augment link-inverses <rocrate-path> [--ontology-path PATH] [--namespace URI]
```

**Options:**
- `--ontology-path`: Custom OWL ontology file (defaults to bundled `evi.xml`)
- `--namespace`: Primary namespace URI for property keys (defaults to EVI namespace)

### `augment add-io`

Calculates and adds `EVI:inputs` and `EVI:outputs` to the root dataset.

```bash
fairscape augment add-io <rocrate-path> [--verbose]
```

**Inputs are:**
- All `EVI:Sample` entities
- Datasets referenced in `usedDataset` that were not generated by a computation
- Datasets referenced in `usedDataset` but not defined in the `@graph`

**Outputs are:**
- All datasets that were not used by any computation

### `build evidence-graph`

Generates a provenance graph for a specific ARK identifier.

```bash
fairscape build evidence-graph <rocrate-path> <ark-id> [--output-file PATH]
```

**Outputs:**
- `provenance-graph.json`: JSON representation of the evidence graph
- `provenance-graph.html`: Interactive HTML visualization

### `build croissant`

Converts an RO-Crate to Croissant JSON-LD format.

```bash
fairscape build croissant <rocrate-path> [--output PATH]
```

**Output:**
- `croissant.json` (or custom path): Croissant-formatted metadata

### `build preview`

Generates a lightweight HTML preview for an RO-Crate.

```bash
fairscape build preview <rocrate-path> [--published]
```

**Options:**
- `--published`: Indicate if the crate is published (affects link rendering)

**Output:**
- `ro-crate-preview.html`: Browser-viewable summary of the crate

### `build subcrate`

Processes a single subcrate with all augmentation and build steps. This is the recommended command for processing individual subcrates.

```bash
fairscape build subcrate <subcrate-path> [--release-directory PATH] [--published]
```

**Options:**
- `--release-directory`: Parent release directory (used for relative paths in evidence graphs)
- `--published`: Indicate if the crate is published

**Steps performed:**
1. Link inverse properties (OWL ontology entailments)
2. Add `EVI:inputs` and `EVI:outputs` to the root dataset
3. Generate evidence graph (JSON + HTML visualization)
4. Generate Croissant export (JSON-LD)
5. Generate preview HTML

**Example:**
```bash
# Process a subcrate within a release
fairscape build subcrate ./my-release/experiment-1 --release-directory ./my-release

# Process a standalone subcrate
fairscape build subcrate ./my-subcrate
```

# Fairscape-CLI Complete Workflow Demo

This document demonstrates a complete workflow for using fairscape-cli to create, manage, and publish research data packages with proper metadata. The workflow follows these key steps:

1. Build a crate with local files and computation
2. Create schemas and validate data
3. Build a crate from external repository data
4. Generate evidence graphs
5. Build a unified release crate with rich metadata

## Prerequisites

Before starting this workflow, make sure you have:

- fairscape-cli installed

## Step 1: Build a Crate with Local Files and Computation

We'll start by creating a small data processing example using local files. This demonstrates the full research object lifecycle from input to output.

### 1.1 Create Input File and Processing Script

First, let's create a directory structure and generate sample files for our computation:

```bash
# Create the base directory
mkdir -p ./simple-computation

# Create sample input.csv with Python
python -c "import pandas as pd; pd.DataFrame({'value1': [10, 20, 30, 40, 50], 'value2': [5, 15, 25, 35, 45]}).to_csv('./simple-computation/input.csv', index=False)"

# Create sample software.py
cat > ./simple-computation/software.py << 'EOF'
import pandas as pd
import sys

def process_data(input_file, output_file):
    # Read input data
    data = pd.read_csv(input_file)

    # Process data (calculate sum and product)
    data['sum'] = data['value1'] + data['value2']
    data['product'] = data['value1'] * data['value2']

    # Save results
    data.to_csv(output_file, index=False)
    print(f"Processing complete. Results saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        process_data(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python software.py input.csv output.csv")
EOF
```

### 1.2 Create and Register RO-Crate

Now, let's create the RO-Crate and register our input dataset and software:

```bash
# Create the RO-Crate
fairscape-cli rocrate create \
    --name 'Simple Computation Example' \
    --organization-name 'Example Organization' \
    --project-name 'Data Processing Demo' \
    --date-published '2025-04-16' \
    --description 'A simple demonstration of data processing in an RO-Crate' \
    --keywords 'computation,demo,rocrate' \
    './simple-computation'

# Register the input dataset
fairscape-cli rocrate register dataset \
    './simple-computation' \
    --name 'Input Dataset' \
    --author 'Example Author' \
    --version '1.0' \
    --date-published '2025-04-16' \
    --description 'Input data for computation example' \
    --keywords 'data,input' \
    --data-format 'csv' \
    --filepath './simple-computation/input.csv'

# Register the software
fairscape-cli rocrate register software \
    './simple-computation' \
    --name 'Data Processing Software' \
    --author 'Example Developer' \
    --version '1.0' \
    --description 'Software that computes sum and product of two columns' \
    --keywords 'software,processing' \
    --file-format 'py' \
    --filepath './simple-computation/software.py' \
    --date-modified '2025-04-16'
```

### 1.3 Infer and Validate Input Data Against Schema

Let's create a schema for our input data and validate against it:

```bash
# Create the tabular schema
fairscape-cli schema create-tabular \
    --name 'Input Dataset Schema' \
    --description 'Schema for the input data used in the computation example' \
    --separator ',' \
    './simple-computation/input_schema.json'

# Add properties to the schema
fairscape-cli schema add-property integer \
    --name 'value1' \
    --index 0 \
    --description 'Column value1' \
    './simple-computation/input_schema.json'

fairscape-cli schema add-property integer \
    --name 'value2' \
    --index 1 \
    --description 'Column value2' \
    './simple-computation/input_schema.json'

# Register the schema with the RO-Crate
fairscape-cli schema add-to-crate \
    './simple-computation' \
    './simple-computation/input_schema.json'

# Validate the input data against the schema
fairscape-cli validate schema \
    --schema './simple-computation/input_schema.json' \
    --data './simple-computation/input.csv'
```

### 1.4 Run and Register the Computation

Execute the software and register the computation activity:

```bash
# Run the software to generate output
python ./simple-computation/software.py \
    ./simple-computation/input.csv \
    ./simple-computation/output.csv

# Register the computation
fairscape-cli rocrate register computation \
    './simple-computation' \
    --name 'Data Processing Computation' \
    --run-by 'Example Researcher' \
    --date-created '2025-04-16' \
    --description 'Computation that generates sum and product of input values' \
    --keywords 'computation,processing' \
    --used-software 'ark:59852/software-data-processing-software-XXXX' \
    --used-dataset 'ark:59852/dataset-input-dataset-XXXX' \
    --command 'python software.py input.csv output.csv'
```

Note: Replace the ARK identifiers with the actual values returned by your previous commands.

### 1.5 Register Output and Infer Schema

Register the output dataset and infer its schema:

```bash
# Register the output dataset with explicit --generated-by parameter
fairscape-cli rocrate register dataset \
    './simple-computation' \
    --name 'Output Dataset' \
    --author 'Example Author' \
    --version '1.0' \
    --date-published '2025-04-16' \
    --description 'Output data from computation example' \
    --keywords 'data,output' \
    --data-format 'csv' \
    --filepath './simple-computation/output.csv' \
    --generated-by 'ark:59852/computation-data-processing-computation-XXXX'

# Infer the schema and add it to the RO-Crate
fairscape-cli schema infer \
    --name 'Output Dataset Schema' \
    --description 'Schema for the output data used in the computation example' \
    --rocrate-path './simple-computation' \
    './simple-computation/output.csv' \
    './simple-computation/output_schema.json'

# Validate the output data against the inferred schema
fairscape-cli validate schema \
    --schema './simple-computation/output_schema.json' \
    --data './simple-computation/output.csv'
```

### 1.6 Generate a Provenance Graph for the Main Output

Create a visual representation of the data provenance:

```bash
# Generate evidence graph for the output dataset
fairscape-cli build evidence-graph \
    './simple-computation' \
    'ark:59852/dataset-output-dataset-XXXX'
```

This will create both JSON and HTML visualizations of the data provenance in the RO-Crate.

## Step 2: Build a Crate from External Repository Data

Now let's demonstrate how to pull data from an external repository and create a new RO-Crate.

### 2.1 Pull Data from an External Repository

```bash
# Pull data from a BioProject
fairscape-cli import bioproject \
    --accession "PRJDB2884" \
    --api-key "" \
    --output-dir "./sra-crate" \
    --author "Justin, Max"
```

This command fetches metadata from NCBI's BioProject database and creates a complete RO-Crate with that information.

### 2.2 Create Schemas for External Data

Let's create a schema for FASTQ sequence data:

```bash
# Create a tabular schema for FASTQ format
fairscape-cli schema create-tabular \
    --name 'fastq_data' \
    --description 'FASTQ sequence data schema' \
    --separator '\n' \
    --header 'false' \
    './sra-crate/fastq_schema.json'

# Add the header property to the schema
fairscape-cli schema add-property string \
    --name 'header' \
    --index '0' \
    --description 'The header line starting with @' \
    --pattern '^@.*' \
    './sra-crate/fastq_schema.json'

# Add the sequence property to the schema
fairscape-cli schema add-property string \
    --name 'sequence' \
    --index '1' \
    --description 'The nucleotide sequence' \
    --pattern '^[ATCGN]+$' \
    './sra-crate/fastq_schema.json'

# Add the plus sign line property to the schema
fairscape-cli schema add-property string \
    --name 'plus' \
    --index '2' \
    --description 'The plus sign line' \
    --pattern '^\+.*' \
    './sra-crate/fastq_schema.json'

# Add the quality scores property to the schema
fairscape-cli schema add-property string \
    --name 'quality_scores' \
    --index '3' \
    --description 'The quality scores in Phred+33 encoding' \
    './sra-crate/fastq_schema.json'

# Register the schema with the RO-Crate
fairscape-cli schema add-to-crate \
    './sra-crate' \
    './sra-crate/fastq_schema.json'
```

### 2.3 Generate Evidence Graph for External Data

Find a key dataset in the crate and generate its evidence graph:

```bash
# First, get the ID of a main dataset in the crate
DATASET_ID=$(grep -o "ark:59852/dataset-[a-zA-Z0-9-]*" ./sra-crate/ro-crate-metadata.json | head -1)

# Generate evidence graph for the dataset
fairscape-cli build evidence-graph \
    './sra-crate' \
    "$DATASET_ID" \
    --output-file './sra-crate/provenance-graph.json'
```

## Step 3: Build a Unified Release Crate

Now, let's build a release crate that combines our local computation and the external data:

```bash
# Create a release RO-Crate
fairscape-cli release build ./ \
    --guid "ark:59852/example-release-for-demo" \
    --name "SRA Genomic Data Example Release - 2025" \
    --organization-name "Example Research Institute" \
    --project-name "Genomic Data Analysis Project" \
    --description "This comprehensive dataset contains genomic data from multiple sources, including Japanese flounder (PRJDB2884) and human RNA-seq data (PRJEB86838) from the Sequence Read Archive (SRA). All data has been processed and prepared as AI-ready datasets in RO-Crate format, with appropriate metadata and provenance information to ensure FAIR data principles compliance." \
    --keywords "Genomics" \
    --keywords "SRA" \
    --keywords "RNA-seq" \
    --keywords "Sequence Read Archive" \
    --keywords "Bioinformatics" \
    --license "https://creativecommons.org/licenses/by/4.0/" \
    --version "1.0" \
    --publisher "University of Virginia Dataverse" \
    --principal-investigator "Dr. Example PI" \
    --copyright-notice "Copyright (c) 2025 The Regents of the University of California except where otherwise noted." \
    --conditions-of-access "Attribution is required to the copyright holders and the authors." \
    --contact-email "example@example.org" \
    --confidentiality-level "HL7 Unrestricted" \
    --funder "Example Agency" \
    --usage-info "This dataset is intended for research purposes in genomics, bioinformatics, and related fields." \
    --content-size "2.45 GB" \
    --citation "Example Research Institute (2025). SRA Genomic Data Example Release." \
    --associated-publication "Smith et al. (2025). Novel approaches to genomic data analysis using SRA datasets." \
    --completeness "These data contain complete processed datasets from the specified SRA projects." \
    --maintenance-plan "This dataset will be periodically updated with corrections or additional annotations." \
    --intended-use "This dataset is intended for genomic research and educational purposes." \
    --limitations "While comprehensive quality control has been performed, researchers should be aware of inherent limitations." \
    --potential-sources-of-bias "Original sample collection methods may introduce biases." \
    --prohibited-uses "Commercial redistribution without attribution is prohibited." \
    --human-subject "No"

# Generate a datasheet for the release
fairscape-cli build datasheet ./
```

This creates a unified release that includes both our individual RO-Crates with a comprehensive datasheet.

## Step 4: Publishing RO-Crates

Once you've created your RO-Crates and assembled them into a release, you can publish them to repositories for broader access and assign persistent identifiers.

### 4 Publish to Fairscape

```bash
fairscape-cli publish fairscape \
    --rocrate "./" \
    --username "your_username" \
    --password "your_password" \
    --api-url "https://fairscape.net/api"
```

## Conclusion

This workflow demonstrates the complete process of creating, managing, combining, and publishing research data packages using fairscape-cli. By following these steps, you can:

1. Create well-structured RO-Crates with proper metadata
2. Register data, software, and computations with appropriate relationships
3. Define and validate data schemas
4. Pull data from external repositories
5. Generate provenance visualizations
6. Build comprehensive release packages with rich metadata
7. Publish your data to fairscape

These capabilities enable FAIR (Findable, Accessible, Interoperable, Reusable) data sharing practices for scientific research, making your data discoverable, properly cited, and reusable by the broader community.

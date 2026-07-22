#!/bin/sh
# Simple Computation Demo
# Demonstrates a complete fairscape-cli workflow: creating an RO-Crate with
# input data, processing software, computation registration, schema validation,
# and provenance tracking.

set -e

# ============================================================================
# 1.1 Create Input File and Processing Script
# ============================================================================

mkdir -p ./simple-computation

# Create sample input.csv
python -c "
import pandas as pd
pd.DataFrame({
    'value1': [10, 20, 30, 40, 50],
    'value2': [5, 15, 25, 35, 45]
}).to_csv('./simple-computation/input.csv', index=False)
"

# Create processing script
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

# ============================================================================
# 1.2 Create and Register RO-Crate
# ============================================================================

fairscape-cli rocrate create \
    --name 'Simple Computation Example' \
    --organization-name 'Example Organization' \
    --project-name 'Data Processing Demo' \
    --date-published '2025-04-16' \
    --description 'A simple demonstration of data processing in an RO-Crate' \
    --keywords 'computation,demo,rocrate' \
    './simple-computation'

# Register the input dataset and store the returned GUID
INPUT_GUID=$(fairscape-cli rocrate register dataset \
    './simple-computation' \
    --name 'Input Dataset' \
    --author 'Example Author' \
    --version '1.0' \
    --date-published '2025-04-16' \
    --description 'Input data for computation example' \
    --keywords 'data,input' \
    --data-format 'csv' \
    --filepath './input.csv')

echo "Input GUID: $INPUT_GUID"

# Register the software and store the returned GUID
SOFTWARE_GUID=$(fairscape-cli rocrate register software \
    './simple-computation' \
    --name 'Data Processing Software' \
    --author 'Example Developer' \
    --version '1.0' \
    --description 'Software that computes sum and product of two columns' \
    --keywords 'software,processing' \
    --file-format 'py' \
    --filepath './software.py' \
    --date-modified '2025-04-16')

echo "Software GUID: $SOFTWARE_GUID"

# ============================================================================
# 1.3 Create and Validate Input Schema
# ============================================================================

fairscape-cli schema create-tabular \
    --name 'Input Dataset Schema' \
    --description 'Schema for the input data used in the computation example' \
    --separator ',' \
    './simple-computation/input_schema.json'

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

fairscape-cli schema add-to-crate \
    './simple-computation' \
    './simple-computation/input_schema.json'

fairscape-cli schema validate \
    --schema './simple-computation/input_schema.json' \
    --data './simple-computation/input.csv'

# ============================================================================
# 1.4 Run the Computation and Register It
# ============================================================================

python ./simple-computation/software.py \
    ./simple-computation/input.csv \
    ./simple-computation/output.csv

# Register the computation using the stored GUIDs
COMPUTATION_GUID=$(fairscape-cli rocrate register computation \
    './simple-computation' \
    --name 'Data Processing Computation' \
    --run-by 'Example Researcher' \
    --date-created '2025-04-16' \
    --description 'Computation that generates sum and product of input values' \
    --keywords 'computation,processing' \
    --used-software "$SOFTWARE_GUID" \
    --used-dataset "$INPUT_GUID" \
    --command 'python software.py input.csv output.csv')

echo "Computation GUID: $COMPUTATION_GUID"

# ============================================================================
# 1.5 Register Output and Infer Schema
# ============================================================================

# Register the output dataset using the stored computation GUID
OUTPUT_GUID=$(fairscape-cli rocrate register dataset \
    './simple-computation' \
    --name 'Output Dataset' \
    --author 'Example Author' \
    --version '1.0' \
    --date-published '2025-04-16' \
    --description 'Output data from computation example' \
    --keywords 'data,output' \
    --data-format 'csv' \
    --filepath './output.csv' \
    --generated-by "$COMPUTATION_GUID")

echo "Output GUID: $OUTPUT_GUID"

# Infer the schema and add it to the RO-Crate
fairscape-cli schema infer \
    --name 'Output Dataset Schema' \
    --description 'Schema for the output data used in the computation example' \
    --rocrate-path './simple-computation' \
    './simple-computation/output.csv' \
    './simple-computation/output_schema.json'

# Validate the output data against the inferred schema
fairscape-cli schema validate \
    --schema './simple-computation/output_schema.json' \
    --data './simple-computation/output.csv'

# ============================================================================
# 1.6 Build the Subcrate
# ============================================================================

# Generates HTML preview, croissant metadata, and fills in inverse properties
fairscape-cli build subcrate './simple-computation'

echo "Done! RO-Crate created at ./simple-computation"

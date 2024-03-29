#!/bin/bash

#####################################
#       TEST TABULAR VALIDATION     #
#####################################

SCHEMA_PATH="./tests/test_generated/schema_apms_music_embedding.json"

# clear the schema path
rm $SCHEMA_PATH

echo "CREATE SCHEMA"
fairscape-cli schema create-tabular \
    --name "APMS Embedding Schema" \
    --description "Tabular format for APMS music embeddings from PPI networks from the music pipeline from the B2AI Cellmaps for AI project" \
    --separator "," \
    --header False \
    $SCHEMA_PATH

echo "ADD PROPERTY STRING"
fairscape-cli schema add-property string \
    --name 'Experiment Identifier' \
    --index 0 \
    --description 'Identifier for the APMS experiment responsible for generating the raw PPI used to create this embedding vector' \
    --pattern 'APMS_[0-9]*' \
    $SCHEMA_PATH

fairscape-cli schema add-property string \
    --name 'Gene Symbol' \
    --index 1 \
    --description 'Gene Symbol for the APMS bait protien' \
    --pattern '[A-Z0-9]*' \
    --value-url 'http://edamontology.org/data_1026' \
    $SCHEMA_PATH


echo "ADD PROPERTY ARRAY"
fairscape-cli schema add-property array \
    --name 'MUSIC APMS Embedding' \
    --index '2::' \
    --description 'Embedding Vector values for genes determined by running node2vec on APMS PPI networks. Vector has 1024 values for each bait protien' \
    --items-datatype 'number' \
    --unique-items False \
    --min-items 1024 \
    --max-items 1024 \
    $SCHEMA_PATH


echo "VALIDATE SCHEMA"
fairscape-cli schema validate \
    --data examples/schemas/MUSIC_embedding/APMS_embedding_MUSIC.csv \
    --schema $SCHEMA_PATH

# test intentional failure of validation
fairscape-cli schema validate \
    --data examples/schemas/MUSIC_embedding/APMS_embedding_corrupted.csv \
    --schema examples/schemas/MUSIC_embedding/music_apms_embedding_schema.json 

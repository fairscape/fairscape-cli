# tests for fairscape-cli using the BATS framework for shell scripts
setup() {
    load 'test_helper/bats-support/load'
    load 'test_helper/bats-assert/load'

    
}

@test "schema default apms-embedding" {
    # Test all default schemas against data in examples
    #

    SCHEMA="ark:59852/schema-cm4ai-apms-embedding"
    DATA="examples/schemas/cm4ai-rocrates/apms_embedding/ppi_emd.tsv"

    run fairscape-cli schema validate \
        --data $DATA \
        --schema $SCHEMA

    assert_success
}

@test "schema default apmsloader" {

    SCHEMA="ark:59852/schema-cm4ai-apmsloader-ppi-edgelist"
    DATA="examples/schemas/cm4ai-rocrates/apmsloader/ppi_edgelist.tsv"

    run fairscape-cli schema validate \
        --data $DATA \
        --schema $SCHEMA

    assert_success

    SCHEMA="ark:59852/schema-cm4ai-apmsloader-gene-node-attributes"
    DATA="examples/schemas/cm4ai-rocrates/apmsloader/ppi_gene_node_attributes.tsv"

    run fairscape-cli schema validate \
        --data $DATA \
        --schema $SCHEMA

    assert_success
}

@test "schema default coembedding" {
    SCHEMA="ark:59852/schema-cm4ai-coembedding"
    DATA="examples/schemas/cm4ai-rocrates/coembedding/coembedding_emd.tsv"
    
    run fairscape-cli schema validate \
        --data $DATA \
        --schema $SCHEMA
    assert_success

}

@test "schema default imageloader" {

    SCHEMA="ark:59852/schema-cm4ai-imageloader-gene-node-attributes"
    DATA="examples/schemas/cm4ai-rocrates/imageloader/image_gene_node_attributes.tsv"
    
    run fairscape-cli schema validate \
        --data $DATA \
        --schema $SCHEMA

    assert_success
    

    SCHEMA="ark:59852/schema-cm4ai-imageloader-samplescopy"
    DATA="examples/schemas/cm4ai-rocrates/imageloader/samplescopy.csv"
    
    run fairscape-cli schema validate \
        --data $DATA \
        --schema $SCHEMA
    assert_success

    SCHEMA="ark:59852/schema-cm4ai-imageloader-uniquecopy"
    DATA="examples/schemas/cm4ai-rocrates/imageloader/uniquecopy.csv"
    
    run fairscape-cli schema validate \
        --data $DATA \
        --schema $SCHEMA
    assert_success
}

@test "schema default imageembedding" {

    SCHEMA="ark:59852/schema-cm4ai-image-embedding-image-emd"
    DATA="examples/schemas/cm4ai-rocrates/image_embedding/image_emd.tsv"

    run fairscape-cli schema validate \
        --data $DATA \
        --schema $SCHEMA
    assert_success
    assert_output -p 'Validation Success'
    

    SCHEMA="ark:59852/schema-cm4ai-image-embedding-labels-prob"
    DATA="examples/schemas/cm4ai-rocrates/image_embedding/labels_prob.tsv"
    
    run fairscape-cli schema validate \
        --data $DATA \
        --schema $SCHEMA
    assert_success
    assert_output -p 'Validation Success'
}

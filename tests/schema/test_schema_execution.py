from fairscape_cli.models.schema.tabular import (
    TabularValidationSchema,
    ReadSchema
)


def ExecuteSchema(schema_path, data_path):
    schema_root_path = './examples/schemas/cm4ai-schemas/v0.1.0/'
    crate_root_path = './examples/schemas/cm4ai-rocrates/'
 
    tabular_schema = ReadSchema(schema_root_path + schema_path)

    failures = tabular_schema.execute_validation(crate_root_path + data_path)
    return failures


class TestSchemaExecution():

    def test_0_apms_loader_schema_edgelist(self):
        data = 'apmsloader/ppi_gene_node_attributes.tsv'
        schema = 'cm4ai_schema_apmsloader_ppi_edgelist.json'
        
        failures = ExecuteSchema(
                schema, 
                data
                )

        assert len(failures) == 0


    def test_1_apms_loader_schema_gene_node(self):
        data = 'apmsloader/ppi_gene_node_attributes.tsv'
        schema = 'cm4ai_schema_apmsloader_ppi_edgelist.json'
        
        failures = ExecuteSchema(
                schema, 
                data
                )

        assert len(failures) == 0


    def test_2_apms_embedding(self):
        schema = 'cm4ai_schema_apms_embedding.json'
        data = 'apms_embedding/ppi_emd.tsv'
        
        failures = ExecuteSchema(
                schema, 
                data
                )

        assert len(failures) == 0


    def test_3_image_loader_samplescopy(self):
        schema = 'cm4ai_schema_imageloader_samplescopy.json'
        data = 'imageloader/samplescopy.csv'
        
        failures = ExecuteSchema(
                schema, 
                data
                )

        assert len(failures) == 0

    
    def test_4_image_loader_uniquecopy(self):
        schema = 'cm4ai_schema_imageloader_uniquecopy.json'
        data = 'imageloader/uniquecopy.csv'
        
        failures = ExecuteSchema(
                schema, 
                data
                )

        assert len(failures) == 0

    
    def test_5_image_embedding_labels(self):
        schema = 'cm4ai_schema_image_embedding_labels_prob.json'
        data = 'image_embedding/labels_prob.tsv'
        
        failures = ExecuteSchema(
                schema, 
                data
                )

        assert len(failures) == 0
    

    def test_6_image_embedding_emd(self):
        image_emd_schema = 'cm4ai_schema_image_embedding_emd.json'
        image_emd_data = 'image_embedding/image_emd.tsv'
        
        failures = ExecuteSchema(
                image_emd_schema, 
                image_emd_data
                )

        assert len(failures) == 0


    def test_7_coembedding(self):
        coembedding_schema = 'cm4ai_schema_coembedding.json'
        coembedding_data = 'coembedding/coembedding_emd.tsv' 
        failures = ExecuteSchema(
                coembedding_schema, 
                coembedding_data
                )

        assert len(failures) == 0


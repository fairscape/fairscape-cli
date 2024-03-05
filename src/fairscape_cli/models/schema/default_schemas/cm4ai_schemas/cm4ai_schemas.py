import os
from fairscape_cli.models.schema.tabular import (
        ReadSchema
)

cm4ai_schemas_location = os.path.dirname(os.path.realpath(__file__))
# for every schema set the path
apms_loader_edgelist_schema_path = os.path.join(
    cm4ai_schemas_location, 
    'cm4ai_schema_apmsloader_ppi_edgelist.json'
)

apms_loader_gene_node_schema_path = os.path.join(
     cm4ai_schemas_location, 
     'cm4ai_schema_apmsloader_ppi_gene_node_attributes.json'
)

apms_embedding_schema_path = os.path.join(
     cm4ai_schemas_location, 
     'cm4ai_schema_apms_embedding.json'
)

image_loader_samplescopy_schema_path = os.path.join(
     cm4ai_schemas_location, 
     'cm4ai_schema_imageloader_samplescopy.json'
)

image_loader_uniquecopy_schema_path = os.path.join(
     cm4ai_schemas_location, 
     'cm4ai_schema_imageloader_uniquecopy.json'
)

image_embedding_labels_schema_path = os.path.join(
     cm4ai_schemas_location, 
    'cm4ai_schema_image_embedding_labels_prob.json'
)

image_embedding_emd_schema_path = os.path.join(
     cm4ai_schemas_location, 
    'cm4ai_schema_image_embedding_emd.json'
)

coembedding_schema_path = os.path.join(
     cm4ai_schemas_location, 
    'cm4ai_schema_coembedding.json'
)

schema_paths = [
    apms_loader_edgelist_schema_path,
    apms_loader_gene_node_schema_path,
    apms_embedding_schema_path,
    image_loader_uniquecopy_schema_path,
    image_loader_samplescopy_schema_path,
    image_embedding_labels_schema_path,
    image_embedding_emd_schema_path,
    coembedding_schema_path
]

cm4ai_schemas = [ ReadSchema(str(path_elem)) for path_elem in schema_paths]

CM4AI_DEFAULT_SCHEMAS = {
        Schema.guid : Schema for Schema in cm4ai_schemas
}

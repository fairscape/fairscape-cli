from fairscape_cli.models.schema.image import (
    ImageSchema,
    ImageValidation,
    ImageValidationException,
    ImagePathNotFoundException,
)
from fairscape_cli.models.schema.tabular import (
	ReadSchemaLocal,
	ReadSchemaGithub,
	ReadSchemaFairscape,
	TabularValidationSchema,
	ImportDefaultSchemas,
	ReadSchema
)
from fairscape_cli.config import (
	DEFAULT_SCHEMA_TYPE,
	DEFAULT_CONTEXT,
	NAAN
)
import pathlib
from unittest import TestCase

from fairscape_cli.__main__ import cli as fairscape_cli_app
import pathlib
from click.testing import CliRunner
import pytest

runner = CliRunner()


class TestReadSchema(TestCase):
	def test_0_read_schema_local(self):
		# read in a local schema
		exampleDirectory = pathlib.Path(
			'examples/schemas/cm4ai-schemas/v0.1.0/'
			)

		schemaFiles = exampleDirectory.rglob('*.json')

		for schemaFilepath in schemaFiles:
			resultSchema = ReadSchemaLocal(schemaFilepath)
			assert isinstance(resultSchema, TabularValidationSchema)
			# check that properties are instantiated
			assert resultSchema is not None
			assert resultSchema.guid is not None


	def test_1_read_schema_default(self):
		# check that read schema can read the default schemas
		defaultSchemaArks = [
			"ark:59852/schema-cm4ai-apms-embedding",
			"ark:59852/schema-cm4ai-apmsloader-ppi-edgelist",
			"ark:59852/schema-cm4ai-apmsloader-gene-node-attributes",
			"ark:59852/schema-cm4ai-coembedding",
			"ark:59852/schema-cm4ai-image-embedding-image-emd",
			"ark:59852/schema-cm4ai-image-embedding-labels-prob",
			"ark:59852/schema-cm4ai-imageloader-samplescopy",
            "ark:59852/schema-cm4ai-imageloader-gene-node-attributes",
			"ark:59852/schema-cm4ai-imageloader-uniquecopy"
		]
		
		# import default schemas
		DefaultSchemas = ImportDefaultSchemas()
		assert len(DefaultSchemas) != 0

		for tabularSchema in DefaultSchemas:
			assert isinstance(tabularSchema, TabularValidationSchema)
			assert tabularSchema.guid in defaultSchemaArks


	def test_2_read_schema_github(self):
		schemaURI = ''
		githubSchema = ReadSchemaGithub(schemaURI)


	def test_3_read_schema_fairscape(self):
		schemaArk = ''
		fairscapeSchema = ReadSchemaFairscape(schemaArk)


	def test_4_read_schema(self):
		defaultSchemaArks = [
			"ark:59852/schema-cm4ai-apms-embedding",
			"ark:59852/schema-cm4ai-apmsloader-ppi-edgelist",
			"ark:59852/schema-cm4ai-apmsloader-gene-node-attributes",
			"ark:59852/schema-cm4ai-coembedding",
			"ark:59852/schema-cm4ai-image-embedding-image-emd",
			"ark:59852/schema-cm4ai-image-embedding-labels-prob",
			"ark:59852/schema-cm4ai-imageloader-samplescopy",
			"ark:59852/schema-cm4ai-imageloader-uniquecopy"
		]

		for defaultSchemaGUID in defaultSchemaArks:
			defaultSchemaInstance = ReadSchema(defaultSchemaGUID)
			assert isinstance(defaultSchemaInstance, TabularValidationSchema)
			assert defaultSchemaInstance.guid in defaultSchemaArks
			assert NAAN in defaultSchemaInstance.guid

			self.assertDictEqual(defaultSchemaInstance.context, DEFAULT_CONTEXT)
			assert defaultSchemaInstance.metadataType == DEFAULT_SCHEMA_TYPE

			assert defaultSchemaInstance.name is not None
			assert defaultSchemaInstance.description is not None
			assert len(defaultSchemaInstance.properties.keys()) != 0




def ExecuteSchema(schema_path, data_path):
    schema_root_path = './examples/schemas/cm4ai-schemas/v0.1.0/'
    crate_root_path = './examples/schemas/cm4ai-rocrates/'

    schemaFullpath = schema_root_path + schema_path
    tabular_schema = ReadSchema(schemaFullpath)

    failures = tabular_schema.execute_validation(crate_root_path + data_path)
    return failures


class TestSchemaExecution(TestCase):

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


def cliExecuteValidate(schema, data):
    data_path = './examples/schemas/cm4ai-rocrates/' + data
    test_command = [
        "schema",
        "validate",
        "--schema",
        schema,
        "--data",
        data_path
    ]

    result = runner.invoke(
        fairscape_cli_app, 
        test_command
        )

    return result

class TestCLI(TestCase):
    def test_0_execute_default_schames(self):
	    
        defaultSchemaArks = [
			"ark:59852/schema-cm4ai-apmsloader-gene-node-attributes",
			"ark:59852/schema-cm4ai-coembedding",
			"ark:59852/schema-cm4ai-image-embedding-image-emd",
			"ark:59852/schema-cm4ai-image-embedding-labels-prob",
			"ark:59852/schema-cm4ai-imageloader-samplescopy",
			"ark:59852/schema-cm4ai-imageloader-uniquecopy"
		]

        # create a test schema
        data = 'apmsloader/ppi_gene_node_attributes.tsv'
        schema = "ark:59852/schema-cm4ai-apmsloader-gene-node-attributes"
        ppi_gene_node_result = cliExecuteValidate(
            schema,
            data
        )
     
        assert ppi_gene_node_result.exit_code == 0 

        # apms embedding 
        schema = "ark:59852/schema-cm4ai-apms-embedding"
        data = 'apms_embedding/ppi_emd.tsv'        
        apms_embedding_result = cliExecuteValidate(
            schema,
            data
        )

        assert apms_embedding_result.exit_code == 0 


        
class TestImage():

    def _test_success(self):

        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1728,
            "width": 1728,
            "colorspace": "RGB"
        })

        blue_image_path = pathlib.Path("./tests/data/1_A1_1_blue.jpg")
        red_image_path = pathlib.Path("./tests/data/1_A1_1_red.jpg")
        green_image_path = pathlib.Path("./tests/data/1_A1_1_green.jpg")
        yellow_image_path = pathlib.Path("./tests/data/1_A1_1_yellow.jpg")

        validate_blue = ImageValidation(
            image_schema=if_image_schema,
            image_path=blue_image_path
        )

        validate_blue.validate()

        validate_red = ImageValidation(
            image_schema=if_image_schema,
            image_path=red_image_path
        )

        validate_red.validate()

        validate_green = ImageValidation(
            image_schema=if_image_schema,
            image_path=green_image_path
        )

        validate_green.validate()

        validate_yellow = ImageValidation(
            image_schema=if_image_schema,
            image_path=yellow_image_path
        )

        validate_yellow.validate()

    def _test_path_not_found(self):

        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1728,
            "width": 10000,
            "colorspace": "RGB"
        })

        nonexistant_image_path = pathlib.Path("./not_an_image.jpg")

        with pytest.raises(ImagePathNotFoundException):

            validate_nonexistant = ImageValidation(
                image_schema=if_image_schema,
                image_path=nonexistant_image_path
            )

    def _test_width_incorrect(self):

        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1728,
            "width": 10000,
            "colorspace": "RGB"
        })

        blue_image_path = pathlib.Path("./tests/data/1_A1_1_blue.jpg")

        validate_blue = ImageValidation(
            image_schema=if_image_schema,
            image_path=blue_image_path
        )

        with pytest.raises(ImageValidationException):
            validate_blue.validate()

    def _test_height_incorrect(self):
        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1000,
            "width": 1728,
            "colorspace": "RGB"
        })

        blue_image_path = pathlib.Path("./tests/data/1_A1_1_blue.jpg")

        validate_blue = ImageValidation(
            image_schema=if_image_schema,
            image_path=blue_image_path
        )

        with pytest.raises(ImageValidationException):
            validate_blue.validate()

    def _test_colorspace_mismatch(self):
        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1728,
            "width": 1728,
            "colorspace": "GRAY"
        })

        blue_image_path = pathlib.Path("./tests/data/1_A1_1_blue.jpg")

        validate_blue = ImageValidation(
            image_schema=if_image_schema,
            image_path=blue_image_path
        )

        with pytest.raises(ImageValidationException):
            validate_blue.validate()

    def _test_format_mismatch(self):
        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1728,
            "width": 1728,
            "colorspace": "GRAY"
        })

        blue_image_path = pathlib.Path("./tests/data/1_A1_1_blue.jpg")

        validate_blue = ImageValidation(
            image_schema=if_image_schema,
            image_path=blue_image_path
        )

        with pytest.raises(ImageValidationException):
            validate_blue.validate()


class TestValidateTabular():
    def test_0_init(self):
        pass


class TestSchemaCLI():

    def test_0_create_schema(self):
        pass


    def test_1_add_string_property(self):
        pass


    def test_2_add_int_property(self):
        pass


    def test_3_add_bool_property(self):
        pass


    def test_4_add_number_property(self):
        pass

    def test_5_add_array_property_string(self):
        pass

    def test_6_add_array_property_int(self):
        pass

    def test_7_add_array_property_number(self):
        pass

    def test_8_add_array_property_bool(self):
        pass


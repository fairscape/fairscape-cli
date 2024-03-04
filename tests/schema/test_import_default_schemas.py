from unittest import TestCase
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

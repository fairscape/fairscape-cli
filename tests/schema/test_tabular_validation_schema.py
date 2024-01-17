import os
import sys

sys.path.insert(
    0, 
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), 
        '../..')
    )
)

import pathlib
import json
from click.testing import CliRunner
from fairscape_cli.models.schema.tabular import (
    TabularValidationSchema,
    StringProperty,
    BooleanProperty,
    IntegerProperty,
    NumberProperty,
    ArrayProperty,
    DatatypeEnum,
    Items,
    AppendProperty,
    ReadSchema
)
from typing import (
    Dict, List
)
from fairscape_cli.__main__ import cli as fairscape_cli_app

runner = CliRunner()

output_path = "tests/data/schema/test_schema.json"

testSchemaData = {
    "name": "test-schema",
    "guid": "ark:99999/test-schema",
    "description": "A Test Schema for APMS Embedding Data",
    "seperator": ",",
    "header": False
}

testStringPropertyData = {
    "datatype": "string", 
    "name": "Gene Name",
    "number": 1,
    "description": "Gene Name for APMS Data",
    "pattern": "[A-Z0-9]*",
    "valueURL": "http://edamontology.org/data_1026"
}

testIntegerPropertyData = {
    "datatype": "integer",
    "name": "Example Integer Property",
    "number": 2,
    "description": "Example integer property",
    "valueURL": None,

}

testBooleanPropertyData = {
    "datatype": "boolean",
    "name": "Example Bool Property",
    "number": 3,
    "description": "Test Boolean Property",
    "valueURL": None
}

testNumberPropertyData = {
    "datatype": "number",
    "name": "Example Number Property",
    "number": 4,
    "description": "Testing Number Property",
    "valueURL": None
}

testArrayPropertyData = {
    "datatype": "array",
    "name": "embedding",
    "number": "5::",
    "minItems": 1024,
    "maxItems": 1024,
    "itemsDatatype": "number",
    "uniqueItems": False,
    "description": "embedding vector values for genes determined by running node2vec on APMS networks",
}

class TestModelGroup():


    def test_0_tabular_validation(self):
        schema_model = TabularValidationSchema(**testSchemaData)
        schema_output_dict = schema_model.model_dump(by_alias=True)
        assert schema_output_dict is not None 


    def test_1_string_property(self):
        string_property_model = StringProperty(**testStringPropertyData)
        string_property_output = string_property_model.model_dump(by_alias=True)
        assert string_property_output is not None


    def test_2_array_property(self):
        array_property_model = ArrayProperty(
            datatype = "array",
            number = testArrayPropertyData['number'],
            description = testArrayPropertyData['description'],
            valueURL = testArrayPropertyData.get('valueURL'),
            maxItems = testArrayPropertyData['maxItems'],
            minItems = testArrayPropertyData['minItems'],
            uniqueItems = testArrayPropertyData['uniqueItems'],
            items = Items(datatype=testArrayPropertyData['itemsDatatype'])
        )
        array_property_output = array_property_model.model_dump(by_alias=True)
        assert array_property_output is not None


    def test_models_3_boolean_property(self):
        bool_property_model = BooleanProperty(**testBooleanPropertyData)
        bool_property_output = bool_property_model.model_dump(by_alias=True)
        assert bool_property_output is not None


    def test_models_4_integer_property(self):
        int_property_model = IntegerProperty(**testIntegerPropertyData)
        int_property_output = int_property_model.model_dump(by_alias=True)
        assert int_property_output is not None


    def test_models_5_number_property(self):
        num_property_model = NumberProperty(**testNumberPropertyData)
        num_property_output = num_property_model.model_dump(by_alias=True)
        assert num_property_output is not None



def test_addProperty():
    # create a test schema to add properties to
    outputPath = "tests/data/schema/add_property_schema.json"

    # clear the test schema
    pathlib.Path(outputPath).unlink(missing_ok=True)

    # create a test schema
    test_command = [
        "schema",
        "create-tabular",
        "--name",
        testSchemaData['name'],
        "--description",
        testSchemaData['description'],
        "--seperator",
        testSchemaData['seperator'],
        "--header",
        testSchemaData['header'],
        outputPath
    ]

    result = runner.invoke(
        fairscape_cli_app, 
        test_command
        )

    assert result.exit_code == 0 

    # add a string property to the schema
    stringMetadata = {
        "datatype": "string",
        "name": "string property",
        "number": 0,
        "description": "an example string property",
        "pattern": "r'[0-3]'", 
    }
    stringInstance = StringProperty(**stringMetadata)
    AppendProperty(outputPath, stringInstance, "string property")

    # read the schema and assert a string property is set correctly
    schemaModel = ReadSchema(outputPath)

    def checkPropertiesSet(passedSchemaModel: TabularValidationSchema, metadata: Dict, attributesToCheck: List[str]): 
        propertyName = metadata.get("name")

        assert propertyName in list(passedSchemaModel.properties.keys())

        propertyObject = passedSchemaModel.properties[propertyName].model_dump(by_alias=True)
        for metadataAttribute in attributesToCheck:
            assert propertyObject[metadataAttribute] == metadata[metadataAttribute]


    # check that the string property is instantiated
    assert schemaModel.properties != {} 
    assert len(list(schemaModel.properties.keys())) == 1


    # check the attributes of the string property
    checkPropertiesSet(schemaModel, stringMetadata, ['number', 'description', 'pattern'])

    # add an integer property to the schema
    integerMetadata = {
        "datatype": "integer",
        "name": "integer property",
        "number": 1,
        "description": "an example integer property",
    }
    integerInstance = IntegerProperty(**integerMetadata)
    AppendProperty(outputPath, integerInstance, "integer property")

    # read the schema model again
    schemaModel = ReadSchema(outputPath)
    assert len(list(schemaModel.properties.keys())) == 2
    checkPropertiesSet(schemaModel, integerMetadata, ['number', 'description'])

    # add a number property to the schema
    numberMetadata = {
        "datatype": "number",
        "name": "number property",
        "number": 2,
        "description": "an example number property",
    }
    numberInstance = NumberProperty(**numberMetadata)
    AppendProperty(outputPath, numberInstance, "number property")

    # read the schema model again
    schemaModel = ReadSchema(outputPath)
    assert len(list(schemaModel.properties.keys())) == 3
    checkPropertiesSet(schemaModel, numberMetadata, ['number', 'description'])

    # add a boolean property to the schema
    booleanMetadata = {
        "datatype": "boolean",
        "name": "boolean property",
        "number": 3,
        "description": "an example boolean property",
    }
    booleanInstance = BooleanProperty(**booleanMetadata)
    AppendProperty(outputPath, booleanInstance, "boolean property")

    # read the schema model again
    schemaModel = ReadSchema(outputPath)
    assert len(list(schemaModel.properties.keys())) == 4
    checkPropertiesSet(schemaModel, numberMetadata, ['number', 'description'])

    # add an array property to the schema
    arrayMetadata = {
        "number": "4::",
        "name": "array property",
        "description": "an example array property",
        "minItems": 4,
        "maxItems": 6,
        "uniqueItems": False,
        "items":{"type":  "number"},
    }

    arrayPropertyModel = ArrayProperty(
        datatype = "array",
        number = "4::",
        description = "an example array property",
        valueURL = None,
        minItems = 4,
        maxItems = 6,
        uniqueItems = False,
        items = Items(datatype="number")
    )

    AppendProperty(outputPath,  arrayPropertyModel, "array property")
    schemaModel = ReadSchema(outputPath)
    # check that properties are set 
    assert len(list(schemaModel.properties.keys())) == 5
    checkPropertiesSet(schemaModel, arrayMetadata, ['number', 'description', "minItems", "maxItems", "uniqueItems"])



class TestCLI():
    output_path = "tests/data/schema/test_cli_schema.json"

    def test_0_create_schema(self):

        # clear the test schema
        pathlib.Path(output_path).unlink(missing_ok=True)

        # create a test schema
        test_command = [
            "schema",
            "create-tabular",
            "--name",
            testSchemaData['name'],
            "--description",
            testSchemaData['description'],
            "--seperator",
            testSchemaData['seperator'],
            "--header",
            testSchemaData['header'],
            self.output_path
        ]

        result = runner.invoke(
            fairscape_cli_app, 
            test_command
            )

        print(result.output)
        assert result.exit_code == 0 

        # read the schema
        tabular_schema = ReadSchema(self.output_path)



    def test_schema_cli_1_property_string(self):
        # add a string property
        string_test_command = [
            "schema",
            "add-property",
            "string",
            "--number",
            testStringPropertyData['number'],
            "--name",
            testStringPropertyData['name'],
            "--description",
            testStringPropertyData['description'],
            "--pattern",
            testStringPropertyData['pattern'],
            "--value-url",
            testStringPropertyData['valueURL'],
            self.output_path
        ]
        string_result = runner.invoke(
            fairscape_cli_app, 
            string_test_command
        )
        print(string_result.output)
        assert string_result.exit_code == 0


    def test_schema_cli_2_property_int(self):
        # add a int property
        int_test_command = [
            "schema",
            "add-property",
            "integer",
            "--number",
            testIntegerPropertyData['number'],
            "--name",
            testIntegerPropertyData['name'],
            "--description",
            testIntegerPropertyData['description'],
            self.output_path
        ]
        int_result = runner.invoke(
            fairscape_cli_app, 
            int_test_command
        )
        assert int_result.exit_code == 0# }}}


    def test_schema_cli_3_property_bool(self):
        # add a boolean property
        bool_test_command = [
            "schema",
            "add-property",
            "boolean",
            "--number",
            testBooleanPropertyData['number'],
            "--name",
            testBooleanPropertyData['name'],
            "--description",
            testBooleanPropertyData['description'],
            self.output_path
        ]
        bool_result = runner.invoke(
            fairscape_cli_app, 
            bool_test_command
        )
        assert bool_result.exit_code == 0


    def test_schema_cli_4_array(self):
        # add an array property
        array_test_command = [
            "schema",
            "add-property",
            "array",
            "--number",
            testArrayPropertyData['number'],
            "--name",
            testArrayPropertyData['name'],
            "--description",
            testArrayPropertyData['description'],
            "--items-datatype",
            testArrayPropertyData['itemsDatatype'],
            "--unique-items",
            testArrayPropertyData['uniqueItems'],
            "--max-items",
            testArrayPropertyData['maxItems'],
            "--min-items",
            testArrayPropertyData['minItems'],
            self.output_path
        ]
        array_result = runner.invoke(
            fairscape_cli_app, 
            array_test_command
        )
        assert array_result.exit_code == 0


def test_json_conversion():


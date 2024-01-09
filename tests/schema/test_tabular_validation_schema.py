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
Items
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
    "type": "string", 
    "name": "Gene Name",
    "number": 1,
    "description": "Gene Name for APMS Data",
    "pattern": "[A-Z0-9]*",
    "valueURL": "http://edamontology.org/data_1026"
}

testIntegerPropertyData = {
    "type": "integer",
    "name": "Example Integer Property",
    "number": 2,
    "description": "Example integer property",
    "valueURL": None,

}

testBooleanPropertyData = {
    "type": "boolean",
    "name": "Example Bool Property",
    "number": 3,
    "description": "Test Boolean Property",
    "valueURL": None
}

testNumberPropertyData = {
    "type": "number",
    "name": "Example Number Property",
    "number": 4,
    "description": "Testing Number Property",
    "valueURL": None
}

testArrayPropertyData = {
    "type": "array",
    "name": "embedding",
    "number": "5::",
    "minItems": 1024,
    "maxItems": 1024,
    "itemsDatatype": "number",
    "uniqueItems": False,
    "description": "embedding vector values for genes determined by running node2vec on APMS networks",
}


def test_models_0_tabular_validation():
    schema_model = TabularValidationSchema(**testSchemaData)
    schema_output_dict = schema_model.model_dump(by_alias=True)
    assert schema_output_dict is not None 


def test_models_1_string_property():
    string_property_model = StringProperty(**testStringPropertyData)
    string_property_output = string_property_model.model_dump(by_alias=True)
    assert string_property_output is not None

    
def test_models_2_array_property():
    array_property_model = ArrayProperty(
        type = "array",
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


def test_models_3_boolean_property():
    bool_property_model = BooleanProperty(**testBooleanPropertyData)
    bool_property_output = bool_property_model.model_dump(by_alias=True)
    assert bool_property_output is not None


def test_models_4_integer_property():
    int_property_model = IntegerProperty(**testIntegerPropertyData)
    int_property_output = int_property_model.model_dump(by_alias=True)
    assert int_property_output is not None


def test_models_5_number_property():
    num_property_model = NumberProperty(**testNumberPropertyData)
    num_property_output = num_property_model.model_dump(by_alias=True)
    assert num_property_output is not None



def _test_schema_cli_0_creation():

    output_path = "tests/data/schema/test_schema.json"

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
        output_path
    ]

    result = runner.invoke(
        fairscape_cli_app, 
        test_command
        )

    print(result.output)
    assert result.exit_code == 0

def test_schema_cli_1_property_string():

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
        output_path
    ]
    string_result = runner.invoke(
        fairscape_cli_app, 
        string_test_command
    )
    print(string_result.output)
    assert string_result.exit_code == 0


def test_schema_cli_2_property_int():

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
        output_path
    ]
    int_result = runner.invoke(
        fairscape_cli_app, 
        int_test_command
    )
    assert int_result.exit_code == 0

def test_schema_cli_3_property_bool():
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
        output_path
    ]
    bool_result = runner.invoke(
        fairscape_cli_app, 
        bool_test_command
    )
    assert bool_result.exit_code == 0


def test_schema_cli_4_array():
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
        output_path
    ]
    array_result = runner.invoke(
        fairscape_cli_app, 
        array_test_command
    )
    assert array_result.exit_code == 0
    


    # read schema file and assert that the property exists
    #with open(output_path, "r") as schema_jsonfile:
    #	schema_dict = json.loads(schema_jsonfile.read())

from jsonschema import validate
import pandas as pd
import datetime
import pathlib
import json
import click

from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    Field,
    ValidationError,
)
from typing import (
    Dict, 
    List, 
    Optional,
    Union,
    Literal
)

from fairscape_cli.models.tabular.utils import (
    GenerateSlice,
    GenerateGUID
)


from enum import Enum
import re


# TODO set to configuration
NAAN = "59852"


# datatype enum
class DatatypeEnum(str, Enum):
    NULL = "null"
    BOOLEAN = "boolean"
    OBJECT = "object"
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    ARRAY = "array"

class Items(BaseModel):
    model_config = ConfigDict(
            populate_by_name = True,
            use_enum_values=True
    )
    datatype: DatatypeEnum = Field(alias="type")


class BaseProperty(BaseModel):
    description: str = Field(description="description of field")
    model_config = ConfigDict(populate_by_name = True)
    number: Union[int,str] = Field(description="index of the column for this value")
    valueURL: Optional[str] = Field(default=None)	
    #multiple: Optional[bool]
    #seperator: Optional[str]


class NullProperty(BaseProperty):
    datatype: Literal['null'] = Field(alias="type", default='null')


class StringProperty(BaseProperty):
    datatype: Literal['string'] = Field(alias="type")
    pattern: Optional[str] = Field(description="Regex pattern to execute against values", default=None)
    maxLength: Optional[int] = Field(description="Inclusive maximum length for string values", default=None)
    minLength: Optional[int] = Field(description="Inclusive minimum length for string values", default=None)
    number: int


class ArrayProperty(BaseProperty):
    datatype: Literal['array'] = Field(alias="type")
    maxItems: int = Field(description="max items in array, validation fails if length is greater than this value")
    minItems: Optional[int] = Field(description="min items in array, validation fails if lenght is shorter than this value")
    uniqueItems: Optional[bool] = Field()
    number: str
    items: Items


class BooleanProperty(BaseProperty):
    datatype: Literal['boolean'] = Field(alias="type")
    number: int


class NumberProperty(BaseProperty):
    datatype: Literal['number'] = Field(alias="type")
    maximum: Optional[float] = Field(description="Inclusive Upper Limit for Values", default=None)
    minimum: Optional[float] = Field(description="Inclusive Lower Limit for Values", default=None)
    number: int


class IntegerProperty(BaseProperty):
    datatype: Literal['integer'] = Field(alias="type")
    maximum: Optional[int] = Field(description="Inclusive Upper Limit for Values", default=None)
    minimum: Optional[int] = Field(description="Inclusive Lower Limit for Values", default=None)
    number: int


PropertyUnion = Union[StringProperty, ArrayProperty, BooleanProperty, NumberProperty, IntegerProperty, NullProperty]



class TabularValidationSchema(BaseModel):
    schema_version: str = Field(default="https://json-schema.org/draft/2020-12/schema", alias="schema")
    name: str
    description: str
    properties: Dict[str, PropertyUnion] = Field(default={})
    datatype: str = Field(default="object", alias="type")
    additionalProperties: bool = Field(default=True)
    required: List[str] = Field(description="list of required properties by name", default=[])
    seperator: str = Field(description="Field seperator for the file")
    header: bool = Field(description="Do files of this schema have a header row", default=False)
    examples: Optional[List[Dict[str, str ]]] = Field(default=[])

    # Computed Field implementation for guid generation
    @computed_field(alias="@id")
    def guid(self) -> str:
        return GenerateGUID([int(datetime.datetime.now(datetime.UTC).timestamp())])

        #return GenerateGUID([ int(elem) for elem in
        #	str(int.from_bytes(self.name.encode("utf-8"), byteorder="big"))
        #])


    def load_data(self, dataPath: str) -> pd.DataFrame:
        # TODO deal with alternative filetypes

        # grab file extension with pathlib
        # if pathlib.Path(dataPath).extension() ==".xls":
        # return pd.read_excel()

        # pd.read_excel
        return pd.read_csv(dataPath, sep=self.seperator)
        

    def convert_data_to_json(self, data_frame):
        schema_definition = self.model_dump(
                by_alias=True, 
                exclude_unset=True,
                exclude_none=True
                )

        property_slice = {
                property_name: {
                        "number": property_data.get("number"),
                        "type": property_data.get("type")
                }
                for property_name, property_data in schema_definition.get("properties").items()
        }


        def json_row(row, passed_property_slice):
            json_output = {}
            for property_name, property_values in passed_property_slice.items():

                index_slice = property_values.get("number")
                datatype = property_values.get("type")

                if isinstance(index_slice, int): 

                    if datatype == "boolean":
                        json_output[property_name] = bool(row.iloc[index_slice])
                    else:
                        json_output[property_name] = row.iloc[index_slice]

                elif isinstance(index_slice, str):
                    generated_slice = GenerateSlice(index_slice)

                    # slice rows according to matched slice
                    # if datatype is boolean coerce datatype
                    if datatype=="boolean":
                        json_output[property_name] = [ bool(item) for item in list(row.iloc[generated_slice])]
                    else:
                        json_output[property_name] = list(row.iloc[generated_slice])

            return json_output

        # apply json conversion to each row
        return [ json_row(row_elem, property_slice) for _, row_elem in data_frame.iterrows()]


    def execute_validation(self, data_path: str) -> Dict[int, ValidationError]:
        """ Use the TabularValidationSchema to execute data validation on a given file
        """

        data_frame = self.load_data(data_path)
        
        schema_definition = self.model_dump(
                by_alias=True, 
                exclude_unset=True,
                exclude_none=True
                )


        json_objects = self.convert_data_to_json(data_frame)
        # run conversion on data frame 
        validation_exceptions = {}

        for i, json_elem in enumerate(json_objects):
            try: 
                validate(
                        instance=json_elem,
                        schema= schema_definition 
                )
                print(".", end="")
            except Exception as e:
                # TODO convert property errors into column index
                print("x", end="")
                validation_exceptions[i] = e

        return validation_exceptions	



class PropertyNameException(Exception):

    def __init__(self, propertyName):
        self.propertyName = propertyName
        self.message = f"PropertyNameException: Property with name '{propertyName}' already present in schema"
        super().__init__(self.message)




def AppendProperty(schemaFilepath: str, propertyInstance, propertyName: str) -> None: 
    # check that schemaFile exists
    schemaPath = pathlib.Path(schemaFilepath)

    if not schemaPath.exists():
        raise Exception

    with schemaPath.open("r+") as schemaFile:
        schemaFileContents = schemaFile.read()
        schemaJson =  json.loads(schemaFileContents) 

        # load the model into a 
        schemaModel = TabularValidationSchema(**schemaJson)

        # check for inconsitencies

        # does there exist a property with same name
        if propertyName in [key for key in schemaModel.properties.keys()]:
            raise PropertyNameException(propertyName)

        # does there exist a property with same column number
        schema_indicies = [ val.number for val in schemaModel.properties.values()]

        # check overlap of indicies
        # CheckOverlap


        # add new property to schema
        schemaModel.properties[propertyName] = propertyInstance

        # serialize model to json
        schemaJson = json.dumps(schemaModel.model_dump(by_alias=True) , indent=2)

        # overwrite file contents
        schemaFile.seek(0)
        schemaFile.write(schemaJson)


def ClickAppendProperty(ctx, schemaFile, propertyModel, name): 
    try:
        # append the property to the 
        AppendProperty(schemaFile,  propertyModel, name)
        click.echo(f"Added Property\tname: {name}\ttype: {propertyModel.datatype}")
        ctx.exit(code=0)

    except ColumnIndexException as indexException:
        click.echo("ERROR: ColumnIndexError")
        click.echo(str(indexException))
        ctx.exit(code=1)
    except PropertyNameException as propertyException:
        click.echo("ERROR: PropertyNameError")
        click.echo(str(propertyException))
        ctx.exit(code=1)


def ReadSchema(schema_file: str) -> TabularValidationSchema:
    """ Helper function for reading the schema and marshaling into the pydantic model
    """
    # read the schema
    with open(schema_file, "r") as input_schema:
        input_schema_data = input_schema.read()
        schema_json =  json.loads(input_schema_data) 

        # load the model into 
        return TabularValidationSchema(**schema_json)


def WriteSchema(tabular_schema: TabularValidationSchema, schema_file):
    """ Helper Function for writing files
    """

    schema_dictionary = tabular_schema.model_dump(by_alias=True) 
    schema_json = json.dumps(schema_dictionary, indent=2)

    # dump json to a file
    with open(schema_file, "w") as output_file:
        output_file.write(schema_json)


def InstantiateStringModel(ctx, name, number, description, value_url, pattern):
    try:
        modelInstance = StringProperty(
            datatype = 'string',
            number = number,
            description = description,
            valueURL = value_url,
            pattern = pattern
        )
        return modelInstance

    except ValidationError as metadataError:
        ctx.echo("ERROR: MetadataValidationError")
        ctx.echo(metadataError)
        #for validationFailure in metadataError.errors():
        #    click.echo(f"loc: {validationFailure.loc}\tinput: {validationFailure.input}\tmsg: {validationFailure.msg}")
        ctx.exit(code=1)


def InstantiateNumberModel(ctx, name, number, description, value_url):
    try:
        modelInstance = NumberProperty(
            datatype = 'number',
            number = number,
            description = description,
            valueURL = value_url
            )
        return modelInstance

    except ValidationError as metadataError:
        click.echo("ERROR: MetadataValidationError")
        click.echo(metadataError)
        #for validationFailure in metadataError.errors():
        #    click.echo(f"loc: {validationFailure.loc}\tinput: {validationFailure.input}\tmsg: {validationFailure.msg}")
        ctx.exit(code=1)


def InstantiateBooleanModel(ctx, name, number, description, value_url):
    try:
        booleanInstance = BooleanProperty(
            datatype = 'boolean',
            number = number,
            description = description,
            valueURL = value_url,
            )
        return booleanInstance

    except ValidationError as metadataError:
        click.echo("ERROR: MetadataValidationError")
        click.echo(metadataError)
        #for validationFailure in metadataError.errors():
        #    click.echo(f"loc: {validationFailure.loc}\tinput: {validationFailure.input}\tmsg: {validationFailure.msg}")
        ctx.exit(code=1)


def InstantiateIntegerModel(ctx, name, number, description, value_url):
    try:
        integerInstance = IntegerProperty(
            datatype = 'integer',
            number = number,
            description = description,
            valueURL = value_url,
        )
        return integerInstance

    except ValidationError as metadataError:
        click.echo("ERROR: MetadataValidationError")
        click.echo(metadataError)
        #for validationFailure in metadataError.errors():
        #    click.echo(f"loc: {validationFailure.loc}\tinput: {validationFailure.input}\tmsg: {validationFailure.msg}")
        ctx.exit(code=1)


def InstantiateArrayModel(ctx, name, number, description, value_url, items_datatype, min_items, max_items, unique_items):
    try:
        datatype_enum = DatatypeEnum(items_datatype)
    except Exception:
        click.echo(f"ITEMS Datatype {itemsDatatype} invalid\n" +
            "ITEMS must be oneOf 'boolean'|'object'|'string'|'number'|'integer'" 
        )
        ctx.exit(code=1)
    try:
        modelInstance = ArrayProperty(
            datatype = 'array',
            number = number,
            description = description,
            valueURL = value_url,
            maxItems = max_items,
            minItems = min_items,
            uniqueItems = unique_items,
            items = Items(datatype=datatype_enum)
            )
        return modelInstance

    except ValidationError as metadataError:
        click.echo("ERROR: MetadataValidationError")
        click.echo(metadataError)
        #for validationFailure in metadataError.errors():
        #    click.echo(f"loc: {validationFailure.loc}\tinput: {validationFailure.input}\tmsg: {validationFailure.msg}")
        ctx.exit(code=1)


def ValidateModel(ctx, createModel):
    try:
        modelInstance = createModel()
        return modelInstance

    except ValidationError as metadataError:
        click.echo("ERROR: MetadataValidationError")
        click.echo(metadataError)
        #for validationFailure in metadataError.errors():
        #    click.echo(f"loc: {validationFailure.loc}\tinput: {validationFailure.input}\tmsg: {validationFailure.msg}")
        ctx.exit(code=1)

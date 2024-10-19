import jsonschema
import pathlib
from functools import lru_cache
import os
import json
import pyarrow.parquet as pq
import pyarrow.compute as pc

from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    Field,
    ValidationError,
    model_validator
)
from typing import (
    Dict, 
    List, 
    Optional,
    Union,
    Literal
)

from fairscape_cli.models.schema.utils import (
    GenerateSlice,
    PropertyNameException,
    ColumnIndexException,
    map_arrow_type_to_json_schema
)

from fairscape_cli.models.utils import (
    GenerateDatetimeSquid
)

from fairscape_cli.config import (
    DEFAULT_CONTEXT,
    DEFAULT_SCHEMA_TYPE,
    NAAN,
)

import datetime
from enum import Enum
import re


# datatype enum
class DatatypeEnum(str, Enum):
    NULL = "null"
    BOOLEAN = "boolean"
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
    index: Union[int,str] = Field(description="index of the column for this value")
    valueURL: Optional[str] = Field(default=None)	


class NullProperty(BaseProperty):
    datatype: Literal['null'] = Field(alias="type", default='null')
    index: int


class StringProperty(BaseProperty):
    datatype: Literal['string'] = Field(alias="type")
    pattern: Optional[str] = Field(description="Regex pattern to execute against values", default=None)
    maxLength: Optional[int] = Field(description="Inclusive maximum length for string values", default=None)
    minLength: Optional[int] = Field(description="Inclusive minimum length for string values", default=None)
    index: int


class ArrayProperty(BaseProperty):
    datatype: Literal['array'] = Field(alias="type")
    maxItems: Optional[int] = Field(description="max items in array, validation fails if length is greater than this value", default=None)
    minItems: Optional[int] = Field(description="min items in array, validation fails if lenght is shorter than this value", default=None)
    uniqueItems: Optional[bool] = Field()
    index: str
    items: Items


class BooleanProperty(BaseProperty):
    datatype: Literal['boolean'] = Field(alias="type")
    index: int


class NumberProperty(BaseProperty):
    datatype: Literal['number'] = Field(alias="type")
    maximum: Optional[float] = Field(description="Inclusive Upper Limit for Values", default=None)
    minimum: Optional[float] = Field(description="Inclusive Lower Limit for Values", default=None)
    index: int

    @model_validator(mode='after')
    def check_max_min(self) -> 'IntegerProperty':
        minimum = self.minimum
        maximum = self.maximum

        if maximum is not None and minimum is not None:

            if maximum == minimum:
                raise ValueError('IntegerProperty attribute minimum != maximum')
            elif maximum < minimum:
                raise ValueError('IntegerProperty attribute maximum !< minimum')
        return self


class IntegerProperty(BaseProperty):
    datatype: Literal['integer'] = Field(alias="type")
    maximum: Optional[int] = Field(description="Inclusive Upper Limit for Values", default=None)
    minimum: Optional[int] = Field(description="Inclusive Lower Limit for Values", default=None)
    index: int

    @model_validator(mode='after')
    def check_max_min(self) -> 'IntegerProperty':
        minimum = self.minimum
        maximum = self.maximum

        if maximum is not None and minimum is not None:

            if maximum == minimum:
                raise ValueError('IntegerProperty attribute minimum != maximum')
            elif maximum < minimum:
                raise ValueError('IntegerProperty attribute maximum !< minimum')
        return self



PropertyUnion = Union[StringProperty, ArrayProperty, BooleanProperty, NumberProperty, IntegerProperty, NullProperty]



class TabularValidationSchema(BaseModel):
    guid: Optional[str] = Field(alias="@id", default=None)
    context: Optional[Dict] = Field(default=DEFAULT_CONTEXT, alias="@context")
    metadataType: Optional[str] = Field(default=DEFAULT_SCHEMA_TYPE, alias="@type")
    schema_version: str = Field(default="https://json-schema.org/draft/2020-12/schema", alias="schema")
    name: str
    description: str
    properties: Dict[str, PropertyUnion] = Field(default={})
    datatype: str = Field(default="object", alias="type")
    additionalProperties: bool = Field(default=True)
    required: List[str] = Field(description="list of required properties by name", default=[])
    separator: str = Field(description="Field seperator for the file")
    header: bool = Field(description="Do files of this schema have a header row", default=False)
    examples: Optional[List[Dict[str, str ]]] = Field(default=[])

    # Computed Field implementation for guid generation
    def generate_guid(self) -> str:
        """ Generate an ARK for the Schema
        """
        # if guid is already set
        if self.guid is None:
            prefix=f"schema-{self.name.lower().replace(' ', '-')}"
            sq = GenerateDatetimeSquid()
            self.guid = f"ark:{NAAN}/{prefix}-{sq}"
        return self.guid


    def load_data(self, dataPath: str) -> List[List[str]]:
        """ Load data from a given path and return a list of rows split by the seperator character
        """
        # wrong data for example
        rows = []
        sep = self.separator
        with open(dataPath, "r") as data_file:
            data_row = data_file.readline()

            # if the file has a header move on to the next row
            if self.header:
                data_row = data_file.readline()

            # iterate through the file slicing each row into 
            while data_row != "": 
                data_line = data_row.replace(",,", ", ,").replace("\n", "").split(sep)
                rows.append(data_line)
                data_row = data_file.readline()

        return rows


    def convert_json(self, dataPath: str):
        """ Given a path to a Tabular File, load in the data and generate a list of JSON equivalent data structures 
        """

        data_rows = self.load_data(dataPath)

        row_lengths = set([len(row) for row in data_rows])
        if len(row_lengths) == 1: 
            default_row_length = list(row_lengths)[0]
        else:
            # TODO set to most common row_length
            default_row_length = list(row_lengths)[0]
            #raise Exception


        schema_definition = self.model_dump(
                by_alias=True, 
                exclude_unset=True,
                exclude_none=True
                )

        # reorganize property data for forming json
        properties_simplified = [
                { 
                    "name": property_name, 
                    "index": property_data.get("index"),                                                                                                                   
                    "type": property_data.get("type"),
                    "items": property_data.get("items", {}).get("type"),
                    "index_slice": None,
                    "access_function": None
                }                                                                                  
                for property_name, property_data in schema_definition.get("properties").items()
        ] 


        # index slice is going to change on each iteration, as a local variable this causes
        # problems for all of the 
        updated_properties = []
        for prop in properties_simplified:
            
            index_slice = prop.get("index")
            datatype = prop.get("type")
            item_datatype = prop.get('items')
 
            prop['index_slice'] = index_slice


            if datatype == 'array':
                generated_slice = GenerateSlice(index_slice, default_row_length)
                prop['index_slice'] = generated_slice
                
                if item_datatype ==" boolean":
                    prop['access_function'] = lambda row, passed_slice: [ bool(item) for item in list(row[passed_slice])]

                if item_datatype == "integer":
                    prop['access_function'] = lambda row, passed_slice: [ int(item) for item in list(row[passed_slice])]
                    
                if item_datatype == "number":
                    prop['access_function'] = lambda row, passed_slice: [ float(item) for item in row[passed_slice]]

                if item_datatype == "string":
                    prop['access_function'] = lambda row, passed_slice: [ str(item) for item in list(row[passed_slice])]

            if datatype == "boolean":
                prop['access_function'] = lambda row, passed_slice: bool(row[passed_slice])
                
            if datatype == "integer":
                prop['access_function'] =  lambda row, passed_slice: int(row[passed_slice])
                    
            if datatype == "number":
                prop['access_function'] = lambda row, passed_slice: float(row[passed_slice])
                
            if datatype == "string":
                prop['access_function'] = lambda row, passed_slice: str(row[passed_slice])

            if datatype == "null":
                prop['access_function'] = lambda row, passed_slice: None

            updated_properties.append(prop)

            
        # coerce types and generate lists 
        json_output = []
        parsing_failures = []

        for i, row in enumerate(data_rows):
            json_row = {}
            row_error = False

            for json_attribute in updated_properties: 
                attribute_name = json_attribute.get("name")
                access_func = json_attribute.get("access_function")
                attribute_slice = json_attribute.get("index_slice")
                try:
                    json_row[attribute_name] = access_func(row, attribute_slice)

                except ValueError as e:
                    parsing_failures.append({ 
                        "message": f"ValueError: Failed to Parse Attribute {attribute_name} for Row {i}", 
                        "type": "ParsingError",
                        "row": i,
                        "exception": e
                        })
                    row_error = True

                except IndexError as e:
                    parsing_failures.append({ 
                        "message": f"IndexError: Failed to Parse Attribute {attribute_name} for Row {i}", 
                        "type": "ParsingError",
                        "row": i,
                        "exception": e
                        })
                    row_error = True

                except Exception as e: 
                    parsing_failures.append({ 
                        "message": f"Error: Failed to Parse Attribute {attribute_name} for Row {i}", 
                        "type": "ParsingError",
                        "row": i,
                        "exception": e
                        })
                    row_error = True

            # if there was an error parsing a row
            if row_error:
                pass
            else:
                json_output.append(json_row)

        return json_output, parsing_failures


    def execute_validation(self, dataPath):
        ''' Given a path to a tabular data file, execute the schema against the 
        '''

        schema_definition = self.model_dump(
                by_alias=True, 
                exclude_unset=True,
                exclude_none=True
                )

        json_objects, parsing_failures = self.convert_json(dataPath)


        output_exceptions = parsing_failures
        
        validator = jsonschema.Draft202012Validator(schema_definition)
        for i, json_elem in enumerate(json_objects):
            errors = sorted(validator.iter_errors(json_elem), key=lambda e: e.path)

            if len(errors) == 0:
                pass
            else:
                for err in errors: 
                    output_exceptions.append({
                        "message": err.message, 
                        "row": i,
                        "type": "ValidationError",
                        #"exception": e ,
                        "failed_keyword": err.validator,
                        "schema_path": err.schema_path
                    })

        return output_exceptions
    
    @classmethod
    def infer_from_parquet(cls, name: str, description: str, guid: Optional[str], parquet_file: str, include_min_max: bool = False) -> 'TabularValidationSchema':
        try:
            table = pq.read_table(parquet_file)
            schema = table.schema

            properties = {}
            for i, field in enumerate(schema):
                field_name = field.name
                field_type = map_arrow_type_to_json_schema(field.type)
                
                if field_type == 'string':
                    properties[field_name] = StringProperty(
                        datatype='string',
                        description=f"Column {field_name}",
                        index=i
                    )
                elif field_type in ['integer', 'number']:
                    if include_min_max:
                        column = table.column(field_name)
                        min_max = pc.min_max(column)
                        min_value = min_max['min'].as_py()
                        max_value = min_max['max'].as_py()
                        
                        if field_type == 'integer':
                            properties[field_name] = IntegerProperty(
                                datatype='integer',
                                description=f"Column {field_name}",
                                index=i,
                                minimum=min_value,
                                maximum=max_value
                            )
                        else:
                            properties[field_name] = NumberProperty(
                                datatype='number',
                                description=f"Column {field_name}",
                                index=i,
                                minimum=min_value,
                                maximum=max_value
                            )
                    else:
                        if field_type == 'integer':
                            properties[field_name] = IntegerProperty(
                                datatype='integer',
                                description=f"Column {field_name}",
                                index=i
                            )
                        else:
                            properties[field_name] = NumberProperty(
                                datatype='number',
                                description=f"Column {field_name}",
                                index=i
                            )
                elif field_type == 'boolean':
                    properties[field_name] = BooleanProperty(
                        datatype='boolean',
                        description=f"Column {field_name}",
                        index=i
                    )
                elif field_type == 'array':
                    item_type = map_arrow_type_to_json_schema(field.type.value_type)
                    properties[field_name] = ArrayProperty(
                        datatype='array',
                        description=f"Column {field_name}",
                        index=str(i),
                        items=Items(datatype=DatatypeEnum(item_type))
                    )

            return cls(
                name=name,
                description=description,
                guid=guid,
                properties=properties,
                required=list(properties.keys()),
                separator=",",  
                header=True  
            )
        except Exception as e:
            raise ValueError(f"Error inferring schema: {str(e)}")


def AppendProperty(schemaFilepath: str, propertyInstance, propertyName: str) -> None: 
    # check that schemaFile exists
    schemaPath = pathlib.Path(schemaFilepath)

    if not schemaPath.exists():
        raise Exception

    with schemaPath.open("r+") as schemaFile:
        schemaFileContents = schemaFile.read()
        schemaJson =  json.loads(schemaFileContents) 

        # load the model into a tabular validation schema
        schemaModel = TabularValidationSchema.model_validate(schemaJson)

        # TODO check for inconsitencies

        # does there exist a property with same name
        if propertyName in [key for key in schemaModel.properties.keys()]:
            raise PropertyNameException(propertyName)

        # does there exist a property with same column number
        schema_indicies = [ val.index for val in schemaModel.properties.values()]

        # check overlap of indicies
        # CheckOverlap


        # add new property to schema
        schemaModel.properties[propertyName] = propertyInstance

        # add new property as required
        schemaModel.required.append(propertyName)

        # serialize model to json
        schemaJson = json.dumps(schemaModel.model_dump(by_alias=True) , indent=2)

        # overwrite file contents
        schemaFile.seek(0)
        schemaFile.write(schemaJson)


def ClickAppendProperty(ctx, schemaFile, propertyModel, name): 
    try:
        # append the property to the 
        AppendProperty(schemaFile,  propertyModel, name)
        print(f"Added Property\tname: {name}\ttype: {propertyModel.datatype}")
        ctx.exit(code=0)

    except ColumnIndexException as indexException:
        print("ERROR: ColumnIndexError")
        print(str(indexException))
        ctx.exit(code=1)
    except PropertyNameException as propertyException:
        print("ERROR: PropertyNameError")
        print(str(propertyException))
        ctx.exit(code=1)


def ReadSchemaGithub(schemaURI: str) -> TabularValidationSchema:
    pass

def ReadSchemaFairscape(schemaArk: str) -> TabularValidationSchema:
    pass



def ReadSchemaLocal(schemaFile: str) -> TabularValidationSchema:
    """ Helper function for reading the schema and marshaling into the pydantic model
    """
    schemaPath = pathlib.Path(schemaFile)

    # read the schema
    with schemaPath.open("r") as inputSchema:
        inputSchemaData = inputSchema.read()
        schemaJson =  json.loads(inputSchemaData) 

    # load the model into 
    tabularSchema = TabularValidationSchema.model_validate(schemaJson)
    return tabularSchema


def ReadSchema(schemaFile:str) -> TabularValidationSchema:
    ''' Read a schema specified by the argument schemaFile

    The schemaFile parameter can be a url to a rawgithub link, or an ark identifier.
    If the ark identifier is in the supplied, default schemas provided in the fairscape cli pacakges will be searched.
    If there is no match then 
    '''

    if 'raw.githubusercontent' in schemaFile:
        schemaInstance = ReadSchemaGithub(schemaFile)
        return schemaInstance


    elif 'ark' in schemaFile:
        defaultSchemas = ImportDefaultSchemas()
        matchingSchemas = list(filter(lambda schema: schema.guid == str(schemaFile), defaultSchemas))

        if len(matchingSchemas) == 0:
            # request against fairscape
            schemaInstance = ReadSchemaFairscape(schemaFile)
            return schemaInstance
        else:
            defaultSchema = matchingSchemas[0]
            return defaultSchema

    else: 
        # schema must be a path that exists
        schemaInstance = ReadSchemaLocal(schemaFile)
        return schemaInstance



def WriteSchema(tabular_schema: TabularValidationSchema, schema_file):
    """ Helper Function for writing files
    """

    schema_dictionary = tabular_schema.model_dump(by_alias=True) 
    schema_json = json.dumps(schema_dictionary, indent=2)

    # dump json to a file
    with open(schema_file, "w") as output_file:
        output_file.write(schema_json)



@lru_cache
def ImportDefaultSchemas()-> List[TabularValidationSchema]:
	defaultSchemaLocation = pathlib.Path(os.path.dirname(os.path.realpath(__file__))) / 'default_schemas'
	schemaPaths = list(defaultSchemaLocation.rglob("*/*.json"))

	defaultSchemaList = []
	for schemaPathElem in schemaPaths:

		with schemaPathElem.open("r") as inputSchema:
			inputSchemaData = inputSchema.read()
			schemaJson =  json.loads(inputSchemaData) 

		try:		
			schemaElem = TabularValidationSchema.model_validate(schemaJson)
			defaultSchemaList.append(schemaElem)
		except:
			# TODO handle validation failures from default schemas
			pass
	
	return defaultSchemaList

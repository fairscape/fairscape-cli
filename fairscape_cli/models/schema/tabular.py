from jsonschema import validate
import pandas as pd
import datetime
import pathlib
import json

from pydantic import (
	BaseModel,
	ConfigDict,
	computed_field,
	Field
)
from typing import (
	Dict, 
	List, 
	Optional,
	Union,
	Literal
)


from enum import Enum
import re

# TODO reorganize for imports
#  Python Interface for Registering Unique GUIDS
from sqids import Sqids
squids = Sqids(min_length=6, )

# TODO set to configuration
NAAN = "59852"

def GenerateGUID(data: List[int]) -> str:
    squid_encoded = squids.encode(data)
    return f"ark:{NAAN}/{squid_encoded}"


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
	number: Union[int,str] = Field(description="index of the column for this value")
	valueURL: Optional[str] = Field(default=None)	
	#multiple: Optional[bool]
	#seperator: Optional[str]

class NullProperty(BaseProperty):
	datatype: Literal['null'] = Field(alias="type")

class StringProperty(BaseProperty):
	datatype: Literal['string'] = Field(alias="type")
	pattern: Optional[str] = Field(description="regex pattern for field", default=None)
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
	number: int

class IntegerProperty(BaseProperty):
	datatype: Literal['integer'] = Field(alias="type")
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
		return pd.read_csv(dataPath, sep=self.seperator,  header=self.header)


	def execute_validation(self, data_frame):
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


		def json_row(row):
			json_output = {}
			for property_name, property_values in property_slice.items():
			
				index_slice = property_values.get("number")
				datatype = property_values.get("type")

				if isinstance(index_slice, int): 

					if datatype == "boolean":
						json_output[property_name] = bool(row.iloc[index_slice])
					else:
						json_output[property_name] = row.iloc[index_slice]
				
				elif isinstance(index_slice, str):

					n_to_end_slice_match = re.search("^([0-9]*)::$", index_slice)
					start_to_n_slice_match = re.search("^::([0-9]*)$", index_slice)
					n_to_m_slice_match = re.search("^([0-9]*):([0-9]*)$", index_slice)

					if n_to_end_slice_match:
						start = int(n_to_end_slice_match.group(1))
						generated_slice = slice(start, len(row))
					elif start_to_n_slice_match:
						end = int(start_to_n_slice_match.group(1))
						generated_slice = slice(0,end)
					elif n_to_m_slice_match:
						start = int(n_to_m_slice_match.group(1))
						end = int(n_to_m_slice_match.group(2))
						generated_slice = slice(start, end)
					else:
						# raise exception for improperly passing a slice 
						raise Exception()

					# slice rows according to matched slice

					# if datatype is boolean coerce datatype
					if datatype=="boolean":
						json_output[property_name] = [ bool(item) for item in list(row.iloc[generated_slice])]
					else:
						json_output[property_name] = list(row.iloc[generated_slice])

			return json_output

		# run conversion on data frame 
		validation_exceptions = {}

		json_list = [ {} for i in range(data_frame.shape[0])]

		for i in range(data_frame.shape[0]):
			data_row = data_frame.iloc[i,:]

			# catch all validation errors and then return
			try: 
				validate(
					instance=json_row(data_row),
					schema= schema_definition 
				)
			except Exception as e:
				# TODO convert property errors into column index
				validation_exceptions[i] = e

		return validation_exceptions	



def AddProperty(schemaFilepath: str, metadata: dict, propertyClass) -> None:
    
    # check that schemaFile exists
    schemaPath = pathlib.Path(schemaFilepath)

    if not schemaPath.exists():
        raise Exception

    # unmarshal metadata into propertyClass
    modelInstance = propertyClass(**metadata)

    # open schemafile
    with schemaPath.open("r+") as schemaFile:
        schemaFileContents = schemaFile.read()
        schemaJson =  json.loads(schemaFileContents) 

        # load the model into a 
        schemaModel = TabularValidationSchema(**schemaJson)

        # check for inconsitencies
        
        # does there exist a property with same name
        propertyName = metadata.get("name")
        if propertyName in [key for key in schemaModel.properties.keys()]:
            # TODO raise more descriptive exception
            raise Exception

        # does there exist a property with same column number
        if modelInstance.number in [ val.number for val in schemaModel.properties.values()]:
            # TODO raise more descriptive exception
            raise Exception

        # add new property to schema
        schemaModel.properties[propertyName] = modelInstance
  
        # serialize model to json
        schemaJson = json.dumps(schemaModel.model_dump(by_alias=True) , indent=2)

        # overwrite file contents
        schemaFile.seek(0)
        schemaFile.write(schemaJson)

        return None


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

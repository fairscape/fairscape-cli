from jsonschema import validate
import pandas as pd

from pydantic import (
	BaseModel,
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
	datatype: DatatypeEnum = Field(alias="type")

class BaseProperty(BaseModel):
	description: str = Field(description="description of field")
	number: Union[int,str] = Field(description="index of the column for this value")
	valueURL: Optional[str] = Field(default=None)	
	#multiple: Optional[bool]
	#seperator: Optional[str]

class NullProperty(BaseModel):
	datatype: Literal['null'] = Field(alias="type")

class StringProperty(BaseProperty):
	datatype: Literal['string'] = Field(alias="type")
	pattern: Optional[str] = Field(description="regex pattern for field", default=None)

class ArrayProperty(BaseProperty):
	datatype: Literal['array'] = Field(alias="type")
	maxItems: int = Field(description="max items in array, validation fails if length is greater than this value")
	minItems: Optional[int] = Field(description="min items in array, validation fails if lenght is shorter than this value")
	uniqueItems: Optional[bool] = Field()
	items: Items

class BooleanProperty(BaseProperty):
	datatype: Literal['boolean'] = Field(alias="type")

class NumberProperty(BaseProperty):
	datatype: Literal['number'] = Field(alias="type")

class IntegerProperty(BaseProperty):
	datatype: Literal['integer'] = Field(alias="type")


PropertyUnion = Union[StringProperty, ArrayProperty, BooleanProperty, NumberProperty, IntegerProperty, NullProperty]


class ValidationSchema(BaseModel):
	schema_version: str = Field(default="https://json-schema.org/draft/2020-12/schema", alias="schema")
	name: str
	description: str
	guid: str = Field(alias="@id")
	properties: Dict[str, PropertyUnion]
	datatype: str = Field(default="object", alias="type")
	additionalProperties: bool = Field()
	required: List[str] = Field(description="list of required properties by name")
	seperator: str = Field(description="Field seperator for the file")
	header: bool = Field(description="Do files of this schema have a header row")
	examples: Optional[List[Dict[str, str ]]]

	def load_data(self, path: str) -> pd.DataFrame:
		# TODO deal with alternative filetypes

		# pd.read_excel
		return pd.read_csv(path, sep=self.seperator,  header=self.header)

	def execute_validation(self, data_frame):
		schema_definition = self.model_dump(by_alias=True)

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
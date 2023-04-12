import pydantic
from typing import (
	Optional,
	List,
	Union
)

class ColumnSchema(pydantic.BaseModel):
	"""

	name
	url: url about the value for this column	
	cells: list of cells in the column, a Column MUST contain one cell from each row in the table
	datatype: the expected datatype for the value of cells in this column
	default: default value for cells whose string value is an empty string
	null: the string or strings which cause the value of a cell to have a value to be null
	ordered: are the 
	number: the position of the column amoungst the columns for the associated table
	propertyURL: creates a URL identifier for the property of each cell value in this column relative to the row it is contained
	required: boolean for if this value is required
	seperator: seperator character for tabular data
	table: the table in which this column schema is used
	titles: any number of human readable titles for the column
	valueURL: identifier url for the value datatype in the table

	"""
	name: str
	metadataType: str = "ColumnSchema"
	aboutURL: Optional[str]
	cells: list
	datatype: str
	default: str
	null: str
	ordered: bool
	number: int
	propertyURL: str
	valueURL: str
	required: bool
	table: list[str]
	titles: list[str]


class DatatypeSchema(pydantic.BaseModel):
	name: str
	

class RowSchema(pydantic.BaseModel):
	name: str

class TabularDataSchema(pydantic.BaseModel):
	guid: str
	context: dict
	metadataType: str = "TabularDataSchema"
	name: str
	columns: List[ColumnSchema]
	tableDirection: str
	foreignKeys: list
	description: str
	rows: List[RowSchema]
	schemaUrl: str

	
	def validate(self, data_path):
		pass
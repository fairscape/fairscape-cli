import pydantic
import pathlib
from enum import Enum
from typing import (
    Optional,
    List,
    Union
)
import pandas as pd


class FiletypeEnum(str, Enum):
    """List of supported filetypes with normative naming
    """
    csv = "csv"
    tsv = "tsv"
    hcx = "hcx"
    

class DatatypeEnum(str, Enum):
    """
    A Datatype Enum for supported types for validation

    These Choices are to be expanded until covering the full spec from [CSV on the Web](https://w3c.github.io/csvw/metadata/#datatypes)
    These datatypes are defined in [XMLSchema](http://www.w3.org/2001/XMLSchema#) as anyAtomicType

    For validation implementation the following datatypes are specified
    - number with identifier http://www.w3.org/2001/XMLSchema#double
    - binary with identifier http://www.w3.org/2001/XMLSchema#base64Binary
    - datetime with identifier http://www.w3.org/2001/XMLSchema#dateTime
    - any with identifier http://www.w3.org/2001/XMLSchema#anyAtomicType
    - xml a subtype of string  http://www.w3.org/1999/02/22-rdf-syntax-ns#XMLLiteral
    - html a subtype of string  http://www.w3.org/1999/02/22-rdf-syntax-ns#HTML
    - json a subtype of string http://www.w3.org/ns/csvw#JSON

    """
    string = 'string'
    integer = 'integer'
    float = 'float'
    datetime = 'datetime'
    binary = 'binary'
    any = 'any'
    xml = 'xml'
    json = 'json'
    html = 'html'


class DatatypeSchema(pydantic.BaseModel):
    """
    A Schema for Datatypes which allows restricting format or value ranges

    The full specification for

    Attributes
    ----------
    name: str
            (dc:title) title of the datatype
    description: str
            (dc:title) description for the
    base: DatatypeEnum
            (csvw:base) the base datatype of this datatype i.e. str, float, int
    format: str
            (csvw:format) the restriction on the base datatype
    """
    name: Optional[str]
    metadataType: str = "csvw:Datatype"
    description: Optional[str]
    base: DatatypeEnum
    format: Optional[str]
    length: Optional[int]
    minLength: Optional[int]
    maxLength: Optional[int]
    min: Optional[Union[int, float]]
    maximum: Optional[Union[int, float]]


class ColumnSchema(pydantic.BaseModel):
    """
    A Schema for Columns on Tabular Data

    Attributes
    ---------
    name: str
            (dc:title) Name for this Column Schema
    url: str
            (dc:url) url about the value for this column
    cells: list
            list of cells in the column, a Column MUST contain one cell from each row in the table

    datatype:
        the expected datatype for the value of cells in this column

    default:
        default value for cells whose string value is an empty string

    null:
        the string or strings that represent a null or na value

    ordered:
        are the rows of this column schema ordered
        ordering is available for numeric and datetime datatypes

    number:
        the position of the column amoungst the columns for the associated table

    propertyURL:
        creates a URL identifier for the property of each cell value in this column relative to the row it is contained

    required:
        boolean for if this value is required

    seperator:
        seperator character for tabular data

    table:
        the table in which this column schema is used

    titles:
        any number of human readable titles for the column

    valueURL:
        identifier url for the value datatype in the table

    """
    name: str
    metadataType: str = "ColumnSchema"
    aboutURL: Optional[str]
    description: str
    cells: Optional[list]
    datatype: Union[DatatypeEnum, DatatypeSchema]
    default: Optional[str]
    null: Optional[str]
    ordered: Optional[bool]
    number: Union[int, str, List[int]]
    valueURL: Optional[str]
    required: bool
    table: Optional[list[str]]
    titles: list[str]

    def validate_column(self, data) -> bool:

        pass

        # if required check for no missing values
        #if self.required:

        #    if data == np.nan:
        #        return False

        # check that string value is not


class RowSchema(pydantic.BaseModel):
    name: str


class TabularDataSchema(pydantic.BaseModel):
    """
    Schema for Tabular data validation.

    Each schema recieves a GUID which supports reuse across RO-crates.

    Attributes
    ---------

    guid: str
        the local identifier for a class instance of a tabular schema

    context: Optional[dict]
        the json-ld context for this tabular schema
        aliased to @context on serialization to json

    metadataType: str = "TabularDataSchema"
        the json-ld @type value, aliased to @type on serialization to json

    url: str
        url for resolvable metadata about this schema

    schemaUrl: str
        url to resolve the instance of this schema

    name: str
        name of this tabular data schema

    description: str
        a writted description of this tabular data schema and its purpose, including the data it will be used to validated


    columns: List[ColumnSchema]
        a list of columns to be validated, each with thier own validation logic.
        if the columns attribute do not cover all columns of input data
        only specified rules will be run but a warning returned

    delimiter: str = ','
        the file delimiter for seperating values within rows

    doubleQuote: bool
        a boolean indicating whether values are to be double quoted.
        if true double quotes around a feild signify a single value

    lineTerminator: str = '\r\n'
        the characters indicating the end of a line in the file

    skipInitialSpace: bool = True
        determines how to handle whitespace
        if false whitespace preceeding or following a field is included as part of the fields value

    header: bool
        header is true if the first line of the file contains column titles

    foreignKeys: Optional[list]
         a list of Column References in other tables

        e.g.
        ```
        {
            "foreignKeys": [
            {
                "columnReference": "country_group",
                "reference": {
                    "resource": "country-groups.csv",
                    "columnReference": "group"
                }
            }
        ]
    }
    ```

    """
    guid: str
    context: Optional[dict]
    metadataType: str = "TabularDataSchema"
    url: Optional[str]
    schemaUrl: Optional[str]
    name: str
    description: str
    columns: List[ColumnSchema]
    delimiter: str = ","
    doubleQuote: bool = False
    lineTerminator: str = "\n"
    skipInitialSpace: bool = False
    header: bool = True
    foreignKeys: Optional[list]

    def ReadTabularData(self, DataPath: pathlib.Path) -> pd.DataFrame:
      ''' Given a path to a file construct a pandas read method to read the data
      '''

      readCsvKwargs = {
           "sep": self.delimiter,
            "lineterminator": self.lineTerminator,
            "skipinitialspace": self.skipInitialSpace
           }
      if self.header == True:
        readCsvKwargs['header'] = 0
      else:
        readCsvKwargs['header'] = None

      if self.doubleQuote == True:
        # set pd.read_csv argument quoting to QUOTE_ALL(1)
        readCsvKwargs['quoting'] = 1
  
      # TODO can specify datatype of columns
      # dtype = {}

      tabularData = pd.read_csv(
        DataPath,
        **readCsvKwargs
      )

      return tabularData


class DataValidationException(Exception):

    def __init__(self, error, message="DataValidationException: Validation Failed"):
        self.error = error
        self.message = message
        super().__init__(self.message)


class NAValidationException(DataValidationException):

    def __init__(self, error, message="DataValidationException: NA Values in required column"):
        self.error = error
        self.message = message
        super().__init__(self.message)

class DatatypeValidationException(DataValidationException):

    def __init__(self, error, message):
        self.error = error
        self.message = message
        super().__init__(self.message)


class PathNotFoundException(DataValidationException):

    def __init__(self, message="PathNotFound", path: pathlib.Path = None):
        self.path = path
        if self.path is not None:
            self.message = f"PathNotFound: {str(self.path)}"
        else:
            self.message = message
        super().__init__(self.message)


class TabularDataValidation():
    ''' A class for running the execution of data validation as determined by a TabularDataSchema
    '''

    def __init__(
        TabularSchema: TabularDataSchema,
        TabularDataPath: pathlib.Path
    ):

        self.TabularDataPath = TabularDataPath
        self.TabularSchema = TabularSchema

    def validate(self):
        ''' Execute the validation logic specified by the schema on the specified file
        '''

        pass
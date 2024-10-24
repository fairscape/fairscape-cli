import jsonschema
import pathlib
from functools import lru_cache
import os
import json
import pandas as pd
import pyarrow.parquet as pq
import pyarrow.compute as pc
import h5py
from enum import Enum
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
    Literal,
    Type
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

class FileType(str, Enum):
    CSV = "csv"
    TSV = "tsv"
    PARQUET = "parquet"
    HDF5 = "h5"
    
    @classmethod
    def from_extension(cls, filepath: str) -> 'FileType':
        ext = pathlib.Path(filepath).suffix.lower()[1:]  # Remove the dot
        if ext == 'h5' or ext == 'hdf5':
            return cls.HDF5
        elif ext == 'parquet':
            return cls.PARQUET
        elif ext == 'tsv':
            return cls.TSV
        elif ext == 'csv':
            return cls.CSV
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

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
    def check_max_min(self) -> 'NumberProperty':
        minimum = self.minimum
        maximum = self.maximum

        if maximum is not None and minimum is not None:
            if maximum == minimum:
                raise ValueError('NumberProperty attribute minimum != maximum')
            elif maximum < minimum:
                raise ValueError('NumberProperty attribute maximum !< minimum')
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

class BaseSchema(BaseModel):
    guid: Optional[str] = Field(alias="@id", default=None)
    context: Optional[Dict] = Field(default=DEFAULT_CONTEXT, alias="@context")
    metadataType: Optional[str] = Field(default=DEFAULT_SCHEMA_TYPE, alias="@type")
    schema_version: str = Field(default="https://json-schema.org/draft/2020-12/schema", alias="schema")
    name: str
    description: str
    datatype: str = Field(default="object", alias="type")
    additionalProperties: bool = Field(default=True)
    required: List[str] = Field(description="list of required properties by name", default=[])
    examples: Optional[List[Dict[str, str]]] = Field(default=[])

    def generate_guid(self) -> str:
        if self.guid is None:
            prefix = f"schema-{self.name.lower().replace(' ', '-')}"
            sq = GenerateDatetimeSquid()
            self.guid = f"ark:{NAAN}/{prefix}-{sq}"
        return self.guid
    
    @model_validator(mode='after')
    def generate_all_guids(self) -> 'BaseSchema':
        """Generate GUIDs for this schema and any nested schemas"""
        self.generate_guid()
        
        # Generate GUIDs for any nested schemas in properties
        if hasattr(self, 'properties'):
            for prop in self.properties.values():
                if isinstance(prop, BaseSchema):
                    prop.generate_guid()
        
        return self
    
    def to_json_schema(self) -> dict:
        """Convert the HDF5Schema to JSON Schema format"""
        schema = self.model_dump(
            by_alias=True,
            exclude_unset=True,
            exclude_none=True
        )
        return schema

PropertyUnion = Union[StringProperty, ArrayProperty, BooleanProperty, NumberProperty, IntegerProperty, NullProperty]
class TabularValidationSchema(BaseSchema):
    properties: Dict[str, PropertyUnion] = Field(default={})
    separator: str = Field(description="Field separator for the file")
    header: bool = Field(description="Do files of this schema have a header row", default=False)

    @classmethod
    def infer_from_file(cls, filepath: str, name: str, description: str, include_min_max: bool = False) -> 'TabularValidationSchema':
        """Infer schema from a file"""
        file_type = FileType.from_extension(filepath)
        
        if file_type == FileType.PARQUET:
            return cls.infer_from_parquet(name, description, None, filepath, include_min_max)
        else:  # csv or tsv
            separator = '\t' if file_type == FileType.TSV else ','
            df = pd.read_csv(filepath, sep=separator)
            return cls.infer_from_dataframe(df, name, description, include_min_max, separator)
        
    @classmethod
    def infer_from_dataframe(cls, df: pd.DataFrame, name: str, description: str, include_min_max: bool = False, separator: str = ',') -> 'TabularValidationSchema':
        """Infer schema from a pandas DataFrame"""
        type_map = {
            'int16': ('integer', IntegerProperty, int),
            'int32': ('integer', IntegerProperty, int),
            'int64': ('integer', IntegerProperty, int),
            'uint8': ('integer', IntegerProperty, int),
            'uint16': ('integer', IntegerProperty, int),
            'uint32': ('integer', IntegerProperty, int),
            'uint64': ('integer', IntegerProperty, int),
            'float16': ('number', NumberProperty, float),
            'float32': ('number', NumberProperty, float),
            'float64': ('number', NumberProperty, float),
            'bool': ('boolean', BooleanProperty, None),
        }
        
        properties = {}
        for i, (column_name, dtype) in enumerate(df.dtypes.items()):
            dtype_str = str(dtype)
            datatype, property_class, converter = type_map.get(dtype_str, ('string', StringProperty, None))
            
            kwargs = {
                "datatype": datatype,
                "description": f"Column {column_name}",
                "index": i
            }
            
            if include_min_max and converter:
                kwargs.update({
                    "minimum": converter(df[column_name].min()),
                    "maximum": converter(df[column_name].max())
                })
                
            properties[column_name] = property_class(**kwargs)
        
        return cls(
            name=name,
            description=description,
            properties=properties,
            required=list(properties.keys()),
            separator=separator,
            header=True
        )

    @classmethod
    def infer_from_parquet(cls, name: str, description: str, guid: Optional[str], filepath: str, include_min_max: bool = False) -> 'TabularValidationSchema':
        """Infer schema from a Parquet file"""
        table = pq.read_table(filepath)
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
            elif field_type == 'integer':
                if include_min_max:
                    column = table.column(field_name)
                    min_max = pc.min_max(column)
                    properties[field_name] = IntegerProperty(
                        datatype='integer',
                        description=f"Column {field_name}",
                        index=i,
                        minimum=min_max['min'].as_py(),
                        maximum=min_max['max'].as_py()
                    )
                else:
                    properties[field_name] = IntegerProperty(
                        datatype='integer',
                        description=f"Column {field_name}",
                        index=i
                    )
            elif field_type == 'number':
                if include_min_max:
                    column = table.column(field_name)
                    min_max = pc.min_max(column)
                    properties[field_name] = NumberProperty(
                        datatype='number',
                        description=f"Column {field_name}",
                        index=i,
                        minimum=min_max['min'].as_py(),
                        maximum=min_max['max'].as_py()
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

        return cls(
            name=name,
            description=description,
            guid=guid,
            properties=properties,
            required=list(properties.keys()),
            separator=",",  # Not used for parquet but required
            header=True    # Not used for parquet but required
        )

    def validate_file(self, filepath: str) -> List[Dict]:
        """Validate a file against the schema"""
        file_type = FileType.from_extension(filepath)
        
        if file_type == FileType.PARQUET:
            df = pd.read_parquet(filepath)
        else:  # csv or tsv
            sep = '\t' if file_type == FileType.TSV else self.separator
            df = pd.read_csv(filepath, sep=sep, header=0 if self.header else None)
        
        return self.validate_dataframe(df)

    def validate_dataframe(self, df: pd.DataFrame) -> List[Dict]:
        """Validate a dataframe against the schema with lenient string type checking.
        Only reports string validation errors for pattern mismatches, not type mismatches."""
        json_schema = self.to_json_schema()
        validator = jsonschema.Draft202012Validator(json_schema)
        errors = []

        for i, row in df.iterrows():
            row_dict = row.to_dict()
            validation_errors = sorted(validator.iter_errors(row_dict), key=lambda e: e.path)
            
            for err in validation_errors:
                # Skip type validation errors for string fields unless there's a pattern mismatch
                if err.validator == "type":
                    field_name = list(err.path)[-1] if err.path else None
                    if field_name in self.properties:
                        prop = self.properties[field_name]
                        if prop.datatype == "string":
                            # Skip string type validation errors
                            continue
                
                # Include all other validation errors
                errors.append({
                    "message": err.message,
                    "row": i,
                    "field": list(err.path)[-1] if err.path else None,
                    "type": "ValidationError",
                    "failed_keyword": err.validator
                })

        return errors

class HDF5Schema(BaseSchema):
    properties: Dict[str, TabularValidationSchema] = Field(default={})

    @staticmethod
    def dataset_to_dataframe(dataset: h5py.Dataset) -> pd.DataFrame:
        """Convert any HDF5 dataset to a pandas DataFrame"""
        data = dataset[()]
        
        # structured array convert directly
        if dataset.dtype.fields:
            return pd.DataFrame(data)
            
        # For multi-dimensional arrays make up column name
        elif len(dataset.shape) > 1:
            n_cols = dataset.shape[1] if len(dataset.shape) > 1 else 1
            columns = [f"column_{i}" for i in range(n_cols)]
            return pd.DataFrame(data, columns=columns)
            
        # For 1D arrays convert to single column DataFrame
        else:
            return pd.DataFrame(data, columns=['value'])

    @classmethod 
    def infer_from_file(cls, filepath: str, name: str, description: str, include_min_max: bool = False) -> 'HDF5Schema':
        """Infer schema from HDF5 file"""
        schema = cls(name=name, description=description)
        properties = {}
        
        with h5py.File(filepath, 'r') as f:
            def process_group(group, parent_path=""):
                for key, item in group.items():
                    path = f"{parent_path}/{key}" if parent_path else key
                    
                    if isinstance(item, h5py.Dataset):
                        try:
                            df = cls.dataset_to_dataframe(item)
                            properties[path] = TabularValidationSchema.infer_from_dataframe(
                                df,
                                name=f"{name}_{path.replace('/', '_')}",
                                description=f"Dataset at {path}",
                                include_min_max=include_min_max
                            )
                        except Exception as e:
                            print(f"Warning: Could not convert dataset {path} to DataFrame: {str(e)}")
                    
                    elif isinstance(item, h5py.Group):
                        # Recursively process group contents
                        process_group(item, path)
                
            process_group(f)
            schema.properties = properties
            schema.required = list(properties.keys())
        
        return schema

    def validate_file(self, filepath: str) -> List[Dict]:
        """Validate an HDF5 file against the schema"""
        errors = []
        
        with h5py.File(filepath, 'r') as f:
            for path, schema in self.properties.items():
                try:
                    # Try to get the dataset using the path
                    dataset = f[path]
                    if isinstance(dataset, h5py.Dataset):
                        # Convert dataset to DataFrame
                        df = self.dataset_to_dataframe(dataset)
                        # Validate using the TabularValidationSchema's validate_dataframe method
                        dataset_errors = schema.validate_dataframe(df)
                        # Add path information to errors
                        for error in dataset_errors:
                            error['path'] = path
                        errors.extend(dataset_errors)
                except KeyError:
                    errors.append({
                        "message": f"Dataset {path} not found",
                        "path": path,
                        "type": "ValidationError",
                        "failed_keyword": "required"
                    })
                except Exception as e:
                    errors.append({
                        "message": f"Error validating dataset {path}: {str(e)}",
                        "path": path,
                        "type": "ValidationError",
                        "failed_keyword": "format"
                    })
        
        return errors

    
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

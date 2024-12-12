import pathlib
import os
import json
import pandas as pd
import h5py
from datetime import datetime
from enum import Enum
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    model_validator
)
from typing import (
    Dict, 
    List, 
    Optional, 
    Literal,
    Union
)
from frictionless import Schema, Resource, describe, fields


from fairscape_cli.models.schema.utils import (
    PropertyNameException,
    ColumnIndexException,
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
    
    @classmethod
    def from_extension(cls, filepath: str) -> 'FileType':
        ext = pathlib.Path(filepath).suffix.lower()[1:]
        if ext == 'parquet':
            return cls.PARQUET
        elif ext == 'tsv':
            return cls.TSV
        elif ext == 'csv':
            return cls.CSV
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

class ValidationError(BaseModel):
    message: str
    row: Optional[int] = None
    field: Optional[str] = None
    type: str = "ValidationError"
    failed_keyword: str
    path: Optional[str] = None

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

def frictionless_type_to_json_schema(field_type: str) -> str:
    """Convert Frictionless types to JSON Schema types"""
    type_mapping = {
        'string': 'string',
        'integer': 'integer',
        'number': 'number',
        'boolean': 'boolean',
        'date': 'string',
        'datetime': 'string',
        'year': 'integer',
        'yearmonth': 'string',
        'duration': 'string',
        'geopoint': 'array',
        'geojson': 'object',
        'array': 'array',
        'object': 'object',
        'time': 'string'
    }
    return type_mapping.get(field_type, 'string')

class TabularValidationSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    guid: Optional[str] = Field(alias="@id", default=None)
    context: Optional[Dict] = Field(default=DEFAULT_CONTEXT, alias="@context")
    metadataType: Optional[str] = Field(default=DEFAULT_SCHEMA_TYPE, alias="@type")
    schema_version: str = Field(default="https://json-schema.org/draft/2020-12/schema", alias="$schema")
    name: str
    description: str
    datatype: str = Field(default="object", alias="type")
    separator: str = Field(description="Field separator for the file")
    header: bool = Field(description="Do files of this schema have a header row", default=True)
    required: List[str] = Field(default=[])
    properties: Dict[str, Dict] = Field(default={})
    additionalProperties: bool = Field(default=True)
    
    # Store the frictionless schema
    _frictionless_schema: Optional[Schema] = None

    def generate_guid(self) -> str:
        """Generate a unique identifier for the schema"""
        if self.guid is None:
            prefix = f"schema-{self.name.lower().replace(' ', '-')}"
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.guid = f"ark:{NAAN}/{prefix}-{timestamp}"
        return self.guid

    @model_validator(mode='after')
    def generate_all_guids(self) -> 'TabularValidationSchema':
        """Generate GUIDs for this schema and any nested schemas"""
        self.generate_guid()
        return self

    @classmethod
    def infer_from_file(cls, filepath: str, name: str, description: str, include_min_max: bool = False) -> 'TabularValidationSchema':
        """Infer schema from a file using Frictionless"""
        file_type = FileType.from_extension(filepath)
        separator = '\t' if file_type == FileType.TSV else ','
        
        resource = describe(filepath)
        
        properties = {}
        required_fields = []
        
        for i, field in enumerate(resource.schema.fields):
            json_schema_type = frictionless_type_to_json_schema(field.type)
            
            property_def = {
                "type": json_schema_type,
                "description": field.description or f"Column {field.name}",
                "index": i
            }
                    
            properties[field.name] = property_def
            required_fields.append(field.name)
        
        # Create our schema instance
        schema = cls(
            name=name,
            description=description,
            separator=separator,
            header=True,
            properties=properties,
            required=required_fields
        )
        
        # Store the frictionless schema for validation
        schema._frictionless_schema = resource.schema
        return schema

    def validate_file(self, filepath: str) -> List[ValidationError]:
        """Validate a file against the schema using Frictionless"""
        if not self._frictionless_schema:
            raise ValueError("Schema not properly initialized")
        
        resource = Resource(
            path=os.path.basename(filepath), 
            basepath=os.path.dirname(filepath), 
            schema=self._frictionless_schema
        )
        report = resource.validate()
        
        errors = []
        for task in report.tasks:
            for error in task.errors:
                if isinstance(error, TypeError):
                    validation_error = ValidationError(
                        message=str(error),
                        type="ValidationError",
                        failed_keyword="type"
                    )
                else:
                    validation_error = ValidationError(
                        message=error.message,
                        row=error.row_number if hasattr(error, 'row_number') else None,
                        field=error.field_name if hasattr(error, 'field_name') else None,
                        failed_keyword=error.code if hasattr(error, 'code') else "error"
                    )
                errors.append(validation_error)
                
        return errors

    def to_dict(self) -> dict:
        """Convert the schema to a dictionary format"""
        return self.model_dump(by_alias=True, exclude={'_frictionless_schema'})

    @classmethod
    def from_dict(cls, data: dict) -> 'TabularValidationSchema':
        """Create a schema instance from a dictionary"""
        properties = data.pop('properties', {})
        required_fields = data.pop('required', [])
        
        frictionless_schema = Schema()
        
        type_to_field = {
            'string': fields.StringField,
            'integer': fields.IntegerField,
            'number': fields.NumberField,
            'boolean': fields.BooleanField,
            'array': fields.ArrayField
        }
        
        for name, prop in properties.items():
            field_type = type_to_field.get(prop.get('type', 'string'), fields.StringField)
            field = field_type(
                name=name,
                description=prop.get('description', ''),
                constraints={}
            )
            
            # Add constraints if they exist
            if 'minimum' in prop:
                field.constraints['minimum'] = prop['minimum']
            if 'maximum' in prop:
                field.constraints['maximum'] = prop['maximum']
            if 'pattern' in prop:
                field.constraints['pattern'] = prop['pattern']
            if 'minLength' in prop:
                field.constraints['minLength'] = prop['minLength']
            if 'maxLength' in prop:
                field.constraints['maxLength'] = prop['maxLength']
                
            frictionless_schema.add_field(field)
        
        # Create our schema instance
        schema = cls(**data, properties=properties, required=required_fields)
        schema._frictionless_schema = frictionless_schema
        return schema

class HDF5ValidationSchema(BaseModel):
    guid: Optional[str] = Field(alias="@id", default=None)
    context: Optional[Dict] = Field(default=DEFAULT_CONTEXT, alias="@context")
    name: str
    description: str
    properties: Dict[str, TabularValidationSchema] = Field(default={})
    required: List[str] = Field(default=[])

    def generate_guid(self) -> str:
        """Generate a unique identifier for the schema"""
        if self.guid is None:
            prefix = f"schema-{self.name.lower().replace(' ', '-')}"
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.guid = f"ark:{NAAN}/{prefix}-{timestamp}"
        return self.guid

    @model_validator(mode='after')
    def generate_all_guids(self) -> 'HDF5ValidationSchema':
        """Generate GUIDs for this schema and any nested schemas"""
        self.generate_guid()
        return self
    
    @staticmethod
    def dataset_to_dataframe(dataset: h5py.Dataset) -> pd.DataFrame:
        """Convert an HDF5 dataset to a pandas DataFrame"""
        data = dataset[()]
        
        if dataset.dtype.fields:  # Structured array
            return pd.DataFrame(data)
        elif len(dataset.shape) > 1:  # Multi-dimensional array
            n_cols = dataset.shape[1]
            columns = [f"column_{i}" for i in range(n_cols)]
            return pd.DataFrame(data, columns=columns)
        else:  # 1D array
            return pd.DataFrame(data, columns=['value'])

    @classmethod
    def infer_from_file(cls, filepath: str, name: str, description: str) -> 'HDF5ValidationSchema':
        """Infer schema from an HDF5 file"""
        schema = cls(
            name=name,
            description=description
        )
        properties = {}

        with h5py.File(filepath, 'r') as f:
            def process_group(group, parent_path=""):
                for key, item in group.items():
                    path = f"{parent_path}/{key}" if parent_path else key
                    
                    if isinstance(item, h5py.Dataset):
                        try:
                            df = cls.dataset_to_dataframe(item)
                            resource = describe(df)
                            
                            tabular_schema = TabularValidationSchema(
                                name=f"{name}_{path.replace('/', '_')}",
                                description=f"Dataset at {path}",
                                separator=",",
                                header=True,
                                properties={},
                                required=[],
                                context=None
                            )
                            
                            tabular_schema._frictionless_schema = resource.schema
                            
                            for i, field in enumerate(resource.schema.fields):
                                property_def = {
                                    "type": field.type,
                                    "description": field.description or f"Column {field.name}",
                                    "index": i
                                }
                                
                                tabular_schema.properties[field.name] = property_def
                                tabular_schema.required.append(field.name)
                            
                            properties[path] = tabular_schema
                            
                        except Exception as e:
                            print(f"Warning: Could not process dataset {path}: {str(e)}")
                    
                    elif isinstance(item, h5py.Group):
                        process_group(item, path)
                        
            process_group(f)
            schema.properties = properties
            schema.required = list(properties.keys())
        
        return schema

    def validate_file(self, filepath: str) -> List[ValidationError]:
        """Validate an HDF5 file against the schema"""
        errors = []
        
        with h5py.File(filepath, 'r') as f:
            for path, schema in self.properties.items():
                try:
                    dataset = f[path]
                    if isinstance(dataset, h5py.Dataset):
                        df = self.dataset_to_dataframe(dataset)
                        resource = Resource(data=df, schema=schema._frictionless_schema)
                        report = resource.validate()
                        
                        for task in report.tasks:
                            for error in task.errors:
                                # Skip string type errors
                                if (hasattr(error, 'type') and error.type == 'type-error' and
                                    hasattr(error, 'note') and 'type is "string' in error.note):
                                    continue
                                    
                                validation_error = ValidationError(
                                    message=error.message,
                                    row=error.rowNumber if hasattr(error, 'rowNumber') else None,
                                    field=error.fieldName if hasattr(error, 'fieldName') else None,
                                    type="ValidationError",
                                    failed_keyword=error.type if hasattr(error, 'type') else "error",
                                    path=path
                                )
                                errors.append(validation_error)
                                
                except KeyError:
                    errors.append(ValidationError(
                        message=f"Dataset {path} not found",
                        type="ValidationError",
                        failed_keyword="required",
                        path=path
                    ))
                except Exception as e:
                    errors.append(ValidationError(
                        message=f"Error validating dataset {path}: {str(e)}",
                        type="ValidationError",
                        failed_keyword="format",
                        path=path
                    ))
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert the schema to a dictionary format including all fields"""
        return self.model_dump(by_alias=True)

    @classmethod
    def from_dict(cls, data: dict) -> 'HDF5ValidationSchema':
        """Create a schema instance from a dictionary"""
        properties = {
            path: TabularValidationSchema.from_dict(schema_dict)
            for path, schema_dict in data.get('properties', {}).items()
        }
        
        return cls(
            name=data['name'],
            description=data['description'],
            properties=properties,
            required=data.get('required', [])
        )
    
def write_schema(schema: TabularValidationSchema, output_file: str):
    """Write a schema to a file"""
    schema_dict = schema.to_dict()
    
    with open(output_file, 'w') as f:
        json.dump(schema_dict, f, indent=2)
    
def AppendProperty(schemaFilepath: str, propertyInstance, propertyName: str) -> None:
    # check that schemaFile exists
    schemaPath = pathlib.Path(schemaFilepath)
    if not schemaPath.exists():
        raise Exception

    with schemaPath.open("r+") as schemaFile:
        schemaFileContents = schemaFile.read()
        schemaJson = json.loads(schemaFileContents)

        schemaModel = TabularValidationSchema.model_validate(schemaJson)

        if propertyName in [key for key in schemaModel.properties.keys()]:
            raise PropertyNameException(propertyName)

        schema_indicies = [val['index'] for val in schemaModel.properties.values()]
        
        schemaModel.properties[propertyName] = propertyInstance
        schemaModel.required.append(propertyName)
        schemaJson = json.dumps(schemaModel.model_dump(by_alias=True, exclude_none=True), indent=2)

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


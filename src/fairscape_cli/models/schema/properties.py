import pathlib
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from fairscape_models.schema import Property

from fairscape_cli.models.schema.core import load_schema, write_schema
from fairscape_cli.models.schema.utils import (
    PropertyNameException,
    ColumnIndexException,
)


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


def AppendProperty(schemaFilepath: str, propertyInstance, propertyName: str) -> None:
    schemaPath = pathlib.Path(schemaFilepath)
    if not schemaPath.exists():
        raise FileNotFoundError(f"Schema file {schemaFilepath} does not exist")

    schemaModel = load_schema(schemaPath)

    if propertyName in schemaModel.properties:
        raise PropertyNameException(propertyName)

    canonical_property = Property.model_validate(
        propertyInstance.model_dump(by_alias=True, exclude_none=True)
    )
    schemaModel.properties[propertyName] = canonical_property
    schemaModel.required.append(propertyName)

    write_schema(schemaModel, schemaPath)


def ClickAppendProperty(ctx, schemaFile, propertyModel, name):
    try:
        # append the property to the schema file
        AppendProperty(schemaFile, propertyModel, name)
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

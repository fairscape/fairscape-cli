import pydantic
import pathlib
from enum import Enum
from typing import (
	Optional,
	List,
	Union
)

import imageio.v3 as iio
import pandas as pd

class ImageFormatEnum(str, Enum):
	"""
	Enum of Options for the supported image types for validation	

	"""
	jpeg = "jpeg"
	jpg = "jpg"
	tiff = "tiff"
	png = "png"


class ColorspaceEnum(str, Enum):
	"""
	Enum of supported Image Colorspaces for validation

	'RGB', 'BGR', 'RGBX', 'BGRX', 'XBGR', 'XRGB',
	'GRAY', 'RGBA', 'BGRA', 'ABGR', 'ARGB';
	'CMYK'
	"""
	rgb  = "RGB"
	bgr  = "BGR"
	rgbx = "RGBX"
	bgrx = "BGRX"
	xbgr = "XBGR"
	xrgb = "XRGB"
	gray = "GRAY"
	rgba = "RGBA"
	bgra = "BGRA"
	abgr = "ABGR"
	argb = "ARGB"
	cmyk = "CMYK"


class ImageSchema(pydantic.BaseModel):
	"""
	Image Schema for validating images based on format.
	May extend to support EXIF metadata on images

	Example Instance
	-------
	"imageSchema": {
				"@id": "ark:99999/schema/immunofluorescence_image_schema",
				"description": "Schema for validating immunoflourecense images",
				"format": "jpg",
				"height": 10000,
				"width": 10000,
				"colorspace": "RGB",
				"color_subsampling": "444"
				}
	
	"""
	guid: str
	description: str
	imageFormat: ImageFormatEnum
	height: int
	width: int
	colorspace: ColorspaceEnum
	colorSubsampling: Optional[str]


class ImageValidationException(Exception):
    """Exception Raised when Image Validation Fails
    """
    
    def __init__(self, message="Image Validation Failed"):
        self.message = message
        super().__init__(self.message)


class ImagePathNotFoundException(Exception):
    """Exception Raised when Image Path is not Found
    """
    pass


class ImageValidation():

    def __init__(
        self, 
        image_schema: ImageSchema, 
        image_path: pathlib.Path
    ):
        self.ImageSchema = image_schema
        self.ImagePath = image_path

        # check that image_path exists
        if image_path.exists() != True:
            raise ImagePathNotFoundException



    def validate(self) -> None:
        """Run the validation for the provided image and image schema

        If any mismatch is found between the Image properties and the ImageSchema
        Raise an ImageValidationException
        """

        # check that image path is one of the supported filetypes
        image_format = ImageFormatEnum(self.ImagePath.suffix.replace(".", "")) 

        # TODO run all validation checks and then raise exception
        # check that the image format is valid to the schema
        if image_format != self.ImageSchema.imageFormat:
            raise ImageValidationException(
                message = f"ImageFormat failed validation {image_format} != {self.ImageSchema.imageFormat}"
            )

        # read in image metadata
        image_metadata = iio.immeta(self.ImagePath)

        # contains encoding mode i.e. RGB
        colorspace = ColorspaceEnum(image_metadata["mode"])
        if colorspace != self.ImageSchema.colorspace:
            raise ImageValidationException(
                message = f"Colorspace failed validation {colorspace} != {self.ImageSchema.colorspace}"
                )

        
        # image_metadata['shape'] contains dimension tuple (height, width, depth)
        image_shape = image_metadata.get("shape")

        height = image_shape[0]
        width  = image_shape[1]


        if height != self.ImageSchema.height:
            raise ImageValidationException(
                message = f"Image Height {height} != {self.ImageSchema.height}"
                )
            
        if width != self.ImageSchema.width:
            raise ImageValidationException(
                message = f"Image Width {width} != {self.ImageSchema.width}"
                )



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
	description: str
	cells: Optional[list]
	datatype: Union[DatatypeEnum, DatatypeSchema]
	default: Optional[str]
	null: Optional[str]
	ordered: Optional[bool]
	number: int
	valueURL: Optional[str]
	required: bool
	table: Optional[list[str]]
	titles: list[str]

	def validate_column(self, data) -> bool:

		# if required check for no missing values
		if self.required:
			
			if data == np.nan:
				return False

		# check that string value is not 





class RowSchema(pydantic.BaseModel):
	name: str

class TabularDataSchema(pydantic.BaseModel):
	"""
	Schema for 	
	"""
	guid: str
	context: Optional[dict]
	metadataType: str = "TabularDataSchema"
	url: Optional[str]
	name: str
	columns: List[ColumnSchema]
	foreignKeys: Optional[list]
	description: str
	rows: Optional[List[RowSchema]]
	schemaUrl: Optional[str]

	
	def validate_data(self, data_path):
		pass
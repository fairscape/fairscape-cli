import pydantic
import pathlib
from enum import Enum
from typing import (
    Optional,
    List,
    Union
)

import imageio.v3 as iio

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
    rgb = "RGB"
    bgr = "BGR"
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
    Attributes
    ----------
    guid: str

    description: str

    imageFormat: ImageFormatEnum

    height: int

    width: int

    colorspace: ColorpsaceEnum

    colorSubsampling: Optional[str]

    Example
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
                message=f"ImageFormat failed validation {image_format} != {self.ImageSchema.imageFormat}"
            )

        # read in image metadata
        image_metadata = iio.immeta(self.ImagePath)

        # contains encoding mode i.e. RGB
        colorspace = ColorspaceEnum(image_metadata["mode"])
        if colorspace != self.ImageSchema.colorspace:
            raise ImageValidationException(
                message=f"Colorspace failed validation {colorspace} != {self.ImageSchema.colorspace}"
            )

        # image_metadata['shape'] contains dimension tuple (height, width, depth)
        image_shape = image_metadata.get("shape")

        height = image_shape[0]
        width = image_shape[1]

        if height != self.ImageSchema.height:
            raise ImageValidationException(
                message=f"Image Height {height} != {self.ImageSchema.height}"
            )

        if width != self.ImageSchema.width:
            raise ImageValidationException(
                message=f"Image Width {width} != {self.ImageSchema.width}"
            )

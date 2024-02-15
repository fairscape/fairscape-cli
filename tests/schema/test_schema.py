from fairscape_cli.models.schema.image import (
    ImageSchema,
    ImageValidation,
    ImageValidationException,
    ImagePathNotFoundException,
)

from fairscape_cli.__main__ import cli as fairscape_cli_app
import pathlib
from click.testing import CliRunner
import pytest
import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__),
                     '..')
    )
)


class TestValidateImage():

    def _test_success(self):

        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1728,
            "width": 1728,
            "colorspace": "RGB"
        })

        blue_image_path = pathlib.Path("./tests/data/1_A1_1_blue.jpg")
        red_image_path = pathlib.Path("./tests/data/1_A1_1_red.jpg")
        green_image_path = pathlib.Path("./tests/data/1_A1_1_green.jpg")
        yellow_image_path = pathlib.Path("./tests/data/1_A1_1_yellow.jpg")

        validate_blue = ImageValidation(
            image_schema=if_image_schema,
            image_path=blue_image_path
        )

        validate_blue.validate()

        validate_red = ImageValidation(
            image_schema=if_image_schema,
            image_path=red_image_path
        )

        validate_red.validate()

        validate_green = ImageValidation(
            image_schema=if_image_schema,
            image_path=green_image_path
        )

        validate_green.validate()

        validate_yellow = ImageValidation(
            image_schema=if_image_schema,
            image_path=yellow_image_path
        )

        validate_yellow.validate()

    def _test_path_not_found(self):

        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1728,
            "width": 10000,
            "colorspace": "RGB"
        })

        nonexistant_image_path = pathlib.Path("./not_an_image.jpg")

        with pytest.raises(ImagePathNotFoundException):

            validate_nonexistant = ImageValidation(
                image_schema=if_image_schema,
                image_path=nonexistant_image_path
            )

    def _test_width_incorrect(self):

        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1728,
            "width": 10000,
            "colorspace": "RGB"
        })

        blue_image_path = pathlib.Path("./tests/data/1_A1_1_blue.jpg")

        validate_blue = ImageValidation(
            image_schema=if_image_schema,
            image_path=blue_image_path
        )

        with pytest.raises(ImageValidationException):
            validate_blue.validate()

    def _test_height_incorrect(self):
        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1000,
            "width": 1728,
            "colorspace": "RGB"
        })

        blue_image_path = pathlib.Path("./tests/data/1_A1_1_blue.jpg")

        validate_blue = ImageValidation(
            image_schema=if_image_schema,
            image_path=blue_image_path
        )

        with pytest.raises(ImageValidationException):
            validate_blue.validate()

    def _test_colorspace_mismatch(self):
        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1728,
            "width": 1728,
            "colorspace": "GRAY"
        })

        blue_image_path = pathlib.Path("./tests/data/1_A1_1_blue.jpg")

        validate_blue = ImageValidation(
            image_schema=if_image_schema,
            image_path=blue_image_path
        )

        with pytest.raises(ImageValidationException):
            validate_blue.validate()

    def _test_format_mismatch(self):
        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
            "description": "Schema for validating immunoflourecense images",
            "imageFormat": "jpg",
            "height": 1728,
            "width": 1728,
            "colorspace": "GRAY"
        })

        blue_image_path = pathlib.Path("./tests/data/1_A1_1_blue.jpg")

        validate_blue = ImageValidation(
            image_schema=if_image_schema,
            image_path=blue_image_path
        )

        with pytest.raises(ImageValidationException):
            validate_blue.validate()


class TestValidateTabular():
    def test_0_init(self):
        pass


class TestSchemaCLI():

    def test_0_create_schema(self):
        pass


    def test_1_add_string_property(self):
        pass


    def test_2_add_int_property(self):
        pass


    def test_3_add_bool_property(self):
        pass


    def test_4_add_number_property(self):
        pass

    def test_5_add_array_property_string(self):
        pass

    def test_6_add_array_property_int(self):
        pass

    def test_7_add_array_property_number(self):
        pass

    def test_8_add_array_property_bool(self):
        pass


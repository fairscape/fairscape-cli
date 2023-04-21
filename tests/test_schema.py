import os
import sys

sys.path.insert(
    0, 
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), 
        '..')
    )
)

from click.testing import CliRunner
import pathlib
from fairscape_cli.main import cli as fairscape_cli_app
from fairscape_cli.models.schema import (
    ImageSchema,
    ImageValidation
)


class TestSchemaValidate():

    def test_validate_image(self):

        if_image_schema = ImageSchema(**{
            "guid": "ark:99999/schema/immunofluorescence_image_schema",
	    "description": "Schema for validating immunoflourecense images",
	    "imageFormat": "jpg",
	    "height": 1728,
	    "width": 1728,
	    "colorspace": "RGB"
        })

        blue_image_path   = pathlib.Path("./tests/data/1_A1_1_blue.jpg")
        red_image_path    = pathlib.Path("./tests/data/1_A1_1_red.jpg")
        green_image_path  = pathlib.Path("./tests/data/1_A1_1_green.jpg")
        yellow_image_path = pathlib.Path("./tests/data/1_A1_1_yellow.jpg")

        validate_blue   = ImageValidation(
            image_schema = if_image_schema, 
            image_path   = blue_image_path
            )

        validate_blue.validate()

        validate_red    = ImageValidation(
            image_schema = if_image_schema, 
            image_path   = red_image_path
            )

        validate_red.validate()

        validate_green  = ImageValidation(
            image_schema = if_image_schema, 
            image_path   = green_image_path
            )
        
        validate_green.validate()

        validate_yellow = ImageValidation(
            image_schema = if_image_schema, 
            image_path   = yellow_image_path
            )

        validate_yellow.validate()



    def test_validate_tabular(self):
        pass

class TestSchemaCLI():
    def test_cli(self):
        pass

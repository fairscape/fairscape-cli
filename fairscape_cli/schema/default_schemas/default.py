from functools import lru_cache
from typing import Dict
import os
import pathlib
from fairscape_cli.models.schema.tabular import (
	TabularValidationSchema,
	ReadSchema
)

@lru_cache
def ImportDefaultSchemas()-> Dict[str, TabularValidationSchema]:

	default_schema_location = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))

	# list out all directories of default schemas
	schema_paths = default_schema_location.rglob("*.json")

	# list all contents of schemas
	default_schema_list = [ ReadSchema(str(path_elem)) for path_elem in schema_paths]

	return  {
					Schema.guid : Schema for Schema in default_schema_list
	}

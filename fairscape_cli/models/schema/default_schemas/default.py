from functools import lru_cache
from typing import Dict
import os
import json
import pathlib
from typing import List
from fairscape_cli.models.schema.tabular import (
	TabularValidationSchema,
)

@lru_cache
def ImportDefaultSchemas()-> List[TabularValidationSchema]:
	defaultSchemaLocation = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
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
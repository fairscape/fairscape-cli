from fairscape_models.biochem_entity import BioChemEntity
from fairscape_cli.config import NAAN
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid, clean_guid
import datetime
from typing import Dict, Any, Optional, List, Tuple, Set

def GenerateBioChemEntity(
		guid: Optional[str] = None,
		name: Optional[str] = None,
		description: Optional[str] = None,
		usedBy: Optional[List[str]] = None,
		identifier: Optional[List[str]] = None,
		cratePath: Optional[str] = None,
		**kwargs
)-> BioChemEntity:
	"""
	Generate a BioChemEntity with flexible parameters.

	Args:
		guid: Optional identifier.
		name: Name for BioChem entity
		description: Description of BioChem entity
		usedBy: List of guids for Dataset/Sample/Experiment entities where this BioChemEntity was used
		identifier: Optional list of identifiers for the biochem entity, the type of identifier can be specified with '<identifier-name>;<identifier-value>'
		cratePath: Optional path to the RO-Crate containing the dataset
		**kwargs: Additional named parameters

	Returns:
		A validated fairscape_models.BioChemEntity instance 
	"""

	if not guid and name:
			sq = GenerateDatetimeSquid()
			seg = clean_guid(f"{name.lower().replace(' ', '-')}-{sq}")
			guid = f"ark:{NAAN}/dataset-{seg}"
	elif not guid:
			sq = GenerateDatetimeSquid()
			guid = f"ark:{NAAN}/dataset-{sq}"
	
	entityMetadata = {
			"@id": guid,
			"name": name,
			"@type": "https://schema.org/BioChemEntity",
			"description": description
	}

	# process identifiers
	identifierList = []

	if identifier:
		for guid in identifier:
			# try splitting in
			splitGUID = guid.strip("\n").split(";")
			
			# if name not specified
			if len(splitGUID) == 2:
				identifierList.append({
					"@type": "https://schema.org/PropertyValue",
					"name": splitGUID[0],
					"value": splitGUID[1]
				})

			elif len(splitGUID)==1:
				# TODO change models so identifiers can be string instead of all property value
				# identifierList.append(guid)

				raise Exception(f"identifiers not properly formatted: {guid}\n identifiers must be formatted with '<propertyName>:<propertyValue>'")
			else:
				# raise exception if identifier split incorrectly
				raise Exception(f"identifiers not properly formatted: {guid}\n identifiers must be formatted with '<propertyName>:<propertyValue>'")

	# add identifiers to metadata
	entityMetadata['identifier'] = identifierList

	for key, value in kwargs.items():
		if key in ["derivedFrom", "usedBy", "generatedBy"] and value:
			if isinstance(value, str):
				entityMetadata[key] = [{"@id": value.strip("\n")}]
			elif (isinstance(value, list) or isinstance(value, tuple)) and len(value) > 0:
				entityMetadata[key] = [{"@id": item.strip("\n")} for item in value]
		elif value is not None:
			entityMetadata[key] = value

	return BioChemEntity.model_validate(entityMetadata)

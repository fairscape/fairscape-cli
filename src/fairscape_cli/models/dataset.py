# Standard library imports
import pathlib
from datetime import datetime
from typing import Optional, List, Union, Dict, Tuple, Set, Any

from pydantic import (
    BaseModel,
    constr,
    Field,
    AnyUrl,
    field_serializer
)

from fairscape_cli.models.base import FairscapeBaseModel
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
from fairscape_cli.config import NAAN

class ArkPointer(BaseModel):
    ark: str = Field(
        alias="@id",
        validation_alias="@id"
    )


class Dataset(FairscapeBaseModel):
    guid: Optional[str] = Field(alias="@id", default=None)
    metadataType: Optional[str] = Field(alias="@type", default="https://w3id.org/EVI#Dataset")
    author: str = Field(max_length=64)
    datePublished: Optional[str] = Field()
    version: str
    description: str = Field(min_length=10)
    keywords: List[str] = Field(...)
    associatedPublication: Optional[str] = Field(default=None)
    additionalDocumentation: Optional[str] = Field(default=None)
    fileFormat: str = Field(alias="format")
    dataSchema: Optional[ArkPointer] = Field(alias="schema", default=None)
    generatedBy: Optional[List[ArkPointer]] = Field(default_factory=list)
    derivedFrom: Optional[List[ArkPointer]] = Field(default_factory=list)
    usedBy: Optional[List[ArkPointer]] = Field(default_factory=list)
    contentUrl: Optional[Union[str,List]] = Field(default=None)
    hasSummaryStatistics: Optional[ArkPointer] = Field(default=None)
    
    model_config = {
        "extra": "allow"
    }

    #@field_serializer('datePublished')
    #def serialize_date_published(self, datePublished: datetime):
    #    return datePublished.timestamp()


def GenerateDataset(
    guid: Optional[str],
    url: Optional[str],
    author: str,
    name: str,
    description: str,
    keywords: List[str],
    datePublished: str,
    version: str,
    dataFormat: str,
    associatedPublication: Optional[str] = None,
    additionalDocumentation: Optional[str] = None,
    schema: Optional[str] = None,
    derivedFrom: Optional[List[str]] = None,
    usedBy: Optional[List[str]] = None,
    generatedBy: Optional[List[str]] = None,
    filepath: Optional[str] = None,
    contentUrl: Optional[Union[str,List]] = None,
    cratePath = None,
    summary_stats_guid: Optional[str] = None,
    additional_metadata: Optional[Dict[str, Any]] = None
    ):
   
    if not guid:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/dataset-{name.lower().replace(' ', '-')}-{sq}"
    
    # Start with required fields
    datasetMetadata = {
        "@id": guid,
        "@type": "https://w3id.org/EVI#Dataset",
        "author": author,
        "name": name,
        "description": description,
        "keywords": keywords,
        "datePublished": datePublished,
        "version": version,
        "format": dataFormat
    }
    
    # Add optional fields only if they have values
    if url:
        datasetMetadata["url"] = url
        
    if associatedPublication:
        datasetMetadata["associatedPublication"] = associatedPublication
        
    if additionalDocumentation:
        datasetMetadata["additionalDocumentation"] = additionalDocumentation
        
    if schema:
        datasetMetadata["schema"] = {"@id": schema}
        
    if derivedFrom and len(derivedFrom) > 0:
        datasetMetadata["derivedFrom"] = [{"@id": derived.strip("\n")} for derived in derivedFrom]
        
    if usedBy and len(usedBy) > 0:
        datasetMetadata["usedBy"] = [{"@id": used.strip("\n")} for used in usedBy]
        
    if generatedBy and len(generatedBy) > 0:
        datasetMetadata["generatedBy"] = [{"@id": gen.strip("\n")} for gen in generatedBy]
        
    if summary_stats_guid:
        datasetMetadata["hasSummaryStatistics"] = {"@id": summary_stats_guid}
    
    # Handle file path if provided
    if filepath:
        datasetMetadata['contentUrl'] = setRelativeFilepath(cratePath, filepath)
    if contentUrl:
        datasetMetadata['contentUrl'] = contentUrl
    
    if additional_metadata:
        datasetMetadata.update(additional_metadata)
        
    datasetInstance = Dataset.model_validate(datasetMetadata)
    return datasetInstance


def setRelativeFilepath(cratePath, filePath):
    ''' Modify the filepath specified in metadata s.t. 
    '''

    if filePath is None:
        return None

    # if filepath is a url        
    if 'http' in  filePath:
        return filePath

    # if a relative file uri to the crate 
    if 'file:///' in filePath:
        # TODO: search within crate to determine file is relative to crate
        # filePath = filePath.replace("file:///", "")

        return filePath

    # set relative filepath
    # if filepath is a path that exists
    if 'ro-crate-metadata.json' in str(cratePath):
        rocratePath = pathlib.Path(cratePath).parent.absolute()
    else:
        rocratePath = pathlib.Path(cratePath).absolute()

            
    # if relative filepath
    datasetPath = pathlib.Path(filePath).absolute()
    relativePath = datasetPath.relative_to(rocratePath)
    return f"file:///{str(relativePath)}"


from fairscape_cli.models.computation import GenerateComputation, Computation
def generateSummaryStatsElements(
    name: str,
    author: str,
    keywords: List[str],
    date_published: str,
    version: str,
    associated_publication: Optional[str],
    additional_documentation: Optional[str],
    schema: Optional[str],
    dataset_guid: str,
    summary_statistics_filepath: str,
    crate_path: pathlib.Path
) -> Tuple[str, Dataset, Computation]:
    """Generate summary statistics dataset and computation elements
    
    Args:
        name: Name of the main dataset
        author: Author of the dataset
        keywords: Dataset keywords
        date_published: Publication date
        version: Dataset version
        associated_publication: Optional associated publication
        additional_documentation: Optional additional documentation
        schema: Optional schema
        dataset_guid: GUID of the main dataset
        summary_statistics_filepath: Path to summary statistics file
        crate_path: Path to RO-Crate
        
    Returns:
        Tuple containing:
        - Summary statistics GUID
        - Summary statistics Dataset instance
        - Computation instance that generated the summary statistics
    """
    # Generate GUIDs
    sq_stats = GenerateDatetimeSquid()
    summary_stats_guid = f"ark:{NAAN}/dataset-{name.lower().replace(' ', '-')}-stats-{sq_stats}"
    
    sq_comp = GenerateDatetimeSquid()
    computation_guid = f"ark:{NAAN}/computation-{name.lower().replace(' ', '-')}-stats-{sq_comp}"
    
    # Create computation instance
    computation_instance = GenerateComputation(
        guid=computation_guid,
        name=f"Summary Statistics Computation for {name}",
        runBy=author,
        command="",
        dateCreated=date_published,
        description=f"Computation that generated summary statistics for dataset: {name}",
        keywords=keywords,
        usedSoftware=[],
        usedDataset=[dataset_guid],
        generated=[summary_stats_guid]
    )

    # Create summary statistics dataset with only non-empty fields
    stats_dataset_params = {
        "guid": summary_stats_guid,
        "author": author,
        "name": f"{name} - Summary Statistics",
        "description": f"Summary statistics for dataset: {name}",
        "keywords": keywords,
        "datePublished": date_published,
        "version": version,
        "dataFormat": "pdf",
        "generatedBy": [computation_guid],
        "filepath": summary_statistics_filepath,
        "cratePath": crate_path
    }
    
    # Add optional fields only if they have values
    if associated_publication:
        stats_dataset_params["associatedPublication"] = associated_publication
    if additional_documentation:
        stats_dataset_params["additionalDocumentation"] = additional_documentation
    if schema:
        stats_dataset_params["schema"] = schema
    
    summary_stats_instance = GenerateDataset(**stats_dataset_params)
    
    return summary_stats_guid, summary_stats_instance, computation_instance

def registerOutputs(
    new_files: Set[pathlib.Path],
    computation_id: str, 
    dataset_id: str,
    author: str
) -> List[Dict]:
    """Register all outputs as datasets"""
    output_instances = []
    for file_path in new_files:
        file_path_str = str(file_path)
        
        # Create dataset with only non-empty fields
        output_params = {
            "guid": None,
            "name": f"Statistics Output - {file_path.name}",
            "author": author,
            "description": f"Statistical analysis output for {dataset_id}",
            "keywords": ["statistics"],
            "datePublished": datetime.now().isoformat(),
            "version": "1.0",
            "dataFormat": file_path.suffix[1:] if file_path.suffix else "unknown",
            "filepath": file_path_str,
            "cratePath": str(file_path.parent)
        }
        
        if computation_id:
            output_params["generatedBy"] = [computation_id]
            
        output_instance = GenerateDataset(**output_params)
        output_instances.append(output_instance)
    return output_instances
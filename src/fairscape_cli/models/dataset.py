from fairscape_models.dataset import Dataset
from fairscape_cli.config import NAAN
from fairscape_cli.models.guid_utils import GenerateDatetimeSquid
from fairscape_cli.models.utils import setRelativeFilepath
import pathlib
import datetime
from typing import Dict, Any, Optional, List, Tuple, Set

def GenerateDataset(
    guid: Optional[str] = None,
    name: Optional[str] = None,
    filepath: Optional[str] = None,
    cratePath: Optional[str] = None,
    **kwargs
) -> Dataset:
    """
    Generate a Dataset instance with flexible parameters.
    
    This function creates a Dataset instance with minimal required parameters and
    allows for any additional parameters to be passed through to the Dataset model.
    Validation is handled by the Dataset model itself.
    
    Args:
        guid: Optional identifier. If not provided, one will be generated.
        name: Optional name for the dataset. Used for GUID generation if provided.
        filepath: Optional path to the dataset file.
        cratePath: Optional path to the RO-Crate containing the dataset.
        **kwargs: Additional parameters to pass to the Dataset model.
        
    Returns:
        A validated Dataset instance
    """
    # Generate GUID if not provided
    if not guid and name:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/dataset-{name.lower().replace(' ', '-')}-{sq}"
    elif not guid:
        sq = GenerateDatetimeSquid()
        guid = f"ark:{NAAN}/dataset-{sq}"
    
    datasetMetadata = {
        "@id": guid,
        "name": name,
        "@type": "https://w3id.org/EVI#Dataset"
    }
    
    if filepath and cratePath:
        datasetMetadata['contentUrl'] = setRelativeFilepath(cratePath, filepath)
    elif filepath:
        datasetMetadata['contentUrl'] = filepath
    
    for key, value in kwargs.items():
        if key in ["schema", "dataSchema"] and value:
            datasetMetadata["schema"] = {"@id": value}
        elif key == "hasSummaryStatistics" and value:
            datasetMetadata["hasSummaryStatistics"] = {"@id": value}
        elif key in ["derivedFrom", "usedBy", "generatedBy"] and value:
            if isinstance(value, str):
                datasetMetadata[key] = [{"@id": value.strip("\n")}]
            elif (isinstance(value, list) or isinstance(value, tuple)) and len(value) > 0:
                datasetMetadata[key] = [{"@id": item.strip("\n")} for item in value]
        elif value is not None: 
            datasetMetadata[key] = value
    
    return Dataset.model_validate(datasetMetadata)

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
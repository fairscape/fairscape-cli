from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from pydantic import BaseModel, Field, ConfigDict, model_validator

##########################################################################
# --- Main Document Subsections ------------------------------------------
##########################################################################

class OverviewSection(BaseModel):
    # Core metadata
    title: Optional[str] = None
    description: Optional[str] = None
    id_value: Optional[str] = None
    doi: Optional[str] = None
    license_value: Optional[str] = Field(default=None, alias="license")

    # Dates
    release_date: Optional[str] = None
    created_date: Optional[str] = None
    updated_date: Optional[str] = None

    # People / orgs
    authors: List[str] = Field(default_factory=list)
    publisher: Optional[str] = None
    principal_investigator: Optional[str] = None
    contact_email: Optional[str] = None

    # Legal
    copyright: Optional[str] = None
    terms_of_use: Optional[str] = None
    citation: Optional[Union[str, List[str]]] = None

    # Versioning 
    version: Optional[str] = None
    content_size: Optional[str] = None
    funding: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    published: Optional[bool] = None 

    # Human-subjects
    human_subject_research: Optional[str] = None
    human_subject_exemptions: Optional[str] = None
    deidentified_samples: Optional[Union[str, bool]] = None
    fda_regulated: Optional[Union[str, bool]] = None
    confidentiality_level: Optional[str] = None
    irb: Optional[Union[str, Dict[str, Any]]] = None
    irb_protocol_id: Optional[str] = None
    
    ethical_review: Optional[str] = None
    data_governance: Optional[str] = None
    
    completeness: Optional[str] = None

    related_publications: List[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, extra="allow")

class UseCasesSection(BaseModel):
    """Datasheet section for describing dataset use cases, limitations, and biases."""

    intended_use: Optional[Union[str, List[str]]] = Field(
        default=None, description="Recommended dataset uses (e.g., training, validation)"
    )
    limitations: Optional[Union[str, List[str]]] = Field(
        default=None, description="Known limitations and non-recommended uses"
    )
    prohibited_uses: Optional[str] = Field(
        default=None, description="Explicitly prohibited uses (subset of limitations)"
    )
    potential_sources_of_bias: Optional[Union[str, List[str]]] = Field(
        default=None, description="Description of known biases in the dataset"
    )
    maintenance_plan: Optional[Union[str, List[str]]] = Field(
        default=None, description="Versioning, maintainers, and deprecation policies"
    )

    # Additional RAI fields
    data_collection: Optional[str] = Field(
        default=None, description="Description of data collection methodology"
    )
    data_collection_type: Optional[Union[str, List[str]]] = Field(
        default=None, description="Type of data collection"
    )
    data_collection_missing_data: Optional[str] = Field(
        default=None, description="Description of missing data in collection"
    )
    data_collection_raw_data: Optional[str] = Field(
        default=None, description="Description of raw data from collection"
    )
    data_collection_timeframe: Optional[Union[str, List[str]]] = Field(
        default=None, description="Timeframe of data collection"
    )
    data_imputation_protocol: Optional[str] = Field(
        default=None, description="Protocol used for data imputation"
    )
    data_manipulation_protocol: Optional[Union[str, List[str]]] = Field(
        default=None, description="Protocol used for data manipulation"
    )
    data_preprocessing_protocol: Optional[Union[str, List[str]]] = Field(
        default=None, description="Protocol used for data preprocessing"
    )
    data_annotation_protocol: Optional[str] = Field(
        default=None, description="Protocol used for data annotation"
    )
    data_annotation_platform: Optional[Union[str, List[str]]] = Field(
        default=None, description="Platform used for data annotation"
    )
    data_annotation_analysis: Optional[Union[str, List[str]]] = Field(
        default=None, description="Analysis of data annotations"
    )
    personal_sensitive_information: Optional[Union[str, List[str]]] = Field(
        default=None, description="Description of personal/sensitive information"
    )
    data_social_impact: Optional[str] = Field(
        default=None, description="Social impact of the data"
    )
    annotations_per_item: Optional[str] = Field(
        default=None, description="Number of annotations per item"
    )
    annotator_demographics: Optional[Union[str, List[str]]] = Field(
        default=None, description="Demographics of annotators"
    )
    machine_annotation_tools: Optional[Union[str, List[str]]] = Field(
        default=None, description="Machine tools used for annotation"
    )

    model_config = ConfigDict(extra="allow")


class DistributionSection(BaseModel):
    """Datasheet section for high-level distribution metadata."""
    
    license_value: Optional[str] = Field(default=None, description="License URL or identifier")
    publisher: Optional[str] = Field(default=None, description="Publisher of the release")
    doi: Optional[str] = Field(default=None, description="DOI identifier for the release")
    release_date: Optional[str] = Field(default=None, description="Publication/release date (ISO format)")
    version: Optional[str] = Field(default=None, description="Version of the release")
    
    model_config = ConfigDict(extra="ignore")
    

class CompositionDetails(BaseModel):
    # counts
    files_count: int = 0
    software_count: int = 0
    instruments_count: int = 0
    samples_count: int = 0
    experiments_count: int = 0
    computations_count: int = 0
    schemas_count: int = 0
    models_count: int = 0
    other_count: int = 0
    datasets_with_provenance_count: int = 0

    # formats & access summaries
    file_formats: Dict[str, int] = {}
    model_formats: Dict[str, int] = {}
    software_formats: Dict[str, int] = {}
    file_access: Dict[str, int] = {}
    software_access: Dict[str, int] = {}

    # patterns
    computation_patterns: Optional[List[str]] = None
    experiment_patterns: Optional[List[str]] = None

    # inputs
    input_datasets: Dict[str, int] = {}
    input_datasets_count: int = 0
    inputs_count: int = 0

    # domain-specific
    cell_lines: List[str] = []
    species: List[str] = []
    experiment_types: List[str] = []

class SubCrateItem(BaseModel):
    # Identity & basics
    name: str = Field(default="Unnamed Sub-Crate")
    id: str
    description: Optional[str] = None
    authors: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    metadata_path: Optional[str] = None
    statistical_summary_info: Optional[str] = None
    size: Optional[str] = None

    # High-level metadata
    doi: Optional[str] = None
    date: Optional[str] = None
    contact: Optional[str] = None
    published: Optional[bool] = None

    # Policy / legal
    copyright: Optional[str] = None
    license: Optional[str] = None
    terms_of_use: Optional[str] = None
    confidentiality: Optional[str] = None
    funder: Optional[str] = None
    md5: Optional[str] = None
    evidence: Optional[str] = None

    composition_details: CompositionDetails = Field(default_factory=CompositionDetails)

    # Publications
    related_publications: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")



class CompositionSection(BaseModel):
    """List of SubCrates to be rendered."""
    items: List[SubCrateItem] = Field(default_factory=list)
    
##########################################################################
# --- Sub-Crate Preview Models -------------------------------------------
##########################################################################


class PreviewItem(BaseModel):
    """Generic preview item used for datasets, software, computations, etc."""
    id: str = Field(default="", description="Entity @id or guid")
    name: str = Field(default="Unnamed Item")
    description: Optional[str] = None
    type: Optional[str] = Field(default=None, description="Primary normalized type (Dataset, Software, etc.)")
    date: Optional[str] = Field(default=None, description="datePublished / dateModified / dateCreated")
    identifier: Optional[str] = None

    # Access & linking
    content_status: Optional[str] = Field(default=None, description="Access / Download status text or link HTML")
    content_url: Optional[str] = None

    experimentType: Optional[str] = None
    manufacturer: Optional[str] = None

    schema_properties: Optional[Dict[str, Dict[str, Union[str, int]]]] = None

    model_config = ConfigDict(extra="allow")


class Preview(BaseModel):
    """Full preview payload (overview + item buckets)."""

    title: str = Field(default="Untitled RO-Crate")
    id_value: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    doi: Optional[str] = None
    license_value: Optional[str] = None

    # Dates
    release_date: Optional[str] = None
    created_date: Optional[str] = None
    updated_date: Optional[str] = None

    # People / orgs
    authors: Optional[str] = None        
    publisher: Optional[str] = None
    principal_investigator: Optional[str] = None
    contact_email: Optional[str] = None
    confidentiality_level: Optional[str] = None

    # Misc
    keywords: List[str] = Field(default_factory=list)
    citation: Optional[Union[str, List[str]]] = None
    related_publications: List[str] = Field(default_factory=list)

    # Linked QC/summary stats report
    statistical_summary_name: Optional[str] = None
    statistical_summary_url: Optional[str] = None

    # Item buckets
    datasets: List[PreviewItem] = Field(default_factory=list)
    software: List[PreviewItem] = Field(default_factory=list)
    computations: List[PreviewItem] = Field(default_factory=list)
    samples: List[PreviewItem] = Field(default_factory=list)
    experiments: List[PreviewItem] = Field(default_factory=list)
    instruments: List[PreviewItem] = Field(default_factory=list)
    schemas: List[PreviewItem] = Field(default_factory=list)
    other_items: List[PreviewItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


##########################################################################
# --- Fairscape Datasheet Top Level Model --------------------------------
##########################################################################

class FairscapeDatasheet(BaseModel):
    """Top-level datasheet composed of section DTOs."""
    overview: Optional[OverviewSection] = None
    use_cases: Optional[UseCasesSection] = None
    distribution: Optional[DistributionSection] = None
    composition: Optional[CompositionSection] = None

    model_config = ConfigDict(extra="ignore")

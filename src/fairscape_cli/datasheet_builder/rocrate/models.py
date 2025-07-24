from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class AIReadyCriterion(BaseModel):
    name: str
    score: int  # Number of passed sub-criteria
    max_score: int # Total number of sub-criteria for this criterion
    evidence: str
    sub_criteria_evidence: Dict[str, str] = Field(default_factory=dict)

class AIReadySummary(BaseModel):
    fairness: AIReadyCriterion
    provenance: AIReadyCriterion
    characterization: AIReadyCriterion
    pre_model_explainability: AIReadyCriterion
    ethics: AIReadyCriterion
    sustainability: AIReadyCriterion
    computability: AIReadyCriterion

class CrateComposition(BaseModel):
    datasets: int = 0
    software: int = 0
    computations: int = 0
    experiments: int = 0
    samples: int = 0
    instruments: int = 0
    schemas: int = 0
    other: int = 0
    total_size: str = "N/A"
    file_formats: Dict[str, int] = Field(default_factory=dict)
    software_formats: Dict[str, int] = Field(default_factory=dict)
    computation_patterns: List[str] = Field(default_factory=list)
    experiment_patterns: List[str] = Field(default_factory=list)
    input_datasets_count: int = 0
    input_datasets: Dict[str, int] = Field(default_factory=dict)

class CrateContent(BaseModel):
    """Holds detailed lists of crate contents, primarily for sub-crate previews."""
    datasets: List[Dict[str, Any]] = Field(default_factory=list)
    software: List[Dict[str, Any]] = Field(default_factory=list)
    computations: List[Dict[str, Any]] = Field(default_factory=list)
    experiments: List[Dict[str, Any]] = Field(default_factory=list)
    samples: List[Dict[str, Any]] = Field(default_factory=list)
    instruments: List[Dict[str, Any]] = Field(default_factory=list)
    schemas: List[Dict[str, Any]] = Field(default_factory=list)
    other: List[Dict[str, Any]] = Field(default_factory=list)

class AIReadyCrate(BaseModel):
    # Core Metadata for display
    guid: str
    name: str
    description: str
    author: str
    version: str
    keywords: List[str]
    license: str
    date_published: str
    doi: str
    publisher: str
    principal_investigator: str
    contact_email: str
    funder: str
    citation: str
    conditions_of_access: str
    copyright_notice: str
    confidentiality_level: str
    usage_info: str
    ethical_review: str
    published: bool
    metadata_path: Optional[str] = None
    evidence_graph_path: Optional[str] = None
    associated_publication: List[str] = Field(default_factory=list)

    # Processed Sections
    composition: CrateComposition
    content: CrateContent
    ai_ready_summary: Optional[AIReadySummary] = None
    
    # List of sub-crates, each also as an AIReadyCrate model
    subcrates: List['AIReadyCrate'] = Field(default_factory=list)

# Allow recursive model reference for subcrates
AIReadyCrate.model_rebuild()
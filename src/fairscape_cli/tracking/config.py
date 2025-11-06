from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class TrackerConfig:
    track_builtins: bool = True
    track_pathlib: bool = True
    track_pandas: bool = True
    track_numpy: bool = True
    excluded_patterns: List[str] = field(default_factory=lambda: [
        '.matplotlib',
        '.ipython',
        '.jupyter',
        'site-packages',
        '/tmp/',
        '__pycache__'
    ])


@dataclass
class TrackingResult:
    computation_guid: str
    software_guid: str
    input_count: int
    output_count: int
    reused_count: int
    new_datasets: int
    
    def __str__(self):
        return (
            f"Tracked computation: {self.computation_guid}\n"
            f"  Software: {self.software_guid}\n"
            f"  Inputs: {self.input_count} datasets ({self.reused_count} reused)\n"
            f"  Outputs: {self.output_count} datasets"
        )


@dataclass
class ProvenanceConfig:
    rocrate_path: Path
    author: str = "Unknown"
    keywords: List[str] = field(default_factory=lambda: ["jupyter", "computation"])
    manual_inputs: List[str] = field(default_factory=list)
    use_llm: bool = False

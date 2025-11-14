from pathlib import Path
from typing import Optional, Dict
import pandas as pd


def normalize_path(filepath) -> str:
    """Normalize a filepath to absolute string representation."""
    if isinstance(filepath, (str, Path)):
        return str(Path(filepath).resolve())
    return str(filepath)


def is_trackable_path(filepath: str, excluded_patterns: list) -> bool:
    """Check if a filepath should be tracked based on exclusion patterns."""
    if not filepath:
        return False
    filepath_str = str(filepath)
    return not any(pattern in filepath_str.lower() for pattern in excluded_patterns)


def read_dataset_sample(filepath: str, n_rows: int = 5) -> Optional[str]:
    """Read first n rows from a dataset file as a string sample."""
    try:
        path = Path(filepath)
        if not path.exists():
            return None
        
        suffix = path.suffix.lower()
        df = None
        
        if suffix == '.csv':
            df = pd.read_csv(filepath)
        elif suffix == '.parquet':
            df = pd.read_parquet(filepath)
        elif suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
        
        if df is not None:
            return df.head(n_rows).to_string()
        
        return None
    except Exception:
        return None


def collect_dataset_samples(filepaths: set, n_rows: int = 5) -> Dict[str, str]:
    """Collect samples from multiple dataset files."""
    samples = {}
    for filepath in filepaths:
        sample = read_dataset_sample(filepath, n_rows)
        if sample:
            samples[Path(filepath).name] = sample
    return samples


def format_samples_for_prompt(samples_dict: Dict[str, str]) -> str:
    """Format dataset samples into a string for LLM prompts."""
    if not samples_dict:
        return "None"
    return "\n\n".join([f"File: {name}\n{sample}" for name, sample in samples_dict.items()])

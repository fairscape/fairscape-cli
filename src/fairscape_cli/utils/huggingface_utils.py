"""
Utilities for fetching and parsing HuggingFace model metadata.
"""
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse
import re

USE_CASE_KEYWORDS = [
    "use case",
    "use-case",
    "use cases",
    "uses cases",
    "intended use",
    "intended uses",
    "intended-use",
    "limitations",
    "appropriate use",
    "applications",
]

USAGE_KEYWORDS = [
    "model usage",
    "usage",
    "useage",
    "usuage",
    "usauge",
    "how to use",
    "using this model",
    "getting started",
    "inference",
    "prediction",
]

BIAS_KEYWORDS = [
    "bias",
    "biases",
    "biased",
    "safety",
]


def parse_huggingface_url(url: str) -> str:
    """
    Extract the repo_id from a HuggingFace URL or validate a repo_id.

    Args:
        url: HuggingFace URL (e.g., https://huggingface.co/timm/densenet121.tv_in1k)
             or repo_id (e.g., "timm/densenet121.tv_in1k")

    Returns:
        repo_id (e.g., "timm/densenet121.tv_in1k")

    Raises:
        ValueError: If not a valid HuggingFace URL or repo_id
    """
    # Check if it's already a repo_id (author/model format without URL)
    if '/' in url and not url.startswith('http://') and not url.startswith('https://'):
        # Validate it's in author/model format
        parts = url.strip('/').split('/')
        if len(parts) >= 2:
            return '/'.join(parts[:2])
        raise ValueError(f"Invalid HuggingFace repo_id format: {url}")

    # Otherwise, parse as URL
    parsed = urlparse(url)

    if parsed.netloc not in ['huggingface.co', 'www.huggingface.co']:
        raise ValueError(f"Not a valid HuggingFace URL or repo_id: {url}")

    path = parsed.path.strip('/')

    path = re.sub(r'/(tree|blob|resolve)/.*$', '', path)

    if '/' not in path:
        raise ValueError(f"Invalid HuggingFace repo path: {path}")

    parts = path.split('/')
    if len(parts) < 2:
        raise ValueError(f"Invalid HuggingFace repo path: {path}")

    return '/'.join(parts[:2])


def select_model_file(files: List[Any]) -> Optional[Tuple[str, Any]]:
    """
    Select the main model file from a list of repo files.

    Prioritizes by extension, then by last_commit date if available.

    Args:
        files: List of RepoFile objects from HuggingFace API

    Returns:
        Tuple of (filename, file_object) or None if no model file found
    """
    # Extension priority (most preferred first)
    extension_priority = ['.safetensors', '.bin', '.pth', '.ckpt', '.h5']

    files_by_ext = {ext: [] for ext in extension_priority}

    for file_obj in files:
        filename = file_obj.rfilename if hasattr(file_obj, 'rfilename') else str(file_obj)

        # Check each extension
        for ext in extension_priority:
            if filename.endswith(ext):
                files_by_ext[ext].append((filename, file_obj))
                break

    # Find the first extension that has files
    for ext in extension_priority:
        if files_by_ext[ext]:
            candidates = files_by_ext[ext]

            if len(candidates) > 1:
                def get_commit_date(item):
                    _, file_obj = item
                    if hasattr(file_obj, 'last_commit') and file_obj.last_commit:
                        if hasattr(file_obj.last_commit, 'date'):
                            return file_obj.last_commit.date
                    return None

                with_dates = [(f, obj) for f, obj in candidates if get_commit_date((f, obj))]
                if with_dates:
                    with_dates.sort(key=get_commit_date, reverse=True)
                    return with_dates[0]

            return candidates[0]

    return None


def extract_section_from_markdown(markdown_text: str, section_heading: str) -> Optional[str]:
    """
    Extract a section from markdown text based on heading.

    Args:
        markdown_text: Full markdown text
        section_heading: Heading to search for (case-insensitive)

    Returns:
        Section content or None if not found
    """
    if not markdown_text:
        return None

    lines = markdown_text.split('\n')
    section_content = []
    in_section = False
    section_level = None

    for line in lines:
        # Check if this is a heading
        if line.strip().startswith('#'):
            heading_match = line.strip()
            # Count the heading level
            level = len(heading_match) - len(heading_match.lstrip('#'))
            heading_text = heading_match.lstrip('#').strip()

            # Check if this is our target section
            if heading_text.lower() == section_heading.lower():
                in_section = True
                section_level = level
                continue

            # If we were in a section and hit another heading of same or higher level, stop
            if in_section and section_level is not None and level <= section_level:
                break

        # Collect lines if we're in the target section
        if in_section:
            section_content.append(line)

    if section_content:
        return '\n'.join(section_content).strip()

    return None


def extract_section_by_keywords(markdown_text: str, keywords: List[str]) -> Optional[str]:
    """
    Extract a section from markdown using heading keywords (case-insensitive).
    Falls back to the first paragraph containing any keyword when no heading matches.
    """
    if not markdown_text:
        return None

    lower_keywords = [kw.lower() for kw in keywords]
    lines = markdown_text.split('\n')
    section_content = []
    in_section = False
    section_level = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            heading_text = stripped.lstrip('#').strip().lower()
            if any(keyword in heading_text for keyword in lower_keywords):
                in_section = True
                section_level = level
                continue
            if in_section and section_level is not None and level <= section_level:
                break
        if in_section:
            section_content.append(line)

    if section_content:
        return '\n'.join(section_content).strip()

    # Fallback: first paragraph containing a keyword
    paragraphs = markdown_text.split('\n\n')
    for paragraph in paragraphs:
        if any(keyword in paragraph.lower() for keyword in lower_keywords):
            return paragraph.strip()

    return None


def extract_model_metadata(model_info: Any, hf_url: str, model_card_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract metadata from HuggingFace ModelInfo object.

    Args:
        model_info: ModelInfo object from huggingface_hub.model_info()
        hf_url: Original HuggingFace URL
        model_card_text: Optional model card text content

    Returns:
        Dictionary of metadata mapped to MLModel schema
    """
    metadata = {}

    # Basic info
    if hasattr(model_info, 'id'):
        # Use the model ID as name
        metadata['name'] = model_info.id
    elif hasattr(model_info, 'modelId'):
        metadata['name'] = model_info.modelId

    if hasattr(model_info, 'author') and model_info.author:
        metadata['author'] = model_info.author

    # Description - try multiple sources
    description = None

    # First try the description field from model_info
    if hasattr(model_info, 'description') and model_info.description:
        description = model_info.description

    # If not found, try to extract from model card text
    if not description and model_card_text:
        # Extract first paragraph or first non-empty line as description
        lines = model_card_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            # Skip headers and empty lines
            if line and not line.startswith('#') and not line.startswith('---'):
                description = line
                break

    if description:
        metadata['description'] = description

    # Try to extract sections from model card text
    if model_card_text:
        usage_section = extract_section_by_keywords(model_card_text, USAGE_KEYWORDS)
        if usage_section:
            metadata['usage_information'] = usage_section

        use_case_section = extract_section_by_keywords(model_card_text, USE_CASE_KEYWORDS)
        if use_case_section:
            metadata['intended_use_case'] = use_case_section

        bias_section = extract_section_by_keywords(model_card_text, BIAS_KEYWORDS)
        if bias_section:
            metadata['bias'] = bias_section

        metadata['README'] = model_card_text

    # Keywords from tags
    if hasattr(model_info, 'tags') and model_info.tags:
        metadata['keywords'] = list(model_info.tags)

        # Try to extract framework from tags
        framework_tags = ['pytorch', 'tensorflow', 'jax', 'keras', 'onnx']
        for tag in model_info.tags:
            if tag.lower() in framework_tags:
                metadata['framework'] = tag
                break

        # Try to extract model type from tags
        if 'image-classification' in model_info.tags:
            metadata['model_type'] = 'image-classification'
        elif 'text-generation' in model_info.tags:
            metadata['model_type'] = 'text-generation'
        elif 'text-classification' in model_info.tags:
            metadata['model_type'] = 'text-classification'

    # Card data (model card metadata)
    if hasattr(model_info, 'cardData') and model_info.cardData:
        card_data = model_info.cardData

        # License
        if hasattr(card_data, 'license') and card_data.license:
            metadata['license'] = card_data.license
        elif isinstance(card_data, dict) and 'license' in card_data:
            metadata['license'] = card_data['license']

        # Base model
        if hasattr(card_data, 'base_model') and card_data.base_model:
            metadata['base_model'] = card_data.base_model
        elif isinstance(card_data, dict) and 'base_model' in card_data:
            metadata['base_model'] = card_data['base_model']

        # Training datasets - convert to HuggingFace dataset URLs
        datasets = None
        if hasattr(card_data, 'datasets') and card_data.datasets:
            datasets = card_data.datasets
        elif isinstance(card_data, dict) and 'datasets' in card_data:
            datasets = card_data['datasets']

        if datasets:
            # Convert dataset names to HuggingFace URLs
            dataset_urls = []
            for ds in datasets:
                # If it's already a URL, keep it as-is
                if isinstance(ds, str) and (ds.startswith('http://') or ds.startswith('https://')):
                    dataset_urls.append(ds)
                # Otherwise, construct HuggingFace dataset URL
                elif isinstance(ds, str):
                    dataset_urls.append(f"https://huggingface.co/datasets/{ds}")
                else:
                    dataset_urls.append(str(ds))
            metadata['training_datasets'] = dataset_urls

    # Landing page URL
    metadata['landing_page_url'] = hf_url

    # Download URL (will be set from file selection)
    if hasattr(model_info, 'siblings') and model_info.siblings:
        selected = select_model_file(model_info.siblings)
        if selected:
            filename, _ = selected
            repo_id = model_info.id if hasattr(model_info, 'id') else model_info.modelId
            metadata['download_url'] = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"

            # Try to infer model format from filename
            if filename.endswith('.safetensors'):
                metadata['model_format'] = 'safetensors'
            elif filename.endswith('.bin'):
                metadata['model_format'] = 'pytorch-bin'
            elif filename.endswith('.pth'):
                metadata['model_format'] = 'pytorch-pth'
            elif filename.endswith('.ckpt'):
                metadata['model_format'] = 'checkpoint'
            elif filename.endswith('.h5'):
                metadata['model_format'] = 'h5'

    # Version (use "1.0" as default, could be overridden)
    metadata['version'] = '1.0'

    return metadata


def fetch_huggingface_model_metadata(hf_url: str) -> Dict[str, Any]:
    """
    Fetch model metadata from HuggingFace API.

    Args:
        hf_url: HuggingFace model URL

    Returns:
        Dictionary of model metadata

    Raises:
        ImportError: If huggingface_hub is not installed
        ValueError: If URL is invalid
        Exception: If API call fails
    """
    try:
        from huggingface_hub import model_info
        from huggingface_hub.repocard import RepoCard
    except ImportError:
        raise ImportError(
            "huggingface_hub is required for HuggingFace integration. "
            "Install it with: pip install huggingface_hub"
        )

    repo_id = parse_huggingface_url(hf_url)

    try:
        info = model_info(repo_id, files_metadata=True)
    except Exception as e:
        raise Exception(f"Failed to fetch model info from HuggingFace: {e}")

    model_card_text = None
    try:
        card = RepoCard.load(repo_id)
        model_card_text = card.text if hasattr(card, 'text') else None
    except Exception:
        pass

    metadata = extract_model_metadata(info, hf_url, model_card_text)

    return metadata

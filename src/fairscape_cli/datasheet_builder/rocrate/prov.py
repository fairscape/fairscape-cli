def get_dataset_format(processor, dataset_id):
    """
    Get the format of a dataset by its ID
    
    Args:
        processor: ROCrateProcessor instance
        dataset_id: The ID of the dataset
    
    Returns:
        str: The format of the dataset, or "unknown" if not found
    """
    for item in processor.graph:
        if item.get("@id") == dataset_id:
            return item.get("format", "unknown")
    
    # If not found in current crate, look for it in subcrates
    subcrates = processor.find_subcrates()
    for subcrate_info in subcrates:
        metadata_path = subcrate_info.get("metadata_path", "")
        if metadata_path:
            try:
                subcrate_processor = ROCrateProcessor(json_path=metadata_path)
                for item in subcrate_processor.graph:
                    if item.get("@id") == dataset_id:
                        return item.get("format", "unknown")
            except Exception:
                pass
    
    return "unknown"

def summarize_computation_io_formats(processor):
    """
    Summarize the input and output formats for computations
    
    Args:
        processor: ROCrateProcessor instance
    
    Returns:
        dict: Dictionary with computation patterns as keys and counts as values
    """
    _, _, _, _, _, computations, _, _ = processor.categorize_items()
    
    patterns = {}
    
    for computation in computations:
        input_formats = []
        output_formats = []
        
        # Get input formats
        input_datasets = computation.get("usedDataset", [])
        if input_datasets:
            if isinstance(input_datasets, list):
                for dataset in input_datasets:
                    if isinstance(dataset, dict) and "@id" in dataset:
                        input_format = get_dataset_format(processor, dataset["@id"])
                        if input_format not in input_formats:
                            input_formats.append(input_format)
                    elif isinstance(dataset, str):
                        input_format = get_dataset_format(processor, dataset)
                        if input_format not in input_formats:
                            input_formats.append(input_format)
            elif isinstance(input_datasets, dict) and "@id" in input_datasets:
                input_format = get_dataset_format(processor, input_datasets["@id"])
                input_formats.append(input_format)
            elif isinstance(input_datasets, str):
                input_format = get_dataset_format(processor, input_datasets)
                input_formats.append(input_format)
        
        # Get output formats
        output_datasets = computation.get("generated", [])
        if output_datasets:
            if isinstance(output_datasets, list):
                for dataset in output_datasets:
                    if isinstance(dataset, dict) and "@id" in dataset:
                        output_format = get_dataset_format(processor, dataset["@id"])
                        if output_format not in output_formats:
                            output_formats.append(output_format)
                    elif isinstance(dataset, str):
                        output_format = get_dataset_format(processor, dataset)
                        if output_format not in output_formats:
                            output_formats.append(output_format)
            elif isinstance(output_datasets, dict) and "@id" in output_datasets:
                output_format = get_dataset_format(processor, output_datasets["@id"])
                output_formats.append(output_format)
            elif isinstance(output_datasets, str):
                output_format = get_dataset_format(processor, output_datasets)
                output_formats.append(output_format)
        
        # Create a pattern string
        if input_formats and output_formats:
            input_str = ", ".join(sorted(input_formats))
            output_str = ", ".join(sorted(output_formats))
            pattern = f"{input_str} → {output_str}"
            
            if pattern in patterns:
                patterns[pattern] += 1
            else:
                patterns[pattern] = 1
    
    return patterns

def get_computation_summary(processor):
    """
    Get a summary of computation transformations
    
    Args:
        processor: ROCrateProcessor instance
    
    Returns:
        list: List of transformation pattern strings
    """
    patterns = summarize_computation_io_formats(processor)
    summary = []
    
    for pattern, count in patterns.items():
        summary.append(pattern)
    
    return summary
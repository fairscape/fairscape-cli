import pandas as pd
import sys
import os
from pathlib import Path

def generate_summary_stats(input_path, output_dir):
    """
    Generate summary statistics for a CSV file and save to output directory
    
    Parameters:
    input_path (str): Path to input CSV file
    output_dir (str): Directory to save output summary statistics
    """
    # Read the input file
    df = pd.read_csv(input_path)
    
    # Create summary statistics
    summary_stats = pd.DataFrame({
        'column_name': df.columns,
        'data_type': df.dtypes.astype(str),
        'count': df.count(),
        'null_count': df.isnull().sum(),
        'null_percentage': (df.isnull().sum() / len(df) * 100).round(2),
        'unique_values': df.nunique(),
    })
    
    # Add numeric column statistics
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    summary_stats.loc[summary_stats['column_name'].isin(numeric_cols), 'mean'] = df[numeric_cols].mean()
    summary_stats.loc[summary_stats['column_name'].isin(numeric_cols), 'std'] = df[numeric_cols].std()
    summary_stats.loc[summary_stats['column_name'].isin(numeric_cols), 'min'] = df[numeric_cols].min()
    summary_stats.loc[summary_stats['column_name'].isin(numeric_cols), 'max'] = df[numeric_cols].max()
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate output filename from input filename
    input_filename = os.path.basename(input_path)
    output_filename = f"summary_stats_{input_filename}"
    output_path = os.path.join(output_dir, output_filename)
    
    # Save summary statistics
    summary_stats.to_csv(output_path, index=False)
    print(f"Summary statistics saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python summary.py <input_path> <output_directory>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        generate_summary_stats(input_path, output_dir)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
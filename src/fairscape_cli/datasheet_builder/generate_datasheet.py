#!/usr/bin/env python3
import argparse
import sys
import os
import traceback
from rocrate.datasheet_generator import DatasheetGenerator

def main():
    parser = argparse.ArgumentParser(
        description='Generate RO-Crate datasheets and previews with support for sub-crates'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Path to top-level ro-crate-metadata.json file'
    )
    args = parser.parse_args()
    
    try:
        input_dir = os.path.dirname(args.input)
        template_dir = "./templates"
        output_path = os.path.join(input_dir, "ro-crate-datasheet.html")
        
        generator = DatasheetGenerator(
            json_path=args.input,
            template_dir=template_dir
        )
        
        generator.process_subcrates()
        
        final_output_path = generator.save_datasheet(output_path)
        print(f"Datasheet generated successfully: {final_output_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
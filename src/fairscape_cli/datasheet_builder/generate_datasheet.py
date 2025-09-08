import argparse
import sys
import os
import traceback
from pathlib import Path

from fairscape_cli.datasheet_builder.rocrate.datasheet_generator import DatasheetGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Generate RO-Crate datasheets and previews with support for sub-crates'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Path to top-level ro-crate-metadata.json file'
    )
    parser.add_argument(
        '--templates',
        default='./templates',
        help='Path to templates directory (default: ./templates)'
    )
    parser.add_argument(
        '--output',
        help='Path for output datasheet HTML (default: same dir as input)'
    )
    parser.add_argument(
        '--published',
        action='store_true',
        help='Generate published version with fairscape.net links'
    )
    
    args = parser.parse_args()
    
    try:
        input_path = Path(args.input)
        input_dir = input_path.parent
        template_dir = Path(args.templates)
        
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = input_dir / "ro-crate-datasheet.html"
        
        generator = DatasheetGenerator(
            json_path=input_path,
            template_dir=template_dir,
            published=args.published
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
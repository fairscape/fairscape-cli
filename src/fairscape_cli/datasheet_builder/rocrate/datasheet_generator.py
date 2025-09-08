"""
DatasheetGenerator orchestrates the conversion process:
1. Loads RO-Crate JSON
2. Converts to pydantic models using converters
3. Passes models to section generators to create HTML
4. Combines section HTML into final datasheet
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from jinja2 import Environment, FileSystemLoader

from fairscape_models.rocrate import ROCrateV1_2
from fairscape_models.conversion.converter import ROCToTargetConverter
from fairscape_models.conversion.models.FairscapeDatasheet import (
    FairscapeDatasheet,
    OverviewSection,
    UseCasesSection,
    DistributionSection,
    SubCrateItem,
    CompositionSection,
    Preview
)
from fairscape_models.conversion.mapping.FairscapeDatasheet import (
    OVERVIEW_MAPPING_CONFIGURATION,
    USECASES_MAPPING_CONFIGURATION,
    DISTRIBUTION_MAPPING_CONFIGURATION,
    SUBCRATE_MAPPING_CONFIGURATION,
    PREVIEW_MAPPING_CONFIGURATION
)

from .section_generators import (
    OverviewSectionGenerator,
    UseCasesSectionGenerator,
    DistributionSectionGenerator,
    SubcratesSectionGenerator,
    PreviewGenerator
)


def get_directory_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if not os.path.islink(file_path):
                total_size += os.path.getsize(file_path)
    return total_size


def format_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"


class DatasheetGenerator:
    """
    Main orchestrator for datasheet generation.
    Coordinates conversion from RO-Crate to HTML via pydantic models.
    """
    
    def __init__(self, json_path: Path, template_dir: Path, published: bool = False):
        self.json_path = Path(json_path)
        self.base_dir = self.json_path.parent
        self.template_dir = Path(template_dir)
        self.published = published
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Initialize section generators with template engine
        self.overview_generator = OverviewSectionGenerator(self.env)
        self.use_cases_generator = UseCasesSectionGenerator(self.env)
        self.distribution_generator = DistributionSectionGenerator(self.env)
        self.subcrates_generator = SubcratesSectionGenerator(self.env)
        self.preview_generator = PreviewGenerator(self.env)
        
        # Load and parse the main RO-Crate
        with open(self.json_path, 'r') as f:
            crate_dict = json.load(f)
        self.main_crate = ROCrateV1_2.model_validate(crate_dict)
        
        # Build global metadata index for cross-references
        self.global_metadata_index = {}
        self._build_initial_index()
    
    def _build_initial_index(self):
        """Build index of all entities in main crate by their guid."""
        for item in self.main_crate.metadataGraph:
            if hasattr(item, 'guid'):
                self.global_metadata_index[getattr(item, 'guid')] = item.model_dump()
    
    def _find_subcrate_paths(self) -> List[Dict[str, Any]]:
        """Find all subcrates referenced in the main crate."""
        subcrate_info = []
        
        for item in self.main_crate.metadataGraph:
            item_dict = item.model_dump()
            if 'ro-crate-metadata' in item_dict:
                metadata_path = item_dict['ro-crate-metadata']
                subcrate_info.append({
                    'id': item_dict.get('@id', ''),
                    'name': item_dict.get('name', 'Unnamed Sub-Crate'),
                    'metadata_path': metadata_path,
                    'full_path': self.base_dir / metadata_path
                })
        
        return subcrate_info
    
    def convert_main_sections(self) -> FairscapeDatasheet:
        """
        Convert main RO-Crate to datasheet sections using converters.
        Returns FairscapeDatasheet with all sections populated.
        """
        # Convert Overview section
        overview_converter = ROCToTargetConverter(
            source_crate=self.main_crate,
            mapping_configuration=OVERVIEW_MAPPING_CONFIGURATION
        )
        overview = overview_converter.convert()
        overview.published = self.published
        
        # Convert Use Cases section
        usecases_converter = ROCToTargetConverter(
            source_crate=self.main_crate,
            mapping_configuration=USECASES_MAPPING_CONFIGURATION
        )
        use_cases = usecases_converter.convert()
        
        # Convert Distribution section
        distribution_converter = ROCToTargetConverter(
            source_crate=self.main_crate,
            mapping_configuration=DISTRIBUTION_MAPPING_CONFIGURATION
        )
        distribution = distribution_converter.convert()
        
        # Process subcrates for Composition section
        subcrate_items = self._process_all_subcrates()
        composition = CompositionSection(items=subcrate_items) if subcrate_items else None
        
        return FairscapeDatasheet(
            overview=overview,
            use_cases=use_cases,
            distribution=distribution,
            composition=composition
        )
    
    def _process_all_subcrates(self) -> List[SubCrateItem]:
        """Process all subcrates and convert them to SubCrateItem models."""
        subcrate_items = []
        subcrate_info_list = self._find_subcrate_paths()
        
        for info in subcrate_info_list:
            if not info['full_path'].exists():
                print(f"Warning: Subcrate metadata file not found at {info['full_path']}")
                continue
            
            try:
                # Load subcrate
                with open(info['full_path'], 'r') as f:
                    subcrate_dict = json.load(f)
                subcrate = ROCrateV1_2.model_validate(subcrate_dict)
                
                # Add subcrate entities to global index
                for item in subcrate.metadataGraph:
                    if hasattr(item, 'guid'):
                        guid = getattr(item, 'guid')
                        self.global_metadata_index[guid] = item.model_dump()
                        if hasattr(subcrate.metadataGraph[1], 'name'):
                            self.global_metadata_index[guid]['rocrateName'] = subcrate.metadataGraph[1].name
                
                # Convert subcrate to SubCrateItem model
                converter = ROCToTargetConverter(
                    source_crate=subcrate,
                    mapping_configuration=SUBCRATE_MAPPING_CONFIGURATION,
                    global_index=self.global_metadata_index
                )
                
                subcrate_item = converter.convert()
                
                # Add computed fields
                subcrate_item.metadata_path = info['metadata_path']
                subcrate_item.published = self.published
                
                subcrate_dir = os.path.dirname(subcrate_item.metadata_path)
                subcrate_item.preview_url = f"{subcrate_dir}/ro-crate-preview.html"
                
                # Calculate size if not provided
                subcrate_dir = info['full_path'].parent
                if not subcrate_item.size and subcrate_dir.exists():
                    try:
                        dir_size = get_directory_size(str(subcrate_dir))
                        subcrate_item.size = format_size(dir_size)
                    except Exception:
                        subcrate_item.size = "Unknown"
                
                # Inherit DOI from main crate if not set
                if not subcrate_item.doi:
                    main_root = self.main_crate.metadataGraph[1].model_dump()
                    subcrate_item.doi = main_root.get('identifier')
                
                # Inherit publications from main crate if not set
                if not subcrate_item.related_publications:
                    main_root = self.main_crate.metadataGraph[1].model_dump()
                    pubs = main_root.get('associatedPublication', [])
                    if pubs:
                        subcrate_item.related_publications = pubs if isinstance(pubs, list) else [pubs]
                
                # Add statistical summary info if present
                self._enhance_subcrate_item(subcrate_item, subcrate)
                
                subcrate_items.append(subcrate_item)
                
            except Exception as e:
                print(f"Error processing subcrate {info['name']}: {e}")
                import traceback
                traceback.print_exc()
        
        return subcrate_items
    
    def _enhance_subcrate_item(self, subcrate_item: SubCrateItem, subcrate: ROCrateV1_2):
        """Add statistical summary info to subcrate item if present."""
        root_dict = subcrate.metadataGraph[1].model_dump() if len(subcrate.metadataGraph) > 1 else {}
        
        statistical_summary_ref = root_dict.get('hasSummaryStatistics')
        if statistical_summary_ref and isinstance(statistical_summary_ref, dict):
            summary_id = statistical_summary_ref.get('@id')
            for entity in subcrate.metadataGraph:
                entity_dict = entity.model_dump()
                if entity_dict.get('@id') == summary_id:
                    summary_name = entity_dict.get('name', 'Statistical Summary')
                    content_url = entity_dict.get('contentUrl')
                    
                    if content_url:
                        # Build relative path to summary file
                        if subcrate_item.metadata_path:
                            subcrate_path_prefix = os.path.dirname(subcrate_item.metadata_path)
                            path_in_subcrate = content_url
                            
                            # Clean up file:// prefixes
                            if path_in_subcrate.startswith("file:///"):
                                path_in_subcrate = path_in_subcrate[len("file:///"):]
                            elif path_in_subcrate.startswith("file://"):
                                path_in_subcrate = path_in_subcrate[len("file://"):]
                            
                            if path_in_subcrate.startswith("/"):
                                path_in_subcrate = path_in_subcrate[1:]
                            
                            if subcrate_path_prefix:
                                final_url = os.path.join(subcrate_path_prefix, path_in_subcrate)
                            else:
                                final_url = path_in_subcrate
                            
                            final_url = final_url.replace(os.sep, '/')
                            
                            subcrate_item.statistical_summary_info = {
                                'name': summary_name,
                                'url': final_url
                            }
                    break
    
    def save_datasheet(self, output_path: Optional[Path] = None) -> Path:
        """
        Generate and save the main datasheet HTML.
        
        This method:
        1. Converts RO-Crate to pydantic models
        2. Passes models to section generators to create HTML
        3. Combines section HTML using base.html template
        4. Saves final HTML to file
        """
        if output_path is None:
            output_path = self.base_dir / "ro-crate-datasheet.html"
        else:
            output_path = Path(output_path)
        
        # Step 1: Convert RO-Crate to pydantic datasheet model
        datasheet = self.convert_main_sections()
        
        # Step 2: Generate HTML for each section using section generators
        overview_html = self.overview_generator.generate(datasheet.overview, self.published)
        use_cases_html = self.use_cases_generator.generate(datasheet.use_cases)
        distribution_html = self.distribution_generator.generate(datasheet.distribution)
        subcrates_html = self.subcrates_generator.generate(datasheet.composition, self.published)
        
        # Step 3: Combine sections using base.html template
        base_template = self.env.get_template('base.html')
        
        context = {
            'title': datasheet.overview.title if datasheet.overview else "Untitled RO-Crate",
            'version': datasheet.overview.version if datasheet.overview else "",
            'overview_section': overview_html,
            'use_cases_section': use_cases_html,
            'distribution_section': distribution_html,
            'subcrates_section': subcrates_html,
            'subcrate_count': len(datasheet.composition.items) if datasheet.composition else 0
        }
        
        final_html = base_template.render(**context)
        
        # Step 4: Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        return output_path
    
    def process_subcrates(self):
        """Generate preview HTML for each subcrate."""
        subcrate_info_list = self._find_subcrate_paths()
        processed_count = 0
        
        for info in subcrate_info_list:
            if not info['full_path'].exists():
                continue
            
            try:
                # Load subcrate
                with open(info['full_path'], 'r') as f:
                    subcrate_dict = json.load(f)
                subcrate = ROCrateV1_2.model_validate(subcrate_dict)
                
                # Convert to Preview model
                converter = ROCToTargetConverter(
                    source_crate=subcrate,
                    mapping_configuration=PREVIEW_MAPPING_CONFIGURATION
                )
                
                preview = converter.convert()
                
                # Generate and save preview HTML
                preview_html = self.preview_generator.generate(preview, self.published)
                
                output_path = info['full_path'].parent / "ro-crate-preview.html"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(preview_html)
                
                processed_count += 1
                
            except Exception as e:
                print(f"Error generating preview for {info['name']}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"Finished processing subcrates. Generated {processed_count} preview files.")
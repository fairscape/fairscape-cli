import os
from .base import ROCrateProcessor
from .template_engine import TemplateEngine
from .section_generators import (
    OverviewSectionGenerator,
    UseCasesSectionGenerator,
    DistributionSectionGenerator,
    SubcratesSectionGenerator
)
from .preview_generator import PreviewGenerator


class DatasheetGenerator:
    """Main class for generating RO-Crate datasheets"""
    
    def __init__(self, json_data=None, json_path=None, template_dir=None, published = False):
        """Initialize with JSON data or a path to a JSON file"""

        self.processor = ROCrateProcessor(json_data=json_data, json_path=json_path, published=published)
        
        self.template_engine = TemplateEngine(template_dir=template_dir)
        
        self.overview_generator = OverviewSectionGenerator(self.template_engine, self.processor)
        self.use_cases_generator = UseCasesSectionGenerator(self.template_engine, self.processor)
        self.distribution_generator = DistributionSectionGenerator(self.template_engine, self.processor)
        self.subcrates_generator = SubcratesSectionGenerator(self.template_engine, self.processor)
        
        if json_path:
            self.base_dir = os.path.dirname(os.path.abspath(json_path))
        else:
            self.base_dir = os.getcwd()
    
    def generate_datasheet(self):
        """Generate the complete datasheet"""
        overview_section = self.overview_generator.generate()
        use_cases_section = self.use_cases_generator.generate()
        subcrates_section = self.subcrates_generator.generate(base_dir=self.base_dir)
        distribution_section = self.distribution_generator.generate()
        
        files, software, instruments, samples, experiments, computations, schemas, other = self.processor.categorize_items()
        files_count = len(files)
        software_count = len(software)
        instruments_count = len(instruments)
        samples_count = len(samples)
        experiments_count = len(experiments)
        computations_count = len(computations)
        schemas_count = len(schemas)
        other_count = len(other)
        
        cell_lines = self.processor.extract_cell_line_info(samples)
        species = self.processor.extract_sample_species(samples)
        experiment_types = self.processor.extract_experiment_types(experiments)
        
        subcrates = self.processor.find_subcrates()
        subcrate_count = len(subcrates)
        
        context = {
            'title': self.processor.root.get("name", "Untitled RO-Crate"),
            'version': self.processor.root.get("version", ""),
            'overview_section': overview_section,
            'use_cases_section': use_cases_section,
            'subcrates_section': subcrates_section,
            'distribution_section': distribution_section,
            'files_count': files_count,
            'software_count': software_count,
            'instruments_count': instruments_count,
            'samples_count': samples_count,
            'experiments_count': experiments_count,
            'computations_count': computations_count,
            'schemas_count': schemas_count,
            'other_count': other_count,
            'cell_lines': cell_lines,
            'species': species,
            'experiment_types': experiment_types,
            'subcrate_count': subcrate_count
        }
        
        return self.template_engine.render('base.html', **context)
    
    def save_datasheet(self, output_path=None):
        """Generate and save the datasheet to a file"""
        if output_path is None:
            output_path = os.path.join(self.base_dir, "ro-crate-datasheet.html")
        
        datasheet_html = self.generate_datasheet()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(datasheet_html)
        
        return output_path
    
    def process_subcrates(self):
        """Process all subcrates and generate HTML preview files for each."""
        subcrates = self.processor.find_subcrates()

        processed_count = 0
        for subcrate_info in subcrates:
            metadata_path = subcrate_info.get("metadata_path", "")
            if not metadata_path:
                print(f"Skipping subcrate '{subcrate_info.get('name', subcrate_info.get('id'))}' due to missing 'ro-crate-metadata' path.")
                continue

            full_path = os.path.normpath(os.path.join(self.base_dir, metadata_path))

            if not os.path.exists(full_path):
                print(f"Warning: Subcrate metadata file not found at {full_path}. Skipping.")
                continue

            try:
                subcrate_dir = os.path.dirname(full_path)
                output_path = os.path.join(subcrate_dir, "ro-crate-preview.html")

                subcrate_processor = ROCrateProcessor(json_path=full_path)
                preview_gen = PreviewGenerator(
                    processor=subcrate_processor,
                    template_engine=self.template_engine,
                    base_dir=subcrate_dir
                )
                saved_path = preview_gen.save_preview_html(output_path)

                processed_count += 1
            except Exception as e:
                import traceback
                print(f"Error processing subcrate {subcrate_info.get('name', '')} at {full_path}: {str(e)}")
                traceback.print_exc()

        print(f"Finished processing subcrates. Generated {processed_count} preview files.")
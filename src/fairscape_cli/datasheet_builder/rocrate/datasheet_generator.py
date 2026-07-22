"""
DatasheetGenerator orchestrates the conversion process:
1. Loads RO-Crate JSON
2. Converts to pydantic models using converters
3. Passes models to section generators to create HTML
4. Combines section HTML into final datasheet
"""
import json
import logging
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
from fairscape_models.conversion.mapping.subcrate_utils import enrich_preview_computations

from fairscape_cli.utils.rocrate_helpers import get_root_entity

from .section_generators import (
    OverviewSectionGenerator,
    UseCasesSectionGenerator,
    DistributionSectionGenerator,
    SubcratesSectionGenerator,
    PreviewGenerator
)
from .summary_generator import SummarySectionGenerator

logger = logging.getLogger(__name__)


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

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

        self.overview_generator = OverviewSectionGenerator(self.env)
        self.use_cases_generator = UseCasesSectionGenerator(self.env)
        self.distribution_generator = DistributionSectionGenerator(self.env)
        self.subcrates_generator = SubcratesSectionGenerator(self.env)
        self.preview_generator = PreviewGenerator(self.env)
        self.summary_generator = SummarySectionGenerator(self.env)

        with open(self.json_path, 'r') as f:
            crate_dict = json.load(f)
        self.main_crate = ROCrateV1_2.model_validate(crate_dict)
        self.main_root = get_root_entity(self.main_crate)

        self._subcrates: Optional[List[Dict[str, Any]]] = None
        self.global_metadata_index = {}
        self._build_complete_index()

    def _load_subcrates(self) -> List[Dict[str, Any]]:
        """Load and validate each subcrate's metadata once, caching the result.

        Returns a list of {'info': <subcrate path info>, 'crate': ROCrateV1_2}.
        Subcrates that are missing or fail validation are logged and skipped.
        """
        if self._subcrates is not None:
            return self._subcrates

        self._subcrates = []
        for info in self._find_subcrate_paths():
            if not info['full_path'].exists():
                logger.warning("Subcrate metadata file not found at %s", info['full_path'])
                continue

            try:
                with open(info['full_path'], 'r') as f:
                    subcrate_dict = json.load(f)
                subcrate = ROCrateV1_2.model_validate(subcrate_dict)
                self._subcrates.append({'info': info, 'crate': subcrate})
            except Exception:
                logger.error("Error loading subcrate %s", info['name'], exc_info=True)

        return self._subcrates

    def _build_complete_index(self):
        """Build index of all entities in main crate and all subcrates by their guid."""
        for item in self.main_crate.metadataGraph:
            if hasattr(item, 'guid'):
                self.global_metadata_index[getattr(item, 'guid')] = item.model_dump()

        for entry in self._load_subcrates():
            subcrate = entry['crate']
            subcrate_root = get_root_entity(subcrate)
            subcrate_name = getattr(subcrate_root, 'name', None)

            for item in subcrate.metadataGraph:
                if hasattr(item, 'guid'):
                    guid = getattr(item, 'guid')
                    self.global_metadata_index[guid] = item.model_dump()
                    if subcrate_name:
                        self.global_metadata_index[guid]['rocrateName'] = subcrate_name

    def _find_subcrate_paths(self) -> List[Dict[str, Any]]:
        """Find all subcrates referenced in the main crate."""
        subcrate_info = []

        # Get the root dataset ID to exclude it
        root_id = getattr(self.main_root, 'guid', None)

        for item in self.main_crate.metadataGraph:
            item_dict = item.model_dump()
            item_id = getattr(item, 'guid', None)

            # Skip the root dataset
            if item_id is not None and item_id == root_id:
                continue

            if 'ro-crate-metadata' in item_dict:
                metadata_path = item_dict['ro-crate-metadata']
                subcrate_info.append({
                    'id': item_id,
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
        overview_converter = ROCToTargetConverter(
            source_crate=self.main_crate,
            mapping_configuration=OVERVIEW_MAPPING_CONFIGURATION
        )
        overview = overview_converter.convert()
        overview.published = self.published

        usecases_converter = ROCToTargetConverter(
            source_crate=self.main_crate,
            mapping_configuration=USECASES_MAPPING_CONFIGURATION
        )
        use_cases = usecases_converter.convert()

        distribution_converter = ROCToTargetConverter(
            source_crate=self.main_crate,
            mapping_configuration=DISTRIBUTION_MAPPING_CONFIGURATION
        )
        distribution = distribution_converter.convert()

        subcrate_items = self._process_all_subcrates()
        if not subcrate_items:
            subcrate_items = self._build_single_crate_composition()
        composition = CompositionSection(items=subcrate_items) if subcrate_items else None

        return FairscapeDatasheet(
            overview=overview,
            use_cases=use_cases,
            distribution=distribution,
            composition=composition
        )

    def _apply_main_root_fallbacks(self, subcrate_item: SubCrateItem):
        """Fill missing DOI/publications on a subcrate item from the main crate root."""
        main_root_dict = self.main_root.model_dump() if self.main_root else {}

        if not subcrate_item.doi:
            subcrate_item.doi = main_root_dict.get('identifier')

        if not subcrate_item.related_publications:
            pubs = main_root_dict.get('associatedPublication', [])
            if pubs:
                subcrate_item.related_publications = pubs if isinstance(pubs, list) else [pubs]

    def _process_all_subcrates(self) -> List[SubCrateItem]:
        """Process all subcrates and convert them to SubCrateItem models."""
        subcrate_items = []

        for entry in self._load_subcrates():
            info = entry['info']
            subcrate = entry['crate']

            try:
                converter = ROCToTargetConverter(
                    source_crate=subcrate,
                    mapping_configuration=SUBCRATE_MAPPING_CONFIGURATION,
                    global_index=self.global_metadata_index
                )

                subcrate_item = converter.convert()

                subcrate_item.metadata_path = info['metadata_path']
                subcrate_item.published = self.published

                subcrate_dir = os.path.dirname(subcrate_item.metadata_path)
                subcrate_item.preview_url = f"{subcrate_dir}/ro-crate-preview.html"

                subcrate_dir = info['full_path'].parent
                if not subcrate_item.size and subcrate_dir.exists():
                    try:
                        dir_size = get_directory_size(str(subcrate_dir))
                        subcrate_item.size = format_size(dir_size)
                    except Exception:
                        subcrate_item.size = "Unknown"

                self._apply_main_root_fallbacks(subcrate_item)

                self._enhance_subcrate_item(subcrate_item, subcrate)

                subcrate_items.append(subcrate_item)

            except Exception:
                logger.error("Error processing subcrate %s", info['name'], exc_info=True)

        return subcrate_items

    def _build_single_crate_composition(self) -> List[SubCrateItem]:
        """When no subcrates exist, treat the main crate itself as a single subcrate."""
        try:
            converter = ROCToTargetConverter(
                source_crate=self.main_crate,
                mapping_configuration=SUBCRATE_MAPPING_CONFIGURATION,
                global_index=self.global_metadata_index
            )
            subcrate_item = converter.convert()
            subcrate_item.published = self.published
            subcrate_item.preview_url = ""

            if not subcrate_item.size and self.base_dir.exists():
                try:
                    dir_size = get_directory_size(str(self.base_dir))
                    subcrate_item.size = format_size(dir_size)
                except Exception:
                    subcrate_item.size = "Unknown"

            self._apply_main_root_fallbacks(subcrate_item)

            self._enhance_subcrate_item(subcrate_item, self.main_crate)

            return [subcrate_item]
        except Exception:
            logger.error("Error building single crate composition", exc_info=True)
            return []

    def _enhance_subcrate_item(self, subcrate_item: SubCrateItem, subcrate: ROCrateV1_2):
        """Add statistical summary info to subcrate item if present."""
        subcrate_root = get_root_entity(subcrate)
        root_dict = subcrate_root.model_dump() if subcrate_root else {}

        statistical_summary_ref = root_dict.get('hasSummaryStatistics')
        if statistical_summary_ref and isinstance(statistical_summary_ref, dict):
            summary_id = statistical_summary_ref.get('@id')
            for entity in subcrate.metadataGraph:
                entity_dict = entity.model_dump()
                if entity_dict.get('@id') == summary_id:
                    summary_name = entity_dict.get('name', 'Statistical Summary')
                    content_url = entity_dict.get('contentUrl')

                    if content_url:
                        if subcrate_item.metadata_path:
                            subcrate_path_prefix = os.path.dirname(subcrate_item.metadata_path)
                            path_in_subcrate = content_url

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

        datasheet = self.convert_main_sections()

        summary_html = self.summary_generator.generate(self.main_crate, output_dir=self.base_dir)

        overview_html = self.overview_generator.generate(datasheet.overview, self.published)
        use_cases_html = self.use_cases_generator.generate(datasheet.use_cases)
        distribution_html = self.distribution_generator.generate(datasheet.distribution)
        subcrates_html = self.subcrates_generator.generate(datasheet.composition, self.published)

        base_template = self.env.get_template('base.html')

        subcrate_nav = []
        if datasheet.composition and datasheet.composition.items:
            for item in datasheet.composition.items:
                subcrate_nav.append({'name': item.name or 'Unnamed Sub-Crate'})

        overview = datasheet.overview
        context = {
            'title': overview.title if overview else "Untitled RO-Crate",
            'version': overview.version if overview else "",
            'doi': overview.doi if overview else None,
            'license_value': overview.license_value if overview else None,
            'release_date': overview.release_date if overview else None,
            'content_size': overview.content_size if overview else None,
            'summary_section': summary_html,
            'overview_section': overview_html,
            'use_cases_section': use_cases_html,
            'distribution_section': distribution_html,
            'subcrates_section': subcrates_html,
            'subcrate_count': len(datasheet.composition.items) if datasheet.composition else 0,
            'subcrates': subcrate_nav
        }

        final_html = base_template.render(**context)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)

        return output_path

    def process_subcrates(self):
        """Generate preview HTML for each subcrate."""
        processed_count = 0

        for entry in self._load_subcrates():
            info = entry['info']
            subcrate = entry['crate']

            try:
                converter = ROCToTargetConverter(
                    source_crate=subcrate,
                    mapping_configuration=PREVIEW_MAPPING_CONFIGURATION
                )

                preview = converter.convert()
                enrich_preview_computations(preview, subcrate, self.global_metadata_index)

                preview_html = self.preview_generator.generate(preview, self.published)

                output_path = info['full_path'].parent / "ro-crate-preview.html"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(preview_html)

                processed_count += 1

            except Exception:
                logger.error("Error generating preview for %s", info['name'], exc_info=True)

        logger.info("Finished processing subcrates. Generated %d preview files.", processed_count)

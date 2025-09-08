"""
Section generators convert pydantic models to HTML.
Each generator:
1. Takes a pydantic model (e.g., OverviewSection)
2. Extracts and transforms fields for template consumption
3. Renders the appropriate template with the context
4. Returns HTML string
"""
from typing import Dict, Any, List, Optional
from jinja2 import Environment

from fairscape_models.conversion.models.FairscapeDatasheet import (
    OverviewSection,
    UseCasesSection,
    DistributionSection,
    SubCrateItem,
    CompositionSection,
    Preview
)


class SectionGenerator:
    """Base class for all section generators."""
    
    def __init__(self, template_engine: Environment):
        self.template_engine = template_engine
    
    def generate(self, template_name: str, **context) -> str:
        """Render a template with the given context."""
        template = self.template_engine.get_template(template_name)
        return template.render(**context)


class OverviewSectionGenerator(SectionGenerator):
    """Convert OverviewSection pydantic model to HTML."""
    
    def generate(self, overview: Optional[OverviewSection], published: bool = False) -> str:
        if not overview:
            return ""
        
        # Extract fields from pydantic model and transform for template
        context = {
            # Core identity
            'title': overview.title or "Untitled RO-Crate",
            'description': overview.description or "",
            'id_value': overview.id_value or "",
            'doi': overview.doi or "",
            'license_value': overview.license_value or "",
            'ethical_review': overview.ethical_review or "",
            
            # Dates
            'release_date': overview.release_date or "",
            'created_date': overview.created_date or "",
            'updated_date': overview.updated_date or "",
            
            # People/orgs - convert lists to strings
            'authors': ', '.join(overview.authors) if overview.authors else "",
            'publisher': overview.publisher or "",
            'principal_investigator': overview.principal_investigator or "",
            'contact_email': overview.contact_email or "",
            
            # Legal/policy
            'copyright': overview.copyright or "",
            'terms_of_use': overview.terms_of_use or "",
            'confidentiality_level': overview.confidentiality_level or "",
            'citation': overview.citation or "",
            
            # Versioning/misc
            'version': overview.version or "",
            'content_size': overview.content_size or "",
            'funding': ', '.join(overview.funding) if overview.funding else "",
            'keywords': overview.keywords or [],  # Keep as list for template
            'completeness': overview.completeness or "",
            
            # Human subjects & governance
            'human_subject': overview.human_subject or "",
            'human_subject_research': overview.human_subject_research or "No",
            'human_subject_exemptions': overview.human_subject_exemptions or "N/A",
            'deidentified_samples': overview.deidentified_samples or "Yes",
            'fda_regulated': overview.fda_regulated or "No",
            'irb': overview.irb or "N/A",
            'irb_protocol_id': overview.irb_protocol_id or "N/A",
            'data_governance': overview.data_governance or "",
            
            # Related publications - keep as list
            'related_publications': overview.related_publications or [],
            
            # Published flag for links
            'published': published
        }
        
        return super().generate('sections/overview.html', **context)


class UseCasesSectionGenerator(SectionGenerator):
    """Convert UseCasesSection pydantic model to HTML."""
    
    def generate(self, use_cases: Optional[UseCasesSection]) -> str:
        if not use_cases:
            return ""
        
        context = {
            'intended_uses': use_cases.intended_use or "",
            'limitations': use_cases.limitations or "",
            'prohibited_uses': use_cases.prohibited_uses or "",
            'maintenance_plan': use_cases.maintenance_plan or "",
            'potential_bias': use_cases.potential_sources_of_bias or ""
        }
        
        return super().generate('sections/use_cases.html', **context)


class DistributionSectionGenerator(SectionGenerator):
    """Convert DistributionSection pydantic model to HTML."""
    
    def generate(self, distribution: Optional[DistributionSection]) -> str:
        if not distribution:
            return ""
        
        context = {
            'license_value': distribution.license_value or "",
            'publisher': distribution.publisher or "",
            'host': "",  # Not in current model but kept for template compatibility
            'doi': distribution.doi or "",
            'release_date': distribution.release_date or "",
            'version': distribution.version or ""
        }
        
        return super().generate('sections/distribution.html', **context)


class SubcratesSectionGenerator(SectionGenerator):
    """Convert CompositionSection (list of SubCrateItems) to HTML."""
    
    def generate(self, composition: Optional[CompositionSection], published: bool = False) -> str:
        if not composition or not composition.items:
            return ""
        
        subcrates_data = []
        
        for item in composition.items:
            subcrate_context = self._prepare_subcrate_context(item, published)
            subcrates_data.append(subcrate_context)
        
        context = {
            'subcrates': subcrates_data,
            'subcrate_count': len(subcrates_data)
        }
        
        return super().generate('sections/subcrates.html', **context)
    
    def _prepare_subcrate_context(self, item: SubCrateItem, published: bool) -> Dict[str, Any]:
        """Convert a SubCrateItem to template context."""
        context = {
            # Basic info
            'name': item.name,
            'id': item.id,
            'description': item.description or "",
            'authors': item.authors or "",
            'keywords': item.keywords or [],
            'metadata_path': item.metadata_path or "",
            'size': item.size or "Unknown",
            
            # High-level metadata
            'doi': item.doi or "",
            'date': item.date or "",
            'contact': item.contact or "",
            'published': published,
            
            # Policy/legal
            'copyright': item.copyright or "",
            'license': item.license or "",
            'terms_of_use': item.terms_of_use or "",
            'confidentiality': item.confidentiality or "",
            'funder': item.funder or "",
            'md5': item.md5 or "",
            'evidence': item.evidence or "",
            
            # Publications
            'related_publications': item.related_publications or [],
            
            # Statistical summary
            'statistical_summary_info': item.statistical_summary_info,
            
            #Link 
            'preview_url': item.preview_url or "",
            
            # Initialize empty lists for compatibility
            'files': [],
            'software': [],
            'instruments': [],
            'samples': [],
            'experiments': [],
            'computations': [],
            'schemas': [],
            'other': []
        }
        
        # Unpack composition details if present
        if item.composition_details:
            details = item.composition_details
            context.update({
                # Counts
                'files_count': details.files_count,
                'software_count': details.software_count,
                'instruments_count': details.instruments_count,
                'samples_count': details.samples_count,
                'experiments_count': details.experiments_count,
                'computations_count': details.computations_count,
                'schemas_count': details.schemas_count,
                'other_count': details.other_count,
                
                # Format and access summaries - convert to dict for template
                'file_formats': dict(details.file_formats) if details.file_formats else {},
                'software_formats': dict(details.software_formats) if details.software_formats else {},
                'file_access': dict(details.file_access) if details.file_access else {},
                'software_access': dict(details.software_access) if details.software_access else {},
                
                # Patterns
                'computation_patterns': details.computation_patterns or [],
                'experiment_patterns': details.experiment_patterns or [],
                
                # Inputs
                'input_datasets': dict(details.input_datasets) if details.input_datasets else {},
                'input_datasets_count': details.input_datasets_count,
                'inputs_count': details.inputs_count,
                
                # Domain-specific
                'cell_lines': details.cell_lines or {},
                'species': details.species or [],
                'experiment_types': details.experiment_types or []
            })
        
        return context


class PreviewGenerator(SectionGenerator):
    """Convert Preview pydantic model to HTML."""
    
    DESCRIPTION_TRUNCATE_LENGTH = 100
    
    def generate(self, preview: Preview, published: bool = False) -> str:
        if not preview:
            return ""
        
        context = {
            # Core metadata
            'title': preview.title or "Untitled RO-Crate",
            'id_value': preview.id_value or "",
            'version': preview.version or "",
            'description': preview.description or "",
            'doi': preview.doi or "",
            'license_value': preview.license_value or "",
            
            # Dates
            'release_date': preview.release_date or "",
            'created_date': preview.created_date or "",
            'updated_date': preview.updated_date or "",
            
            # People/orgs
            'authors': preview.authors or "",
            'publisher': preview.publisher or "",
            'principal_investigator': preview.principal_investigator or "",
            'contact_email': preview.contact_email or "",
            'confidentiality_level': preview.confidentiality_level or "",
            
            # Misc
            'keywords': preview.keywords or [],
            'citation': preview.citation or "",
            'related_publications': preview.related_publications or [],
            
            # Published flag
            'published': published,
            
            # Statistical summary
            'statistical_summary_info': None
        }
        
        # Build statistical summary info if present
        if preview.statistical_summary_name and preview.statistical_summary_url:
            context['statistical_summary_info'] = {
                'name': preview.statistical_summary_name,
                'url': preview.statistical_summary_url
            }
        
        # Process item collections
        context['datasets'] = self._prepare_items(preview.datasets)
        context['software'] = self._prepare_items(preview.software)
        context['computations'] = self._prepare_items(preview.computations)
        context['samples'] = self._prepare_items(preview.samples)
        context['experiments'] = self._prepare_items(preview.experiments)
        context['instruments'] = self._prepare_items(preview.instruments)
        context['schemas'] = self._prepare_items(preview.schemas)
        context['other_items'] = self._prepare_items(preview.other_items)
        
        return super().generate('preview.html', **context)
    
    def _prepare_items(self, items: List) -> List[Dict[str, Any]]:
        """Convert list of PreviewItems to template context."""
        prepared = []
        for item in items:
            item_context = {
                'id': item.id or "",
                'name': item.name or "Unnamed Item",
                'description': item.description or "",
                'description_display': self._truncate_description(item.description),
                'type': item.type or "Unknown",
                'date': item.date or "N/A",
                'identifier': item.identifier or item.id or "",
                'content_status': item.content_status or "Not specified",
                'experimentType': getattr(item, 'experimentType', None) or "N/A",
                'manufacturer': getattr(item, 'manufacturer', None) or "N/A",
                'schema_properties': getattr(item, 'schema_properties', None)
            }
            prepared.append(item_context)
        return prepared
    
    def _truncate_description(self, description: Optional[str]) -> str:
        """Truncate description for display."""
        if not description:
            return ""
        if len(description) <= self.DESCRIPTION_TRUNCATE_LENGTH:
            return description
        return description[:self.DESCRIPTION_TRUNCATE_LENGTH] + "..."
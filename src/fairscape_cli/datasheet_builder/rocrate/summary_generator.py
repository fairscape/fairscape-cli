"""
Summary section generator for datasheet.
Generates the executive summary with AI-Readiness score.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from jinja2 import Environment

from fairscape_models.rocrate import ROCrateV1_2
from fairscape_models.conversion.mapping.AIReady import score_rocrate
from fairscape_models.conversion.models.AIReady import AIReadyScore


@dataclass
class SummaryData:
    """Data extracted from RO-Crate for the summary section."""
    name: str
    description: str
    total_size_formatted: str = ""
    total_entities: int = 0
    dataset_count: int = 0
    computation_count: int = 0
    software_count: int = 0
    formats: List[str] = field(default_factory=list)


@dataclass
class AIReadyCategory:
    """A single AI-Ready score category."""
    label: str
    earned: int
    possible: int
    percentage: float
    color: str


@dataclass
class AIReadyScoreData:
    """AI-Ready score data for visualization."""
    categories: List[AIReadyCategory]
    total_earned: int
    total_possible: int
    total_percentage: float
    total_color: str


class SummarySectionGenerator:
    """Generate the executive summary section with AI-Readiness score."""

    CATEGORY_MAP = {
        "fairness": ("Fairness", ["findable", "accessible", "interoperable", "reusable"]),
        "provenance": ("Provenance", ["transparent", "traceable", "interpretable", "key_actors_identified"]),
        "characterization": ("Characterization", ["semantics", "statistics", "standards", "potential_sources_of_bias", "data_quality"]),
        "pre_model_explainability": ("Explainability", ["data_documentation_template", "fit_for_purpose", "verifiable"]),
        "ethics": ("Ethics", ["ethically_acquired", "ethically_managed", "ethically_disseminated", "secure"]),
        "sustainability": ("Sustainability", ["persistent", "domain_appropriate", "well_governed", "associated"]),
        "computability": ("Computability", ["standardized", "computationally_accessible", "portable", "contextualized"]),
    }

    def __init__(self, template_engine: Environment):
        self.template_engine = template_engine

    @staticmethod
    def _get_color(percentage: float) -> str:
        """Return color based on percentage score."""
        if percentage >= 75:
            return "#4CAF50"  
        elif percentage >= 50:
            return "#8BC34A" 
        elif percentage >= 25:
            return "#FFC107" 
        return "#f44336"  

    def extract_summary_data(self, crate: ROCrateV1_2) -> SummaryData:
        """Extract summary statistics from an RO-Crate."""
        root_data = crate.metadataGraph[1].model_dump(by_alias=True) if len(crate.metadataGraph) > 1 else {}
        
        
        size_str = root_data.get("contentSize", "")
        if not size_str:
            size_bytes = root_data.get("evi:totalContentSizeBytes", 0)
            if size_bytes:
                size_str = self._format_size(size_bytes)

        formats = root_data.get("evi:formats", [])
        formats = [f for f in formats if f and f != "unknown"]

        return SummaryData(
            name=root_data.get("name", "Unnamed Dataset"),
            description=root_data.get("description", ""),
            total_size_formatted=size_str,
            total_entities=root_data.get("evi:totalEntities", 0),
            dataset_count=root_data.get("evi:datasetCount", 0),
            computation_count=root_data.get("evi:computationCount", 0),
            software_count=root_data.get("evi:softwareCount", 0),
            formats=formats
        )

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        if size_bytes >= 1e12:
            return f"{size_bytes / 1e12:.1f} TB"
        elif size_bytes >= 1e9:
            return f"{size_bytes / 1e9:.1f} GB"
        elif size_bytes >= 1e6:
            return f"{size_bytes / 1e6:.1f} MB"
        elif size_bytes >= 1e3:
            return f"{size_bytes / 1e3:.1f} KB"
        return f"{size_bytes} B"

    def compute_aiready_score(self, crate: ROCrateV1_2) -> Tuple[AIReadyScoreData, AIReadyScore]:
        """Compute AI-Ready score from an RO-Crate.

        Returns:
            Tuple of (AIReadyScoreData for visualization, AIReadyScore raw pydantic model)
        """
        crate_dict = {
            "@context": crate.context,
            "@graph": [entity.model_dump(by_alias=True) for entity in crate.metadataGraph]
        }
        raw_score = score_rocrate(crate_dict)

        categories = []
        total_earned = 0
        total_possible = 0

        for cat_key, (label, subcriteria) in self.CATEGORY_MAP.items():
            cat_score = getattr(raw_score, cat_key)
            earned = sum(1 for sc in subcriteria if getattr(cat_score, sc).has_content)
            possible = len(subcriteria)
            percentage = (earned / possible * 100) if possible > 0 else 0

            categories.append(AIReadyCategory(
                label=label,
                earned=earned,
                possible=possible,
                percentage=round(percentage, 1),
                color=self._get_color(percentage)
            ))

            total_earned += earned
            total_possible += possible

        total_percentage = (total_earned / total_possible * 100) if total_possible > 0 else 0

        score_data = AIReadyScoreData(
            categories=categories,
            total_earned=total_earned,
            total_possible=total_possible,
            total_percentage=round(total_percentage, 1),
            total_color=self._get_color(total_percentage)
        )

        return score_data, raw_score

    def save_aiready_score(self, raw_score: AIReadyScore, output_path: Path) -> None:
        """Save the AI-Ready score to a JSON file."""
        score_dict = raw_score.model_dump()
        with open(output_path, 'w') as f:
            json.dump(score_dict, f, indent=2)

    def generate(self, crate: ROCrateV1_2, output_dir: Optional[Path] = None) -> str:
        """Generate the summary section HTML.

        Args:
            crate: The RO-Crate to generate summary for
            output_dir: Directory to save ai_ready_score.json (optional)

        Returns:
            HTML string for the summary section
        """
        summary = self.extract_summary_data(crate)
        score_data, raw_score = self.compute_aiready_score(crate)

        aiready_json_path = None
        if output_dir:
            aiready_json_path = output_dir / "ai_ready_score.json"
            self.save_aiready_score(raw_score, aiready_json_path)

        desc = summary.description
        if len(desc) > 500:
            desc = desc[:500].rsplit(" ", 1)[0] + "..."

        formats_str = ", ".join(sorted(summary.formats)[:10])
        if len(summary.formats) > 10:
            formats_str += f" (+{len(summary.formats) - 10} more)"

        context = {
            'description': desc,
            'total_size': summary.total_size_formatted,
            'total_entities': f"{summary.total_entities:,}" if summary.total_entities else "N/A",
            'formats': formats_str,
            'dataset_count': f"{summary.dataset_count:,}" if summary.dataset_count else "0",
            'computation_count': f"{summary.computation_count:,}" if summary.computation_count else "0",
            'software_count': f"{summary.software_count:,}" if summary.software_count else "0",
            'aiready_categories': [
                {
                    'label': cat.label,
                    'earned': cat.earned,
                    'possible': cat.possible,
                    'percentage': cat.percentage,
                    'color': cat.color
                }
                for cat in score_data.categories
            ],
            'aiready_total_percentage': score_data.total_percentage,
            'aiready_total_color': score_data.total_color,
            'aiready_json_filename': "ai_ready_score.json" if output_dir else None
        }

        template = self.template_engine.get_template('sections/summary.html')
        return template.render(**context)

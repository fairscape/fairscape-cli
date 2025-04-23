from pydantic import BaseModel
import json
import pathlib
from datetime import datetime
import os
from typing import List, Optional, Dict, Any

import requests
import xml.etree.ElementTree as ET

# Official Fairscape Models
from fairscape_models.sample import Sample
from fairscape_models.experiment import Experiment
from fairscape_models.instrument import Instrument
from fairscape_models.dataset import Dataset

# Internal models for parsing NCBI structure before conversion
class InternalSample(BaseModel):
    accession: str
    title: Optional[str] = None
    scientific_name: Optional[str] = None
    taxon_id: Optional[str] = None
    attributes: Dict[str, str] = {}
    study_accession: Optional[str] = None
    study_center_name: Optional[str] = None
    study_title: Optional[str] = None
    study_abstract: Optional[str] = None
    study_description: Optional[str] = None

class InternalExperiment(BaseModel):
    accession: str
    title: Optional[str] = None
    study_ref: Optional[str] = None
    sample_ref: Optional[str] = None
    library_name: Optional[str] = None
    library_strategy: Optional[str] = None
    library_source: Optional[str] = None
    library_selection: Optional[str] = None
    library_layout: Optional[str] = None
    nominal_length: Optional[str] = None
    platform_type: Optional[str] = None
    instrument_model: Optional[str] = None

# Keep original Project, Output models as they represent NCBI structure
class Project(BaseModel):
    id: str
    accession: str
    archive: Optional[str] = None
    organism_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    release_date: Optional[str] = None
    target_capture: Optional[str] = None
    target_material: Optional[str] = None
    target_sample_scope: Optional[str] = None
    organism_species: Optional[str] = None
    organism_taxID: Optional[str] = None
    organism_supergroup: Optional[str] = None
    method: Optional[str] = None
    data_types: List[str] = []
    project_data_type: Optional[str] = None
    submitted_date: Optional[str] = None
    organization_role: Optional[str] = None
    organization_type: Optional[str] = None
    organization_name: Optional[str] = None
    access: Optional[str] = None

class OutputFile(BaseModel):
    filename: str
    size: Optional[int] = None
    date: Optional[str] = None
    url: str
    md5: Optional[str] = None

class Output(BaseModel):
    accession: str
    title: Optional[str] = None
    experiment_ref: Optional[str] = None
    total_spots: Optional[int] = None
    total_bases: Optional[int] = None
    size: Optional[int] = None
    published: Optional[str] = None
    files: List[OutputFile] = []
    nreads: Optional[int] = None
    nspots: Optional[int] = None
    a_count: Optional[int] = None
    c_count: Optional[int] = None
    g_count: Optional[int] = None
    t_count: Optional[int] = None
    n_count: Optional[int] = None

# Wrapper classes using Internal types for parsing
class Samples(BaseModel):
    items: List[InternalSample]

class Experiments(BaseModel):
    items: List[InternalExperiment]

class Outputs(BaseModel):
    items: List[Output]

from fairscape_cli.data_fetcher.cell_line_api import get_cell_line_entity
from fairscape_cli.data_fetcher.bioproject_fetcher import fetch_bioproject_data

from fairscape_cli.models.rocrate import GenerateROCrate, AppendCrate
from fairscape_cli.models.dataset import GenerateDataset
from fairscape_cli.models.experiment import GenerateExperiment
from fairscape_cli.models.instrument import GenerateInstrument
from fairscape_cli.models.sample import GenerateSample


class GenomicData(BaseModel):
    project: Project
    samples: Samples 
    experiments: Experiments 
    outputs: Outputs

    def to_rocrate(
        self,
        output_dir: str,
        author: str = "Unknown",
        crate_name: Optional[str] = None,
        crate_description: Optional[str] = None,
        crate_keywords: Optional[List[str]] = None,
        crate_license: Optional[str] = None,
        crate_version: Optional[str] = None,
        organization_name: Optional[str] = None,
        project_name: Optional[str] = None,
        **kwargs
    ) -> str:
        output_path = pathlib.Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        bioproject = self.project

        default_crate_name = crate_name if crate_name else bioproject.title
        default_crate_description = crate_description if crate_description else bioproject.description

        default_crate_keywords = ["bioproject", "bioinformatics"]
        if bioproject.organism_name:
            default_crate_keywords.append(bioproject.organism_name)
        default_crate_keywords.extend([dt.replace('e', '') for dt in bioproject.data_types])
        if bioproject.project_data_type:
            default_crate_keywords.append(bioproject.project_data_type)
        final_crate_keywords = crate_keywords if crate_keywords is not None else default_crate_keywords

        rocrate_params = {
            "path": output_path,
            "guid": "",
            "name": default_crate_name,
            "description": default_crate_description,
            "keywords": final_crate_keywords,
            "license": crate_license if crate_license else "https://creativecommons.org/publicdomain/zero/1.0/",
            "author": author,
            "version": crate_version if crate_version else "1.0",
            "organizationName": organization_name if organization_name else bioproject.organization_name,
            "projectName": project_name if project_name else None,
            "datePublished": datetime.now().isoformat(),
            "associatedPublication": "",
            "isPartOf": [],
            "hasPart": [],
            "sameAs": f"https://www.ncbi.nlm.nih.gov/bioproject/{bioproject.accession}"
        }
        rocrate_params.update(kwargs)
        rocrate_params = {k: v for k, v in rocrate_params.items() if v is not None}

        crate_root_dict = GenerateROCrate(**rocrate_params)
        crate_root_guid = crate_root_dict['@id']

        all_elements_to_append = []
        id_mapping = {}
        instrument_guids = {}

        experiment_fairscape_objects: Dict[str, Experiment] = {}

        cell_line_entities_to_add = {}
        for sample_spec in self.samples.items:
            accession = sample_spec.accession
            cell_line = None
            for attr_name in ['cell_line', 'cell line', 'cell_line_name']:
                if attr_name in sample_spec.attributes:
                    cell_line = sample_spec.attributes[attr_name]
                    break

            cell_line_guid = None
            if cell_line and cell_line not in cell_line_entities_to_add:
                 try:
                     cell_line_entity = get_cell_line_entity(cell_line)
                     if cell_line_entity:
                         cell_line_guid = cell_line_entity["@id"]
                         cell_line_entities_to_add[cell_line] = cell_line_entity
                 except Exception as e:
                     print(f"Warning: Failed to get cell line entity for {cell_line}: {e}")
            elif cell_line in cell_line_entities_to_add:
                cell_line_guid = cell_line_entities_to_add[cell_line]["@id"]

            sample_keywords = ["biosample", sample_spec.scientific_name]
            if cell_line:
                sample_keywords.append(cell_line)

            # Map InternalSample fields to GenerateSample arguments
            sample_params = {
                "guid": None,
                "name": sample_spec.title or f"BioSample {accession}",
                "author": author,
                "description": sample_spec.title or f"BioSample {accession} from project {bioproject.accession}",
                "keywords": sample_keywords,
                "version": "1.0",
                "contentUrl": f"https://www.ncbi.nlm.nih.gov/biosample/{accession}",
                "cellLineReference":  cell_line_guid if cell_line_guid else None,
                "additionalProperty": [
                    {"@type": "PropertyValue", "name": "NCBI BioSample Accession", "value": accession},
                    {"@type": "PropertyValue", "name": "NCBI Taxon ID", "value": sample_spec.taxon_id},
                    {"@type": "PropertyValue", "name": "Scientific Name", "value": sample_spec.scientific_name},
                ]
            }
            sample_params = {k: v for k, v in sample_params.items() if v is not None}

            generated_sample: Sample = GenerateSample(**sample_params)
            all_elements_to_append.append(generated_sample)
            id_mapping[accession] = generated_sample.guid

        all_elements_to_append.extend(cell_line_entities_to_add.values())


        for experiment_spec in self.experiments.items:
            exp_accession = experiment_spec.accession
            platform = experiment_spec.platform_type
            model = experiment_spec.instrument_model
            instrument_key = f"{platform}_{model}"

            if instrument_key not in instrument_guids:
                # Map InternalExperiment fields to GenerateInstrument arguments
                instrument_params = {
                    "guid": None,
                    "name": model,
                    "manufacturer": platform,
                    "model": model,
                    "description": f"{model} instrument ({platform}) used for sequencing",
                    "usedByExperiment": []
                }

                generated_instrument: Instrument = GenerateInstrument(**instrument_params)
                all_elements_to_append.append(generated_instrument)
                instrument_guids[instrument_key] = generated_instrument.guid

            instrument_guid = instrument_guids[instrument_key]

            sample_guid = id_mapping.get(experiment_spec.sample_ref)
            used_samples_list = [{"@id": sample_guid}] if sample_guid else []

            exp_keywords = ["experiment", experiment_spec.library_strategy, experiment_spec.library_source]

            # Map InternalExperiment fields to GenerateExperiment arguments
            exp_params = {
                "guid": None,
                "name": experiment_spec.title or f"Experiment {exp_accession}",
                "experimentType": experiment_spec.library_strategy,
                "runBy": author,
                "description": experiment_spec.title or f"Sequencing experiment {exp_accession}",
                "datePerformed": datetime.now().isoformat(),
                "keywords": exp_keywords,
                "usedInstrument": [{"@id": instrument_guid}] if instrument_guid else [],
                "usedSample": used_samples_list,
                "generated": [],
                "additionalProperty": [
                    {"@type": "PropertyValue", "name": "NCBI SRA Experiment Accession", "value": exp_accession},
                    {"@type": "PropertyValue", "name": "Library Name", "value": experiment_spec.library_name},
                    {"@type": "PropertyValue", "name": "Library Strategy", "value": experiment_spec.library_strategy},
                    {"@type": "PropertyValue", "name": "Library Source", "value": experiment_spec.library_source},
                    {"@type": "PropertyValue", "name": "Library Selection", "value": experiment_spec.library_selection},
                    {"@type": "PropertyValue", "name": "Library Layout", "value": experiment_spec.library_layout},
                    {"@type": "PropertyValue", "name": "Nominal Length", "value": experiment_spec.nominal_length},
                ]
            }
            exp_params = {k: v for k, v in exp_params.items() if v is not None and v != ""}

            generated_experiment: Experiment = GenerateExperiment(**exp_params)
            all_elements_to_append.append(generated_experiment)
            id_mapping[exp_accession] = generated_experiment.guid
            experiment_fairscape_objects[exp_accession] = generated_experiment # Store official model

        generated_output_datasets = []
        for output_spec in self.outputs.items:
            run_accession = output_spec.accession
            experiment_guid = id_mapping.get(output_spec.experiment_ref)

            dataset_params = {
                "guid": None,
                "name": output_spec.title or f"SRA Run {run_accession}",
                "author": author,
                "description": f"Sequencing run {run_accession} from experiment {output_spec.experiment_ref}",
                "keywords": ["SRA Run", "sequencing data"],
                "datePublished": output_spec.published if output_spec.published else datetime.now().isoformat(),
                "version": "1.0",
                "format": "sra",
                "generatedBy": experiment_guid if experiment_guid else [],
                "contentUrl": f"https://www.ncbi.nlm.nih.gov/sra/{run_accession}",
                 "additionalProperty": [
                    {"@type": "PropertyValue", "name": "NCBI SRA Run Accession", "value": run_accession},
                    {"@type": "PropertyValue", "name": "Total Spots", "value": str(output_spec.total_spots)},
                    {"@type": "PropertyValue", "name": "Total Bases", "value": str(output_spec.total_bases)},
                    {"@type": "PropertyValue", "name": "Size (bytes)", "value": str(output_spec.size)},
                ]
            }
            dataset_params = {k: v for k, v in dataset_params.items() if v is not None and v != ""}

            generated_dataset: Dataset = GenerateDataset(**dataset_params)
            generated_output_datasets.append(generated_dataset)
            id_mapping[run_accession] = generated_dataset.guid

            if output_spec.experiment_ref in experiment_fairscape_objects:
                exp_obj = experiment_fairscape_objects[output_spec.experiment_ref]
                if not exp_obj.generated:
                    exp_obj.generated = []
                exp_obj.generated.append({"@id": generated_dataset.guid})


        all_elements_to_append.extend(generated_output_datasets)


        models_to_append = [elem for elem in all_elements_to_append if hasattr(elem, 'model_dump')]
        dicts_to_append = [elem for elem in all_elements_to_append if not hasattr(elem, 'model_dump')]

        if models_to_append:
             AppendCrate(cratePath=output_path, elements=models_to_append)

        if dicts_to_append:
            metadata_file_path = output_path / "ro-crate-metadata.json"
            with metadata_file_path.open("r+") as f:
                crate_json = json.load(f)
                existing_ids = {item.get("@id") for item in crate_json["@graph"]}
                root_dataset_node = crate_json["@graph"][1]

                for entity_dict in dicts_to_append:
                    entity_id = entity_dict.get("@id")
                    if entity_id and entity_id not in existing_ids:
                        crate_json["@graph"].append(entity_dict)
                        existing_ids.add(entity_id)
                        if not any(part.get("@id") == entity_id for part in root_dataset_node.get("hasPart",[])):
                             if "hasPart" not in root_dataset_node: root_dataset_node["hasPart"] = []
                             root_dataset_node["hasPart"].append({"@id": entity_id})

                f.seek(0)
                json.dump(crate_json, f, indent=2)
                f.truncate()


        metadata_file_path = output_path / "ro-crate-metadata.json"
        with metadata_file_path.open("r+") as f:
            crate_json_final = json.load(f)
            graph = crate_json_final["@graph"]
            updated = False
            for i, item in enumerate(graph):
                item_id = item.get("@id")
                matching_exp_obj = next((exp for acc, exp in experiment_fairscape_objects.items() if exp.guid == item_id and exp.generated), None)
                if matching_exp_obj:
                    graph[i]["generated"] = [gen for gen in matching_exp_obj.generated]
                    updated = True

            if updated:
                f.seek(0)
                json.dump(crate_json_final, f, indent=2)
                f.truncate()


        return crate_root_guid

    @classmethod
    def from_api(cls, accession: str, api_key: str = "", details_dir: str = "details") -> 'GenomicData':
        data = fetch_bioproject_data(accession, api_key=api_key, details_dir=details_dir)
        if not data:
            raise ValueError(f"Failed to fetch data for BioProject: {accession}")
        return cls.from_json(data)

    @classmethod
    def from_json(cls, data: dict) -> 'GenomicData':
        sample_to_study_map = {}
        for experiment in data.get("experiments", []):
            sample_ref = experiment.get("sample_ref") or experiment.get("title", "")
            study_ref = experiment.get("study_ref") or experiment.get("title", "")
            sample_to_study_map[sample_ref] = study_ref

        studies_map = {}
        if data.get("studies"):
            studies_map = {study.get("accession") or study.get("title", ""): study for study in data.get("studies", [])}

        project_data = data.get("bioproject", {})
        project_type = project_data.get("project_type", {})
        target = project_type.get("target", {})
        organism = target.get("organism", {})
        submission = project_data.get("submission", {})
        organization = submission.get("organization", {})

        # Create Project instance (using its own definition)
        project = Project(
            id=project_data.get("id", ""),
            accession=project_data.get("accession") or project_data.get("title", ""),
            archive=project_data.get("archive", ""),
            organism_name=project_data.get("organism_name", ""),
            title=project_data.get("title", ""),
            description=project_data.get("description", ""),
            release_date=project_data.get("release_date", ""),
            target_capture=target.get("capture", ""),
            target_material=target.get("material", ""),
            target_sample_scope=target.get("sample_scope", ""),
            organism_species=organism.get("species", ""),
            organism_taxID=organism.get("taxID", ""),
            organism_supergroup=organism.get("supergroup", ""),
            method=project_type.get("method", ""),
            data_types=project_type.get("data_types", []),
            project_data_type=project_type.get("project_data_type", ""),
            submitted_date=submission.get("submitted", ""),
            organization_role=organization.get("role", ""),
            organization_type=organization.get("type", ""),
            organization_name=organization.get("name", ""),
            access=submission.get("access", "")
        )

        # Parse into InternalSample instances
        internal_samples = []
        for biosample in data.get("biosamples", []):
            sample_ref = biosample.get("accession") or biosample.get("title") or biosample.get("scientific_name", "")
            study_ref = sample_to_study_map.get(sample_ref)
            study_data = studies_map.get(study_ref, {})

            internal_sample = InternalSample(
                accession=biosample.get("accession") or biosample.get("title") or biosample.get("scientific_name", ""),
                title=biosample.get("title", ""),
                scientific_name=biosample.get("scientific_name", ""),
                taxon_id=biosample.get("taxon_id", ""),
                attributes=biosample.get("attributes", {}),
                study_accession=study_ref,
                study_center_name=study_data.get("center_name"),
                study_title=study_data.get("title"),
                study_abstract=study_data.get("abstract"),
                study_description=study_data.get("description")
            )
            internal_samples.append(internal_sample)

        # Parse into InternalExperiment instances
        internal_experiments = []
        for exp in data.get("experiments", []):
            design = exp.get("design", {})
            platform = exp.get("platform", {})

            internal_experiment = InternalExperiment(
                accession=exp.get("accession") or exp.get("title", ""),
                title=exp.get("title", ""),
                study_ref=exp.get("study_ref") or exp.get("title", ""),
                sample_ref=exp.get("sample_ref") or exp.get("title", ""),
                library_name=design.get("library_name", ""),
                library_strategy=design.get("library_strategy", ""),
                library_source=design.get("library_source", ""),
                library_selection=design.get("library_selection", ""),
                library_layout=design.get("library_layout", ""),
                nominal_length=design.get("nominal_length", ""),
                platform_type=platform.get("type", ""),
                instrument_model=platform.get("instrument_model", "")
            )
            internal_experiments.append(internal_experiment)

        # Parse into Output instances (using its own definition)
        outputs_list = []
        for run in data.get("runs", []):
            base_composition = run.get("base_composition", {})

            output_files = [
                OutputFile(
                    filename=file.get("filename") or file.get("url", "").split("/")[-1] or "",
                    size=file.get("size", 0),
                    date=file.get("date", ""),
                    url=file.get("url", ""),
                    md5=file.get("md5", "")
                )
                for file in run.get("files", [])
            ]

            output = Output(
                accession=run.get("accession") or run.get("title", ""),
                title=run.get("title", ""),
                experiment_ref=run.get("experiment_ref") or run.get("title", ""),
                total_spots=run.get("total_spots", 0),
                total_bases=run.get("total_bases", 0),
                size=run.get("size", 0),
                published=run.get("published", ""),
                files=output_files,
                nreads=run.get("nreads", 0),
                nspots=run.get("nspots", 0),
                a_count=base_composition.get("A", 0),
                c_count=base_composition.get("C", 0),
                g_count=base_composition.get("G", 0),
                t_count=base_composition.get("T", 0),
                n_count=base_composition.get("N", 0)
            )
            outputs_list.append(output)

        # Create the final GenomicData instance using wrappers containing internal types
        return cls(
            project=project,
            samples=Samples(items=internal_samples),
            experiments=Experiments(items=internal_experiments),
            outputs=Outputs(items=outputs_list)
        )


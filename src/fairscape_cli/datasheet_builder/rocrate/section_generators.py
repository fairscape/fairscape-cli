from .base import ROCrateProcessor
import os
import traceback

class SectionGenerator:
    def __init__(self, template_engine, processor=None):
        self.template_engine = template_engine
        self.processor = processor
    
    def generate(self, template_name, **context):
        return self.template_engine.render(template_name, **context)


class OverviewSectionGenerator(SectionGenerator):
    def generate(self, processor=None):
        if processor:
            self.processor = processor
        
        if not self.processor:
            raise ValueError("Processor is required to generate the overview section")
        
        root = self.processor.root
        additional_properties = root.get("additionalProperty", [])
        
        context = {
            'title': root.get("name", "Untitled RO-Crate"),
            'description': root.get("description", ""),
            'id_value': root.get("@id", ""),
            'doi': root.get("identifier", ""),
            'license_value': root.get("license", ""),
            'ethical_review': root.get("ethicalReview", ""),
            'release_date': root.get("datePublished", ""),
            'created_date': root.get("dateCreated", ""),
            'updated_date': root.get("dateModified", ""),
            'authors': root.get("author", ""),
            'publisher': root.get("publisher", ""),
            'principal_investigator': root.get("principalInvestigator", ""),
            'contact_email': root.get("contactEmail", ""),
            'copyright': root.get("copyrightNotice", ""),
            'terms_of_use': root.get("conditionsOfAccess", ""),
            'confidentiality_level': root.get("confidentialityLevel", ""),
            'citation': root.get("citation", ""),
            'version': root.get("version", ""),
            'content_size': root.get("contentSize", ""),
            'human_subject': self.processor.get_property_value("Human Subject", additional_properties),
            'human_subject_research': self.processor.get_property_value("Human Subject Research", additional_properties) or "No",
            'human_subject_exemptions': self.processor.get_property_value("Human Subjects Exemptions", additional_properties) or "N/A",
            'deidentified_samples': self.processor.get_property_value("De-identified Samples", additional_properties) or "Yes",
            'fda_regulated': self.processor.get_property_value("FDA Regulated", additional_properties) or "No",
            'irb': self.processor.get_property_value("IRB", additional_properties) or "N/A",
            'irb_protocol_id': self.processor.get_property_value("IRB Protocol ID", additional_properties) or "N/A",
            'data_governance': self.processor.get_property_value("Data Governance Committee", additional_properties) or "",
            'completeness': self.processor.get_property_value("Completeness", additional_properties),
            'funding': root.get("funder", ""),
            'keywords': root.get("keywords", []),
            "published": self.processor.published
        }
        
        related_publications = root.get("associatedPublication", [])
        if related_publications and isinstance(related_publications, list):
            context['related_publications'] = related_publications
        else:
            context['related_publications'] = []
        
        return self.template_engine.render('sections/overview.html', **context)

class UseCasesSectionGenerator(SectionGenerator):
    def generate(self, processor=None):
        if processor:
            self.processor = processor
        
        if not self.processor:
            raise ValueError("Processor is required to generate the use cases section")
        
        root = self.processor.root
        additional_properties = root.get("additionalProperty", [])
        
        context = {
            'intended_uses': self.processor.get_property_value("Intended Use", additional_properties),
            'limitations': self.processor.get_property_value("Limitations", additional_properties),
            'prohibited_uses': self.processor.get_property_value("Prohibited Uses", additional_properties),
            'maintenance_plan': self.processor.get_property_value("Maintenance Plan", additional_properties),
            'potential_bias': self.processor.get_property_value("Potential Sources of Bias", additional_properties)
        }
        
        return self.template_engine.render('sections/use_cases.html', **context)


class DistributionSectionGenerator(SectionGenerator):
    def generate(self, processor=None):
        if processor:
            self.processor = processor
        
        if not self.processor:
            raise ValueError("Processor is required to generate the distribution section")
        
        root = self.processor.root
        
        context = {
            'license_value': root.get("license", ""),
            'publisher': root.get("publisher", ""),
            'host': root.get("distributionHost", ""),
            'doi': root.get("doi", ""),
            'release_date': root.get("datePublished", ""),
            'version': root.get("version", "")
        }
        
        return self.template_engine.render('sections/distribution.html', **context)


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


class SubcratesSectionGenerator(SectionGenerator):
    def generate(self, processor=None, base_dir=None):
        if processor:
            self.processor = processor
        
        if not self.processor:
            raise ValueError("Processor is required to generate the subcrates section")
        
        subcrates = self.processor.find_subcrates()
        
        processed_subcrates = []
        subcrate_processors = {}
        hasPart_mapping = {}
        
        for subcrate_ref in self.processor.root.get("hasPart", []):
            if isinstance(subcrate_ref, dict) and "@id" in subcrate_ref:
                subcrate_id = subcrate_ref["@id"]
                hasPart_mapping[subcrate_id] = {}
        
        for subcrate_info in subcrates:
            metadata_path = subcrate_info.get("metadata_path", "")
            if not metadata_path or not base_dir:
                continue
                
            full_path = os.path.join(base_dir, metadata_path)
            if not os.path.exists(full_path):
                continue
                
            try:
                subcrate_processor = ROCrateProcessor(json_path=full_path)
                subcrate_id = subcrate_processor.root.get("@id", subcrate_info.get("id", ""))
                
                subcrate_processors[subcrate_id] = subcrate_processor
                subcrate_dir = os.path.dirname(full_path)
                
                files, software, instruments, samples, experiments, computations, schemas, other = subcrate_processor.categorize_items()
                if isinstance(subcrate_processor.root.get("author", ""), list):
                    authors = ", ".join(subcrate_processor.root.get("author", ""))
                else:
                    authors = subcrate_processor.root.get("author", "")
                
                additional_properties = subcrate_processor.root.get("additionalProperty", [])
                
                subcrate = {
                    'name': subcrate_processor.root.get("name", subcrate_info.get("name", "Unnamed Sub-Crate")),
                    'id': subcrate_id,
                    'description': subcrate_processor.root.get("description", subcrate_info.get("description", "")),
                    'authors': authors,
                    'keywords': subcrate_processor.root.get("keywords", []),
                    'metadata_path': metadata_path,
                }
                
                
                size = subcrate_processor.root.get("contentSize", "")
                if not size and os.path.exists(subcrate_dir):
                    try:
                        dir_size = get_directory_size(subcrate_dir)
                        size = format_size(dir_size)
                    except Exception:
                        size = "Unknown"
                
                subcrate["size"] = size
                
                subcrate['doi'] = subcrate_processor.root.get("identifier", self.processor.root.get("identifier", ""))
                subcrate['date'] = subcrate_processor.root.get("datePublished", self.processor.root.get("datePublished", ""))
                subcrate['contact'] = subcrate_processor.root.get("contactEmail", self.processor.root.get("contactEmail", ""))
                subcrate['published'] = self.processor.published
                
                # Get copyright, license, and terms of use
                subcrate['copyright'] = subcrate_processor.root.get("copyrightNotice", "Copyright (c) 2025 The Regents of the University of California")
                subcrate['license'] = subcrate_processor.root.get("license", "https://creativecommons.org/licenses/by-nc-sa/4.0/")
                subcrate['terms_of_use'] = subcrate_processor.root.get("conditionsOfAccess", "Attribution is required to the copyright holders and the authors. Any publications referencing this data or derived products should cite the related article as well as directly citing this data collection.")
                
                subcrate['confidentiality'] = subcrate_processor.root.get("confidentialityLevel", self.processor.root.get("confidentialityLevel", ""))
                subcrate['funder'] = subcrate_processor.root.get("funder", self.processor.root.get("funder", ""))
                subcrate['md5'] = subcrate_processor.root.get("MD5", "")
                subcrate['evidence'] = subcrate_processor.root.get("hasEvidenceGraph", {}).get("@id","")

                subcrate['files'] = files
                subcrate['files_count'] = len(files)
                subcrate['software'] = software
                subcrate['software_count'] = len(software)
                subcrate['instruments'] = instruments
                subcrate['instruments_count'] = len(instruments)
                subcrate['samples'] = samples
                subcrate['samples_count'] = len(samples)
                subcrate['experiments'] = experiments
                subcrate['experiments_count'] = len(experiments)
                subcrate['computations'] = computations
                subcrate['computations_count'] = len(computations)
                subcrate['schemas'] = schemas
                subcrate['schemas_count'] = len(schemas)
                subcrate['other'] = other
                subcrate['other_count'] = len(other)
                
                subcrate['file_formats'] = subcrate_processor.get_formats_summary(files)
                subcrate['software_formats'] = subcrate_processor.get_formats_summary(software)
                subcrate['file_access'] = subcrate_processor.get_access_summary(files)
                subcrate['software_access'] = subcrate_processor.get_access_summary(software)
                
                patterns, external_datasets = self.extract_computation_patterns(subcrate_processor, computations, subcrate_processors)
                subcrate['computation_patterns'] = patterns
                
                external_datasets_by_format = {}
                for dataset in external_datasets:
                    fmt = dataset["format"]
                    subcrate_name = dataset["subcrate"]
                    
                    if subcrate_name:
                        key = f"{subcrate_name}, {fmt}"
                        if key in external_datasets_by_format:
                            external_datasets_by_format[key] += 1
                        else:
                            external_datasets_by_format[key] = 1
                
                subcrate['input_datasets'] = external_datasets_by_format
                subcrate['input_datasets_count'] = len(external_datasets)
                subcrate['inputs_count'] = subcrate['samples_count'] + subcrate['input_datasets_count']
                
                subcrate['experiment_patterns'] = self.extract_experiment_patterns(subcrate_processor, experiments)
                
                # Extract cell line information including CVCL identifier
                subcrate['cell_lines'] = subcrate_processor.extract_cell_line_info(samples)
                subcrate['species'] = subcrate_processor.extract_sample_species(samples)
                subcrate['experiment_types'] = subcrate_processor.extract_experiment_types(experiments)
                
                related_pubs = subcrate_processor.root.get("relatedPublications", [])
                if not related_pubs:
                    associated_pub = subcrate_processor.root.get("associatedPublication", "")
                    if associated_pub:
                        if isinstance(associated_pub, str):
                            related_pubs = [associated_pub]
                        elif isinstance(associated_pub, list):
                            related_pubs = associated_pub
                    elif self.processor.root.get("relatedPublications", []):
                        related_pubs = self.processor.root.get("relatedPublications", [])
                    elif self.processor.root.get("associatedPublication", ""):
                        associated_pub = self.processor.root.get("associatedPublication", "")
                        if associated_pub and isinstance(associated_pub, str):
                            related_pubs = [associated_pub]
                        elif isinstance(associated_pub, list):
                            related_pubs = associated_pub
                
                subcrate['related_publications'] = related_pubs
                processed_subcrates.append(subcrate)
                
            except Exception as e:
                print(f"Error processing subcrate {subcrate_info.get('name', 'Unnamed Sub-Crate')}: {e}")
                traceback.print_exc()
                continue
        
        context = {
            'subcrates': processed_subcrates,
            'subcrate_count': len(processed_subcrates)
        }
        
        return self.template_engine.render('sections/subcrates.html', **context)


    def extract_experiment_patterns(self, processor, experiments):
        patterns = {}
        
        for experiment in experiments:
            input_type = "Sample"
            output_formats = []
            
            output_datasets = experiment.get("generated", [])
            if output_datasets:
                if isinstance(output_datasets, list):
                    for dataset in output_datasets:
                        if isinstance(dataset, dict) and "@id" in dataset:
                            format_value = processor.get_dataset_format(dataset["@id"])
                            if format_value != "unknown" and format_value not in output_formats:
                                output_formats.append(format_value)
                        elif isinstance(dataset, str):
                            format_value = processor.get_dataset_format(dataset)
                            if format_value != "unknown" and format_value not in output_formats:
                                output_formats.append(format_value)
            
            if output_formats:
                output_str = ", ".join(sorted(output_formats))
                pattern = f"{input_type} → {output_str}"
                
                if pattern in patterns:
                    patterns[pattern] += 1
                else:
                    patterns[pattern] = 1
        
        return list(patterns.keys())

    def extract_computation_patterns(self, processor, computations, subcrate_processors=None):
        patterns = {}
        external_datasets = []
        
        for computation in computations:
            input_formats = []
            output_formats = []
            
            # Process inputs
            input_datasets_raw = computation.get("usedDataset", [])
            if input_datasets_raw:
                if isinstance(input_datasets_raw, list):
                    for dataset in input_datasets_raw:
                        if isinstance(dataset, dict) and "@id" in dataset:
                            dataset_id = dataset["@id"]
                        elif isinstance(dataset, str):
                            dataset_id = dataset
                        else:
                            continue
                            
                        format_value = processor.get_dataset_format(dataset_id)
                        if format_value != "unknown":
                            if format_value not in input_formats:
                                input_formats.append(format_value)
                        elif subcrate_processors:
                            for subcrate_id, subcrate_proc in subcrate_processors.items():
                                if subcrate_proc:
                                    format_value = subcrate_proc.get_dataset_format(dataset_id)
                                    if format_value != "unknown":
                                        subcrate_name = subcrate_proc.root.get("name", "Unknown")
                                        
                                        display_fmt = f"{subcrate_name} ({format_value})"
                                        if display_fmt not in input_formats:
                                            input_formats.append(display_fmt)
                                        
                                        external_datasets.append({
                                            "id": dataset_id,
                                            "format": format_value,
                                            "subcrate": subcrate_name
                                        })
                                        break
                elif isinstance(input_datasets_raw, dict) and "@id" in input_datasets_raw:
                    dataset_id = input_datasets_raw["@id"]
                    format_value = processor.get_dataset_format(dataset_id)
                    if format_value != "unknown":
                        input_formats.append(format_value)
                    elif subcrate_processors:
                        for subcrate_id, subcrate_proc in subcrate_processors.items():
                            if subcrate_proc:
                                format_value = subcrate_proc.get_dataset_format(dataset_id)
                                if format_value != "unknown":
                                    subcrate_name = subcrate_proc.root.get("name", "Unknown")
                                    display_fmt = f"{subcrate_name} ({format_value})"
                                    input_formats.append(display_fmt)
                                    external_datasets.append({
                                        "id": dataset_id,
                                        "format": format_value,
                                        "subcrate": subcrate_name
                                    })
                                    break
            
            output_datasets = computation.get("generated", [])
            if output_datasets:
                if isinstance(output_datasets, list):
                    for dataset in output_datasets:
                        if isinstance(dataset, dict) and "@id" in dataset:
                            format_value = processor.get_dataset_format(dataset["@id"])
                            if format_value != "unknown" and format_value not in output_formats:
                                output_formats.append(format_value)
                elif isinstance(output_datasets, dict) and "@id" in output_datasets:
                    format_value = processor.get_dataset_format(output_datasets["@id"])
                    if format_value != "unknown":
                        output_formats.append(format_value)
            
            # Create a pattern string
            if input_formats and output_formats:
                input_str = ", ".join(sorted(input_formats))
                output_str = ", ".join(sorted(output_formats))
                pattern = f"{input_str} → {output_str}"
                
                if pattern in patterns:
                    patterns[pattern] += 1
                else:
                    patterns[pattern] = 1
        
        return list(patterns.keys()), external_datasets
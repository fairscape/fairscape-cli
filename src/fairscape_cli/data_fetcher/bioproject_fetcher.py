import requests
import json
import xml.etree.ElementTree as ET
import os
import argparse

def fetch_bioproject_data(bioproject_accession, api_key, details_dir="details"):

    
    # First fetch the BioProject data
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "bioproject",
        "term": bioproject_accession,
        "retmode": "json",
        "api_key": api_key
    }

    response = requests.get(search_url, params=search_params)
    
    try:
        search_results = response.json()
        
        if "esearchresult" not in search_results or "idlist" not in search_results["esearchresult"] or len(search_results["esearchresult"]["idlist"]) == 0:
            return None
            
        bioproject_id = search_results["esearchresult"]["idlist"][0]
    except json.JSONDecodeError:
        return None

    bioproject_fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    bioproject_fetch_params = {
        "db": "bioproject",
        "id": bioproject_id,
        "retmode": "xml",
        "api_key": api_key
    }
    
    response = requests.get(bioproject_fetch_url, params=bioproject_fetch_params)
    response_text = response.text
    
    bioproject_metadata = parse_bioproject_xml(response_text)
    if not bioproject_metadata:
        bioproject_metadata = {
            "id": bioproject_id,
            "accession": bioproject_accession
        }

    # Initialize result structure
    result = {
        "bioproject": bioproject_metadata,
        "biosamples": [],
        "studies": [],
        "experiments": [],
        "runs": []
    }

    # First try via SRA linkage
    sra_data = fetch_sra_data(bioproject_id, api_key)
    if sra_data and (sra_data.get("biosamples") or sra_data.get("studies") or sra_data.get("experiments") or sra_data.get("runs")):
        result["biosamples"] = sra_data.get("biosamples", [])
        result["studies"] = sra_data.get("studies", [])
        result["experiments"] = sra_data.get("experiments", [])
        result["runs"] = sra_data.get("runs", [])
    else:
        # If no SRA data, try to get BioSamples directly
        biosamples = fetch_biosamples_for_bioproject(bioproject_id, api_key)
        if biosamples:
            result["biosamples"] = biosamples

    return result

def fetch_sra_data(bioproject_id, api_key):
    """Fetch SRA data linked to a BioProject"""
    link_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    sra_link_params = {
        "dbfrom": "bioproject",
        "db": "sra",
        "id": bioproject_id,
        "retmode": "json",
        "api_key": api_key
    }

    response = requests.get(link_url, params=sra_link_params)
    
    try:
        sra_link_results = response.json()
    except json.JSONDecodeError:
        return None

    sra_ids = []
    if "linksets" in sra_link_results and len(sra_link_results["linksets"]) > 0:
        linkset = sra_link_results["linksets"][0]
        if "linksetdbs" in linkset:
            for linksetdb in linkset["linksetdbs"]:
                if linksetdb["linkname"] == "bioproject_sra":
                    sra_ids = linksetdb["links"]
                    break

    if sra_ids:
        batch_size = 50
        all_roots = []
        
        for i in range(0, len(sra_ids), batch_size):
            batch = sra_ids[i:i+batch_size]
            
            sra_fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            sra_fetch_params = {
                "db": "sra",
                "id": ",".join(batch),
                "rettype": "xml",
                "api_key": api_key
            }
            
            response = requests.get(sra_fetch_url, params=sra_fetch_params)
            response_text = response.text
            
            if response_text.strip():
                try:
                    batch_root = ET.fromstring(response_text)
                    all_roots.append(batch_root)
                except ET.ParseError:
                    pass
        
        if all_roots:
            if len(all_roots) > 1:
                combined_root = ET.Element("EXPERIMENT_PACKAGE_SET")
                
                for root in all_roots:
                    for exp_package in root.findall(".//EXPERIMENT_PACKAGE"):
                        combined_root.append(exp_package)
                
                return parse_experiment_packages(combined_root)
            else:
                return parse_experiment_packages(all_roots[0])
    
    return None

def fetch_biosamples_for_bioproject(bioproject_id, api_key):
    """Fetch BioSamples directly linked to a BioProject"""
    # First, get the BioSample IDs linked to this BioProject
    link_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    biosample_link_params = {
        "dbfrom": "bioproject",
        "db": "biosample",
        "id": bioproject_id,
        "retmode": "json",
        "api_key": api_key
    }

    response = requests.get(link_url, params=biosample_link_params)
    
    try:
        link_results = response.json()
    except json.JSONDecodeError:
        return []

    biosample_ids = []
    if "linksets" in link_results and len(link_results["linksets"]) > 0:
        linkset = link_results["linksets"][0]
        if "linksetdbs" in linkset:
            for linksetdb in linkset["linksetdbs"]:
                if linksetdb["linkname"] == "bioproject_biosample":
                    biosample_ids = linksetdb["links"]
                    break

    if not biosample_ids:
        return []

    # Now fetch the BioSample details
    biosamples = []
    batch_size = 50
    
    for i in range(0, len(biosample_ids), batch_size):
        batch = biosample_ids[i:i+batch_size]
        
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "biosample",
            "id": ",".join(batch),
            "rettype": "xml",
            "api_key": api_key
        }
        
        response = requests.get(fetch_url, params=fetch_params)
        if response.status_code != 200:
            continue
            
        try:
            root = ET.fromstring(response.text)
            
            for biosample in root.findall(".//BioSample"):
                sample_data = {
                    "accession": biosample.get("accession", ""),
                    "title": "",
                    "scientific_name": "",
                    "taxon_id": "",
                    "attributes": {}
                }
                
                # Get title from Description/Title
                title_elem = biosample.find(".//Description/Title")
                if title_elem is not None and title_elem.text:
                    sample_data["title"] = title_elem.text
                
                # Get organism information
                organism = biosample.find(".//Description/Organism")
                if organism is not None:
                    sample_data["scientific_name"] = organism.get("taxonomy_name", "")
                    sample_data["taxon_id"] = organism.get("taxonomy_id", "")
                
                # Get attributes
                for attribute in biosample.findall(".//Attributes/Attribute"):
                    attr_name = attribute.get("attribute_name", "")
                    if attr_name and attribute.text:
                        sample_data["attributes"][attr_name] = attribute.text
                
                biosamples.append(sample_data)
                
        except ET.ParseError:
            pass
    
    return biosamples

def parse_bioproject_xml(xml_text):
    try:
        root = ET.fromstring(xml_text)
        
        bioproject_data = {}
        
        doc_summary = root.find(".//DocumentSummary")
        if not doc_summary:
            return None
        
        uid = doc_summary.get("uid", "")
        if uid:
            bioproject_data["id"] = uid
        
        project = doc_summary.find(".//Project")
        if project:
            archive_id = project.find(".//ProjectID/ArchiveID")
            if archive_id is not None:
                bioproject_data["accession"] = archive_id.get("accession", "")
                bioproject_data["archive"] = archive_id.get("archive", "")
                if not uid and archive_id.get("id"):
                    bioproject_data["id"] = archive_id.get("id")
            
            project_descr = project.find(".//ProjectDescr")
            if project_descr is not None:
                name_elem = project_descr.find("Name")
                if name_elem is not None and name_elem.text:
                    bioproject_data["organism_name"] = name_elem.text
                
                title_elem = project_descr.find("Title")
                if title_elem is not None and title_elem.text:
                    bioproject_data["title"] = title_elem.text
                
                desc_elem = project_descr.find("Description")
                if desc_elem is not None and desc_elem.text:
                    bioproject_data["description"] = desc_elem.text
                
                release_date_elem = project_descr.find("ProjectReleaseDate")
                if release_date_elem is not None and release_date_elem.text:
                    bioproject_data["release_date"] = release_date_elem.text
                
                relevance_elem = project_descr.find("Relevance")
                if relevance_elem is not None:
                    relevance = {}
                    for rel_elem in relevance_elem:
                        if rel_elem.text:
                            relevance[rel_elem.tag] = rel_elem.text
                    if relevance:
                        bioproject_data["relevance"] = relevance
            
            project_type = project.find(".//ProjectType")
            if project_type is not None:
                project_type_submission = project_type.find("ProjectTypeSubmission")
                if project_type_submission is not None:
                    type_data = {}
                    
                    target_elem = project_type_submission.find("Target")
                    if target_elem is not None:
                        target_data = {
                            "capture": target_elem.get("capture", ""),
                            "material": target_elem.get("material", ""),
                            "sample_scope": target_elem.get("sample_scope", "")
                        }
                        
                        organism_elem = target_elem.find("Organism")
                        if organism_elem is not None:
                            organism_data = {
                                "species": organism_elem.get("species", ""),
                                "taxID": organism_elem.get("taxID", ""),
                                "name": "",
                                "supergroup": ""
                            }
                            
                            org_name_elem = organism_elem.find("OrganismName")
                            if org_name_elem is not None and org_name_elem.text:
                                organism_data["name"] = org_name_elem.text
                            
                            supergroup_elem = organism_elem.find("Supergroup")
                            if supergroup_elem is not None and supergroup_elem.text:
                                organism_data["supergroup"] = supergroup_elem.text
                            
                            target_data["organism"] = organism_data
                        
                        type_data["target"] = target_data
                    
                    method_elem = project_type_submission.find("Method")
                    if method_elem is not None:
                        type_data["method"] = method_elem.get("method_type", "")
                    
                    objectives_elem = project_type_submission.find("Objectives")
                    if objectives_elem is not None:
                        data_types = []
                        for data_elem in objectives_elem.findall("Data"):
                            data_type = data_elem.get("data_type", "")
                            if data_type:
                                data_types.append(data_type)
                        
                        if data_types:
                            type_data["data_types"] = data_types
                    
                    data_type_set_elem = project_type_submission.find("ProjectDataTypeSet")
                    if data_type_set_elem is not None:
                        data_type_elem = data_type_set_elem.find("DataType")
                        if data_type_elem is not None and data_type_elem.text:
                            type_data["project_data_type"] = data_type_elem.text
                    
                    if type_data:
                        bioproject_data["project_type"] = type_data
        
        submission = doc_summary.find(".//Submission")
        if submission is not None:
            submission_data = {
                "submitted": submission.get("submitted", "")
            }
            
            desc = submission.find("Description")
            if desc is not None:
                org_elem = desc.find("Organization")
                if org_elem is not None:
                    org_data = {
                        "role": org_elem.get("role", ""),
                        "type": org_elem.get("type", ""),
                        "name": ""
                    }
                    
                    name_elem = org_elem.find("Name")
                    if name_elem is not None and name_elem.text:
                        org_data["name"] = name_elem.text
                    
                    submission_data["organization"] = org_data
                
                access_elem = desc.find("Access")
                if access_elem is not None and access_elem.text:
                    submission_data["access"] = access_elem.text
            
            if submission_data:
                bioproject_data["submission"] = submission_data
        
        return bioproject_data
    
    except ET.ParseError:
        return None
        
def parse_experiment_packages(root):
    data = {
        "biosamples": [],
        "studies": [],
        "experiments": [],
        "runs": []
    }
    
    for exp_package in root.findall(".//EXPERIMENT_PACKAGE"):
        study = exp_package.find(".//STUDY")
        if study is not None and study.get("accession") not in [s.get("accession") for s in data["studies"]]:
            study_data = {
                "accession": study.get("accession", ""),
                "center_name": study.get("center_name", ""),
                "title": "",
                "abstract": "",
                "description": ""
            }
            
            descriptor = study.find(".//DESCRIPTOR")
            if descriptor is not None:
                study_data["title"] = descriptor.findtext(".//STUDY_TITLE", "")
                study_data["abstract"] = descriptor.findtext(".//STUDY_ABSTRACT", "")
                study_data["description"] = descriptor.findtext(".//STUDY_DESCRIPTION", "")
            
            data["studies"].append(study_data)
        
        sample = exp_package.find(".//SAMPLE")
        if sample is not None and sample.get("accession") not in [s.get("accession") for s in data["biosamples"]]:
            sample_data = {
                "accession": sample.get("accession", ""),
                "title": sample.findtext(".//TITLE", ""),
                "scientific_name": sample.findtext(".//SCIENTIFIC_NAME", ""),
                "taxon_id": sample.findtext(".//TAXON_ID", ""),
                "attributes": {}
            }
            
            for attr in sample.findall(".//SAMPLE_ATTRIBUTE"):
                tag = attr.findtext(".//TAG", "")
                value = attr.findtext(".//VALUE", "")
                if tag and tag != "N. A.":
                    sample_data["attributes"][tag] = value
            
            data["biosamples"].append(sample_data)
        
        experiment = exp_package.find(".//EXPERIMENT")
        if experiment is not None:
            exp_data = {
                "accession": experiment.get("accession", ""),
                "title": experiment.findtext(".//TITLE", ""),
                "study_ref": "",
                "sample_ref": "",
                "design": {},
                "platform": {}
            }
            
            study_ref_elem = experiment.find(".//STUDY_REF")
            if study_ref_elem is not None:
                exp_data["study_ref"] = study_ref_elem.get("accession", "")
            
            sample_desc_elem = experiment.find(".//SAMPLE_DESCRIPTOR")
            if sample_desc_elem is not None:
                exp_data["sample_ref"] = sample_desc_elem.get("accession", "")
            
            design_elem = experiment.find(".//DESIGN")
            if design_elem is not None:
                library_elem = design_elem.find(".//LIBRARY_DESCRIPTOR")
                if library_elem is not None:
                    exp_data["design"]["library_name"] = library_elem.findtext(".//LIBRARY_NAME", "")
                    exp_data["design"]["library_strategy"] = library_elem.findtext(".//LIBRARY_STRATEGY", "")
                    exp_data["design"]["library_source"] = library_elem.findtext(".//LIBRARY_SOURCE", "")
                    exp_data["design"]["library_selection"] = library_elem.findtext(".//LIBRARY_SELECTION", "")
                    
                    layout_elem = library_elem.find(".//LIBRARY_LAYOUT")
                    if layout_elem is not None and len(layout_elem) > 0:
                        layout_type = layout_elem[0].tag
                        exp_data["design"]["library_layout"] = layout_type
                        if layout_type == "PAIRED":
                            exp_data["design"]["nominal_length"] = layout_elem[0].get("NOMINAL_LENGTH", "")
            
            platform_elem = experiment.find(".//PLATFORM")
            if platform_elem is not None and len(platform_elem) > 0:
                platform_type = platform_elem[0].tag
                exp_data["platform"]["type"] = platform_type
                
                instrument_model = platform_elem.find(f".//{platform_type}/INSTRUMENT_MODEL")
                if instrument_model is not None:
                    exp_data["platform"]["instrument_model"] = instrument_model.text
            
            data["experiments"].append(exp_data)
        
        for run in exp_package.findall(".//RUN"):
            run_data = {
                "accession": run.get("accession", ""),
                "title": run.findtext(".//TITLE", ""),
                "experiment_ref": "",
                "total_spots": run.get("total_spots", ""),
                "total_bases": run.get("total_bases", ""),
                "size": run.get("size", ""),
                "published": run.get("published", ""),
                "files": []
            }
            
            exp_ref = run.find(".//EXPERIMENT_REF")
            if exp_ref is not None:
                run_data["experiment_ref"] = exp_ref.get("accession", "")
            
            for file_elem in run.findall(".//SRAFile"):
                file_data = {
                    "filename": file_elem.get("filename", ""),
                    "size": file_elem.get("size", ""),
                    "date": file_elem.get("date", ""),
                    "url": file_elem.get("url", ""),
                    "md5": file_elem.get("md5", "")
                }
                run_data["files"].append(file_data)
            
            stats_elem = run.find(".//Statistics")
            if stats_elem is not None:
                run_data["nreads"] = stats_elem.get("nreads", "")
                run_data["nspots"] = stats_elem.get("nspots", "")
                
                reads = []
                for read_elem in stats_elem.findall(".//Read"):
                    read_data = {
                        "index": read_elem.get("index", ""),
                        "count": read_elem.get("count", ""),
                        "average": read_elem.get("average", ""),
                        "stdev": read_elem.get("stdev", "")
                    }
                    reads.append(read_data)
                
                if reads:
                    run_data["reads"] = reads
            
            bases_elem = run.find(".//Bases")
            if bases_elem is not None:
                run_data["base_count"] = bases_elem.get("count", "")
                
                bases = {}
                for base_elem in bases_elem.findall(".//Base"):
                    value = base_elem.get("value", "")
                    count = base_elem.get("count", "")
                    if value and count:
                        bases[value] = count
                
                if bases:
                    run_data["base_composition"] = bases
            
            data["runs"].append(run_data)
    
    return data

def main():
    parser = argparse.ArgumentParser(description="Fetch and parse BioProject, BioSample, and SRA data")
    parser.add_argument("bioproject", help="BioProject accession number")
    parser.add_argument("--api-key", default="b5842d8d17966b13241247e793b879532d07", help="NCBI API key")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--details-dir", default="details", help="Details directory")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    details_dir = os.path.join(args.output_dir, args.details_dir, args.bioproject)
    if not os.path.exists(details_dir):
        os.makedirs(details_dir)
    
    os.chdir(args.output_dir)
    
    data = fetch_bioproject_data(args.bioproject, args.api_key, details_dir)
    
    if data:
        output_file = f"{args.bioproject}_metadata.json"
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Data written to {output_file}")

if __name__ == "__main__":
    main()
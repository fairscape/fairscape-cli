import click
import pathlib
from typing import List, Optional, Tuple
import traceback 

from fairscape_cli.data_fetcher.GenomicData import GenomicData
from fairscape_cli.models.pep import PEPtoROCrateMapper
from fairscape_cli.data_fetcher.PhysioNetImporter import PhysioNetImporter
from fairscape_cli.data_fetcher.generic_data import ResearchData


@click.group('import')
def import_group():
    """Import external data or projects into RO-Crate format."""
    pass

@import_group.command('bioproject')
@click.option('--accession', required=True, type=str, help='NCBI BioProject accession (e.g., PRJNA12345).')
@click.option('--output-dir', required=True, type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=pathlib.Path), help='Directory to create the RO-Crate in.')
@click.option('--author', required=True, type=str, help='Author name to associate with generated metadata.')
@click.option('--api-key', required=True, type=str, default=None, help='NCBI API key (optional).')
@click.option('--name', required=False, type=str, help='Override the default RO-Crate name.')
@click.option('--description', required=False, type=str, help='Override the default RO-Crate description.')
@click.option('--keywords', required=False, multiple=True, type=str, help='Override the default RO-Crate keywords (can be used multiple times).')
@click.option('--license', required=False, type=str, help='Override the default RO-Crate license URL.')
@click.option('--version', required=False, type=str, help='Override the default RO-Crate version.')
@click.option('--organization-name', required=False, type=str, help='Set the organization name for the RO-Crate.')
@click.option('--project-name', required=False, type=str, help='Set the project name for the RO-Crate.')
@click.pass_context
def pull_bioproject(
    ctx,
    accession: str,
    output_dir: pathlib.Path,
    author: str,
    api_key: Optional[str],
    name: Optional[str],
    description: Optional[str],
    keywords: Optional[List[str]],
    license: Optional[str],
    version: Optional[str],
    organization_name: Optional[str],
    project_name: Optional[str]
):
    """Pulls NCBI BioProject data and converts it into an RO-Crate."""

    click.echo(f"Pulling BioProject {accession}...")

    cache_details_path = output_dir 

    try:
        # Step 1: Fetch data using GenomicData.from_api
        genomic_data_instance = GenomicData.from_api(
            accession=accession,
            api_key=api_key if api_key else "", 
            details_dir=str(cache_details_path) 
        )
        click.echo("Successfully fetched data from NCBI.")

        guid = genomic_data_instance.to_rocrate(
            output_dir=str(output_dir), 
            author=author,
            crate_name=name,
            crate_description=description,
            crate_keywords=list(keywords) if keywords else None,
            crate_license=license,
            crate_version=version,
            organization_name=organization_name,
            project_name=project_name
        )

        click.echo(f"Successfully created RO-Crate.")
        click.echo(f"{guid}")

    except ValueError as e:
        click.echo(f"ERROR: {e}", err=True)
        ctx.exit(1)
    except FileNotFoundError as e:
            click.echo(f"ERROR: File not found during RO-Crate generation - {e}", err=True)
            ctx.exit(1)
    except Exception as e:
        click.echo(f"An error occurred: {e}", err=True)
        import traceback 
        traceback.print_exc()
        ctx.exit(1)


@import_group.command('pep')
@click.argument('pep-path', type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--output-path', required=False, type=click.Path(path_type=pathlib.Path), help='Path for RO-Crate (defaults to PEP directory)')
@click.option('--name', required=False, type=str, help='Name for the RO-Crate (overrides PEP metadata)')
@click.option('--description', required=False, type=str, help='Description (overrides PEP metadata)')
@click.option('--author', required=False, type=str, help='Author (overrides PEP metadata)')
@click.option('--organization-name', required=False, type=str, help='Organization name')
@click.option('--project-name', required=False, type=str, help='Project name')
@click.option('--keywords', required=False, multiple=True, type=str, help='Keywords (overrides PEP metadata)')
@click.option('--license', required=False, type=str, default="https://creativecommons.org/licenses/by/4.0/", help='License URL')
@click.option('--date-published', required=False, type=str, help='Publication date')
@click.option('--version', required=False, type=str, default="1.0", help='Version string')
@click.pass_context
def from_pep(
    ctx,
    pep_path: pathlib.Path,
    output_path: Optional[pathlib.Path],
    name: Optional[str],
    description: Optional[str],
    author: Optional[str],
    organization_name: Optional[str],
    project_name: Optional[str],
    keywords: Optional[List[str]],
    license: Optional[str],
    date_published: Optional[str],
    version: str
):
    """Convert a Portable Encapsulated Project (PEP) to an RO-Crate.
    
    PEP-PATH: Path to the PEP directory or config file
    """
    try:
        
        
        mapper = PEPtoROCrateMapper(pep_path)
        rocrate_id = mapper.create_rocrate(
            output_path=output_path,
            name=name,
            description=description,
            author=author,
            organization_name=organization_name,
            project_name=project_name,
            keywords=keywords,
            license=license,
            date_published=date_published,
            version=version
        )
        click.echo(rocrate_id)
    except Exception as exc:
        click.echo(f"ERROR: {str(exc)}")
        ctx.exit(code=1)
        

@import_group.command('physionet')
@click.argument('physionet-url', type=str)
@click.option('--output-dir', required=True, type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=pathlib.Path), help='Directory to create the RO-Crate in.')
@click.option('--author', required=False, type=str, help='Author name to associate with generated metadata. PhysioNet authors are extracted but overridden by this.')
@click.option('--name', required=False, type=str, help='Override the default RO-Crate name (extracted from PhysioNet title).')
@click.option('--description', required=False, type=str, help='Override the default RO-Crate description (extracted from PhysioNet abstract).')
@click.option('--keywords', required=False, multiple=True, type=str, help='Override the default RO-Crate keywords (extracted from PhysioNet topics). Can be used multiple times.')
@click.option('--license', required=False, type=str, help='Override the default RO-Crate license URL (extracted from PhysioNet license).')
@click.option('--version', required=False, type=str, help='Override the default RO-Crate version (extracted from PhysioNet version).')
@click.option('--organization-name', required=False, type=str, help='Set the organization name for the RO-Crate.', default="PhysioNet")
@click.option('--project-name', required=False, type=str, help='Set the project name for the RO-Crate.', default="PhysioNet Project")
@click.option('--associated-publication', required=False, multiple=True, type=str, help='Override/add associated publication URLs (extracted from PhysioNet citation). Can be used multiple times.')
@click.option('--usage-info', required=False, type=str, help='Override the usage information (extracted from PhysioNet usage notes).')
@click.option('--ethical-review', required=False, type=str, help='Override the ethical review information (extracted from PhysioNet ethics).')
@click.option('--doi', required=False, type=str, help='Override/set the DOI identifier.')
@click.option('--additional-property', required=False, multiple=True, type=(str, str), help='Add custom additional properties as key=value pairs (e.g., --additional-property "Method=Description of methods").')
@click.pass_context
def pull_physionet(
    ctx: click.Context,
    physionet_url: str,
    output_dir: pathlib.Path,
    author: str,
    name: Optional[str],
    description: Optional[str],
    keywords: Optional[List[str]],
    license: Optional[str],
    version: Optional[str],
    organization_name: Optional[str],
    project_name: Optional[str],
    associated_publication: Optional[List[str]],
    usage_info: Optional[str],
    ethical_review: Optional[str],
    doi: Optional[str],
    additional_property: Optional[List[Tuple[str, str]]],
):
    """Pulls PhysioNet project data (metadata and file structure) and converts it into an RO-Crate.

    PHYSiONET_URL: The URL of the PhysioNet project page (e.g., https://physionet.org/content/bigp3bci/1.0.0/).
    """

    click.echo(f"Pulling PhysioNet project from {physionet_url}...")

    try:
        # Step 1: Initialize the importer
        importer = PhysioNetImporter(physionet_url=physionet_url, output_dir=output_dir)
        click.echo(f"PhysioNet project ID: {importer.project_id}, Version: {importer.version}")

        # Prepare additional properties from command line input
        extra_properties_list = []
        if additional_property:
            for key, value in additional_property:
                 extra_properties_list.append({
                     "@type": "PropertyValue",
                     "name": key,
                     "value": value
                 })

        # Prepare associated publications from command line input
        # This format expects just URLs for simplicity in CLI
        assoc_pubs_list = None
        if associated_publication:
             assoc_pubs_list = [{"@type": "CreativeWork", "url": url} for url in associated_publication]


        # Step 2: Generate the RO-Crate
        guid = importer.to_rocrate(
            output_dir=output_dir,
            author=author,
            crate_name=name,
            crate_description=description,
            crate_keywords=list(keywords) if keywords else None,
            crate_license=license,
            crate_version=version,
            organization_name=organization_name,
            project_name=project_name,
            associated_publication=assoc_pubs_list, # Use prepared list
            usage_info=usage_info,
            ethical_review=ethical_review,
            identifier=doi,
            additional_properties=extra_properties_list # Use prepared list
        )

        click.echo(f"Successfully created RO-Crate.")
        click.echo(f"{guid}")

    except ValueError as e:
        click.echo(f"ERROR: Invalid input or URL format - {e}", err=True)
        ctx.exit(1)
    except ConnectionError as e:
        click.echo(f"ERROR: Failed to fetch data from PhysioNet - {e}", err=True)
        ctx.exit(1)
    except RuntimeError as e:
         click.echo(f"ERROR: Failed to parse PhysioNet page - {e}", err=True)
         ctx.exit(1)
    except FileNotFoundError as e:
            click.echo(f"ERROR: File not found during RO-Crate generation - {e}", err=True)
            ctx.exit(1)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
        import traceback
        traceback.print_exc()
        ctx.exit(1)
        
def generic_importer_options(f):
    f = click.option('--output-dir', required=True, type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=pathlib.Path), help='Directory to create the RO-Crate in.')(f)
    f = click.option('--name', required=False, type=str, help='Override the default RO-Crate name (extracted from repository).')(f)
    f = click.option('--description', required=False, type=str, help='Override the default RO-Crate description (extracted from repository).')(f)
    f = click.option('--author', required=False, multiple=True, type=str, help='Override authors (extracted from repository). Can be used multiple times. If not provided, repository authors are used.')(f)
    f = click.option('--keywords', required=False, multiple=True, type=str, help='Override keywords (extracted from repository). Can be used multiple times.')(f)
    f = click.option('--license', required=False, type=str, help='Override the default RO-Crate license URL (extracted from repository).')(f)
    f = click.option('--publication-date', required=False, type=str, help='Override publication date (ISO format, extracted from repository).')(f)
    f = click.option('--doi', required=False, type=str, help='Override DOI (extracted from repository).')(f)
    f = click.option('--crate-version', required=False, type=str, default="1.0", help='Set the version for the RO-Crate itself.')(f)
    f = click.option('--organization-name', required=False, type=str, help='Set the organization name for the RO-Crate.')(f)
    f = click.option('--project-name', required=False, type=str, help='Set the project name for the RO-Crate.')(f)
    f = click.option('--include-files/--exclude-files', default=True, help='Whether to include metadata for files (default: include).')(f)
    return f

@import_group.command('figshare')
@click.argument('article-id', type=str)
@click.option('--token', required=False, type=str, help='Figshare API token (optional, for private articles).')
@generic_importer_options
@click.pass_context
def import_figshare(
    ctx: click.Context,
    article_id: str,
    output_dir: pathlib.Path,
    name: Optional[str],
    description: Optional[str],
    author: Optional[Tuple[str]],
    keywords: Optional[Tuple[str]],
    license: Optional[str],
    publication_date: Optional[str],
    doi: Optional[str],
    crate_version: str,
    organization_name: Optional[str],
    project_name: Optional[str],
    include_files: bool,
    token: Optional[str]
):
    """Pulls Figshare article data and converts it into an RO-Crate.

    ARTICLE_ID: The Figshare article ID (e.g., 1234567).
    """
    click.echo(f"Importing Figshare article {article_id}...")

    try:
        research_data_instance = ResearchData.from_repository(
            repository_type='figshare',
            identifier=article_id,
            token=token,
            include_files=include_files
        )
        click.echo(f"Successfully fetched data for Figshare article: {research_data_instance.title}")

        # Override attributes if CLI options are provided
        if name: research_data_instance.title = name
        if description: research_data_instance.description = description
        if author: research_data_instance.authors = list(author)
        if keywords: research_data_instance.keywords = list(keywords)
        if license: research_data_instance.license = license
        if publication_date: research_data_instance.publication_date = publication_date
        if doi: research_data_instance.doi = doi

        # Call to_rocrate with crate-specific options
        rocrate_guid = research_data_instance.to_rocrate(
            output_dir=str(output_dir),
            crate_version=crate_version,
            organization_name=organization_name,
            project_name=project_name
        )

        click.echo(f"Successfully created RO-Crate for Figshare article {article_id}.")
        click.echo(f"RO-Crate Root GUID: {rocrate_guid}")
        click.echo(f"RO-Crate saved to: {output_dir.resolve()}")

    except ValueError as e:
        click.echo(f"ERROR: {e}", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
        traceback.print_exc()
        ctx.exit(1)


@import_group.command('dataverse')
@click.argument('dataset-doi', type=str)
@click.option('--server-url', default='https://dataverse.harvard.edu', show_default=True, help='Dataverse server URL.')
@click.option('--token', required=False, type=str, help='Dataverse API token (optional, for restricted datasets).')
@generic_importer_options
@click.pass_context
def import_dataverse(
    ctx: click.Context,
    dataset_doi: str,
    output_dir: pathlib.Path,
    name: Optional[str],
    description: Optional[str],
    author: Optional[Tuple[str]],
    keywords: Optional[Tuple[str]],
    license: Optional[str],
    publication_date: Optional[str],
    doi: Optional[str], 
    crate_version: str,
    organization_name: Optional[str],
    project_name: Optional[str],
    include_files: bool,
    server_url: str,
    token: Optional[str]
):
    """Pulls Dataverse dataset and converts it into an RO-Crate.

    DATASET_DOI: The DOI or persistent identifier of the Dataverse dataset (e.g., doi:10.7910/DVN/XXXXX).
    """
    click.echo(f"Importing Dataverse dataset {dataset_doi} from {server_url}...")

    try:
        research_data_instance = ResearchData.from_repository(
            repository_type='dataverse',
            identifier=dataset_doi,
            server_url=server_url,
            token=token,
            include_files=include_files
        )
        click.echo(f"Successfully fetched data for Dataverse dataset: {research_data_instance.title}")

        # Override attributes if CLI options are provided
        if name: research_data_instance.title = name
        if description: research_data_instance.description = description
        if author: research_data_instance.authors = list(author)
        if keywords: research_data_instance.keywords = list(keywords)
        if license: research_data_instance.license = license
        if publication_date: research_data_instance.publication_date = publication_date
        if doi: 
            research_data_instance.doi = doi
        elif not research_data_instance.doi: 
            research_data_instance.doi = dataset_doi


        # Call to_rocrate with crate-specific options
        rocrate_guid = research_data_instance.to_rocrate(
            output_dir=str(output_dir),
            crate_version=crate_version,
            organization_name=organization_name,
            project_name=project_name
        )

        click.echo(f"Successfully created RO-Crate for Dataverse dataset {dataset_doi}.")
        click.echo(f"RO-Crate Root GUID: {rocrate_guid}")
        click.echo(f"RO-Crate saved to: {output_dir.resolve()}")

    except ValueError as e:
        click.echo(f"ERROR: {e}", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
        traceback.print_exc()
        ctx.exit(1)
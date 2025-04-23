import click
from pathlib import Path
from typing import Optional

from fairscape_cli.publish.publish_tools import DataversePublisher, DataCitePublisher, FairscapePublisher

@click.group('publish')
def publish_group():
    """Publish RO-Crates to external repositories."""
    pass

@publish_group.command('fairscape')
@click.option('--rocrate', required=True, type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path), help='Path to the RO-Crate directory or zip file.')
@click.option('--username', required=True, envvar='FAIRSCAPE_USERNAME', help='Fairscape username (can also be set via FAIRSCAPE_USERNAME env var).')
@click.option('--password', required=True, envvar='FAIRSCAPE_PASSWORD', help='Fairscape password (can also be set via FAIRSCAPE_PASSWORD env var).')
@click.option('--api-url', default='https://fairscape.net/api', help='Fairscape API URL (default: https://fairscape.net/api).')
def publish_fairscape(rocrate: Path, username: str, password: str, api_url: str):
    """Upload RO-Crate directory or zip file to Fairscape."""
    publisher = FairscapePublisher(base_url=api_url)
    publisher.publish(rocrate_path=rocrate, username=username, password=password)

@publish_group.command('dataverse')
@click.option('--rocrate', required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path), help='Path to the ro-crate-metadata.json file.')
@click.option('--url', required=True, help='Base URL of the target Dataverse instance (e.g., https://dataverse.example.edu).')
@click.option('--collection', required=True, help='Alias of the target Dataverse collection to publish into.')
@click.option('--token', required=True, envvar='DATAVERSE_API_TOKEN', help='Dataverse API token (can also be set via DATAVERSE_API_TOKEN env var).')
@click.option('--authors-csv', type=click.Path(exists=True, dir_okay=False, path_type=Path), help='Optional CSV file with author details (name, affiliation, orcid). Requires "name" column header.')
def publish_dataverse(rocrate: Path, url: str, collection: str, token: str, authors_csv: Optional[Path]):
    """Publish RO-Crate metadata as a new dataset to Dataverse."""
    publisher = DataversePublisher(base_url=url, collection_alias=collection)
    publisher.publish(rocrate_path=rocrate, api_token=token, authors_csv_path=str(authors_csv) if authors_csv else None)

@publish_group.command('doi')
@click.option('--rocrate', required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path), help='Path to the ro-crate-metadata.json file.')
@click.option('--prefix', required=True, help='Your DataCite DOI prefix (e.g., 10.1234).')
@click.option('--username', required=True, envvar='DATACITE_USERNAME', help='DataCite API username (repository ID, e.g., MEMBER.REPO) (can use DATACITE_USERNAME env var).')
@click.option('--password', required=True, envvar='DATACITE_PASSWORD', help='DataCite API password (can use DATACITE_PASSWORD env var).')
@click.option('--api-url', default='https://api.datacite.org', help='DataCite API URL (default: https://api.datacite.org, use https://api.test.datacite.org for testing).')
@click.option('--event', type=click.Choice(['publish', 'register', 'hide'], case_sensitive=False), default='publish', help="DOI event type: 'publish' (make public), 'register' (create draft), 'hide' (make findable but hide metadata).")
def publish_doi(rocrate: Path, prefix: str, username: str, password: str, api_url: str, event: str):
    """Mint or update a DOI on DataCite using RO-Crate metadata."""
    repository_id = username
    publisher = DataCitePublisher(prefix=prefix, repository_id=repository_id, api_url=api_url)
    publisher.publish(rocrate_path=rocrate, username=username, password=password, event=event)
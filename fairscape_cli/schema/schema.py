import click

from fairscape_cli.models import (
    ImageFormatEnum,
    ColorspaceEnum,
    FiletypeEnum,
    DatatypeEnum
)



@click.group('schema')
def schema():
    pass

@schema.command('create')
def create():
    pass

@schema.command('validate')
def validate():
    pass

@schema.command('add-column')
def add_column():
    pass

import pathlib
from fairscape_models import ROCrate as ROCrateModel
from fairscape_cli.models import (
    Software,
    Dataset,
    Computation
)
from prettytable import PrettyTable
from typing import (
    Optional,
    Union,
    List
)

class ROCrate(ROCrateModel):
    guid: Optional[str]
    metadataType: str = "https://schema.org/Dataset"
    name: Optional[str]
    path: pathlib.Path
    metadataGraph: Optional[List[Union[Dataset,Software, Computation]]]

    def print_contents(self):
        rocrate_table = PrettyTable()

        rocrate_table.field_names= ['ro_crate', '@id', 'type', 'name']
        for metadata_element in self.graph:
            rocrate_table.add_row(
                [
                    "*", 
                    metadata_element.guid, 
                    metadata_element.type, 
                    metadata_element.name
                ]
            )

        return rocrate_table


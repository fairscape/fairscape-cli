from fairscape_models import ROCrate as ROCrateModel
from prettytable import PrettyTable

class ROCrate(ROCrateModel):
    path: str

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



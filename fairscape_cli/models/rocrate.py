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
    guid: Optional[str] = ""
    metadataType: str = "https://schema.org/Dataset"
    name: Optional[str]
    projectName: Optional[str]
    organizationName: Optional[str]
    path: pathlib.Path
    metadataGraph: Optional[List[Union[Dataset,Software, Computation]]]

    def createCrateFolder(self):
        self.path.mkdir(exist_ok=False)
        

    def initCrate(self):
        """Create an rocrate at the current working directory, initilize the 
        """

        # TODO url encode all string values for organization_name and project_name
        organization_guid = f"ark:/{self.organizationName.replace(' ', '_')}"
        project_guid = organization_guid + f"/{self.projectName.replace(' ', '_')}"

        if self.guid == "":
            guid = project_guid + f"/{self.name.replace(' ', '_')}"

        # create basic rocrate metadata
        ro_crate_metadata_path = self.path / 'ro-crate-metadata.json'
        ro_crate_metadata_ark = self.guid + "/ro-crate-metadata.json"

        rocrate_metadata = {
            "@id": guid,
            "@context": {
                "EVI": "https://w3id.org/EVI#",
                "@vocab": "https://schema.org/"
            },
            "@type": "Dataset",
            "name": name,
            "isPartOf": [
                {
                    "@id": organization_guid,
                    "@type": "Organization",
                    "name": organization_name
                },
                {
                    "@id": project_guid,
                    "@type": "Project",
                    "name": project_name
                }
            ],
            "@graph": [
                {
                    "@id": ro_crate_metadata_ark,
                    "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                    "about": {"@id": guid},
                    "isPartOf": {"@id": guid},
                    "contentUrl": 'file://' + str(ro_crate_metadata_path),
                }
            ]  
        }

        # write out to file
        with ro_crate_metadata_path.open(mode="w") as metadata_file:
            json.dump(rocrate_metadata, metadata_file, indent=2)

        #TODO add to cache
     

    def addDataset(self, Dataset):
        pass


    def addSoftware(self, Software):
        pass


    def addComputation(self, Computation):
        pass


    def listContents(self):
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


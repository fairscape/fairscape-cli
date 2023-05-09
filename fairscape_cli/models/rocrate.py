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
        """Create an rocrate at the current working directory, initilize the ro-crate-metadata.json

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

        #TODO list all contents that need to be registered as warnings   

 
    def copyObject(source_filepath: str, destination_filepath: str):

        if source_filepath == "":
            raise Exception(message="source path is None")

        if destination_filepath == "":
            raise Exception(message="destination path is None") 

        # check if the source file exists 
        source_path = pathlib.Path(source_filepath)
        destination_path = pathlib.Path(destination_filepath)

        if source_path.exists() != True:
            raise Exception(
                message =f"sourcePath: {source_path} Doesn't Exist"
            )
    
        # TODO check that destination path is in the rocrate

        # copy the file into the destinationPath
        shutil.copy(source_path, destination_path)



    def registerObject(self, model: Union[Dataset, Software, Computation]):
        ''' Add a specified peice of metadata to the graph of an ROCrate

        Marshals a given model into JSON-LD, opens the ro-crate-metadata.json,
        appends the new metadata to the @graph, and overwrites the ro-crate-metadata.json
        '''

        metadata_path = self.path

        # open the ro-crate-metadata.json
        with metadata_path.open("r") as rocrate_metadata_file:
            rocrate_metadata = json.load(rocrate_metadata_file)

            # TODO check if the file is redundant
     
            # add to the @graph
            rocrate_metadata['@graph'].append(model.dict(by_alias=True))
        
        # overwrite the ro-crate-metadata.json file
        with metadata_path.open("w") as f:
            json_object = json.dumps(rocrate_metadata, indent=2)
            f.write(json_object)



    def registerDataset(self, Dataset):
        self.registerObject(model=Dataset)
        

    def registerSoftware(self, Software):
        self.registerObject(model=Software)


    def registerComputation(self, Computation):
        self.registerComputation(model=Computation)


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


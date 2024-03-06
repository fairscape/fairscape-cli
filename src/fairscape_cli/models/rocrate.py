from fairscape_cli.models import (
    Software,
    Dataset,
    Computation
)
from fairscape_cli.models.utils import GenerateDatetimeSquid
from fairscape_cli.config import (
    DEFAULT_CONTEXT,
    NAAN
)

import pathlib
import shutil
import json
from prettytable import PrettyTable
from pydantic import (
    BaseModel,
    computed_field,
    Field,
)
from typing import (
    Optional,
    Union,
    List
)


class ROCrate(BaseModel):
    guid: Optional[str] = Field(alias="@id", default=None)
    metadataType: str = Field(alias="@type", default="https://schema.org/Dataset")
    name: str = Field(max_length=200)
    description: str = Field(min_length=10)
    keywords: List[str] = Field(...)
    projectName: Optional[str] = Field(default=None)
    organizationName: Optional[str] = Field(default=None)
    path: pathlib.Path
    metadataGraph: Optional[List[Union[Dataset,Software, Computation]]]

    def generate_guid(self) -> str:
        if self.guid is None:
            sq = GenerateDatetimeSquid()
            self.guid = f"ark:{NAAN}/rocrate-{self.name.replace(' ', '-').lower()}-{sq}"
        return self.guid



    def createCrateFolder(self):
        self.path.mkdir(parents=True, exist_ok=True)
        

    def initCrate(self):
        """Create an rocrate at the current working directory, initilize the ro-crate-metadata.json

        """

        # create basic rocrate metadata
        ro_crate_metadata_path = self.path / 'ro-crate-metadata.json'

        # create guid if none exists
        self.generate_guid()

        rocrate_metadata = {
            "@id": self.guid,
            "@context": DEFAULT_CONTEXT,
            "@type": "EVI:Dataset",
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords,
            "isPartOf": [],
            "@graph": []  
        }

        if self.organizationName:
            organization_guid = f"ark:{NAAN}/organization-{self.organizationName.lower().replace(' ', '-')}-{GenerateDatetimeSquid()}"
            rocrate_metadata['isPartOf'].append(
                {
                    "@id": organization_guid,
                    "@type": "Organization",
                    "name": self.organizationName
                }
            )

        if self.projectName:
            project_guid = f"ark:{NAAN}/project-{self.projectName.lower().replace(' ', '-')}-{GenerateDatetimeSquid()}"
            rocrate_metadata['isPartOf'].append(
                {
                    "@id": project_guid,
                    "@type": "Project",
                    "name": self.projectName
                }
            )

        # write out to file
        with ro_crate_metadata_path.open(mode="w") as metadata_file:
            json.dump(rocrate_metadata, metadata_file, indent=2)

        #TODO add to cache

        #TODO list all contents that need to be registered as warnings   

 
    def copyObject(self, source_filepath: str, destination_filepath: str):

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

        metadata_path = pathlib.Path(self.path)

        with metadata_path.open("r+") as rocrate_metadata_file:
            rocrate_metadata = json.load(rocrate_metadata_file)
            
             # TODO assure no duplicative content
            
            # add to the @graph
            rocrate_metadata['@graph'].append(model.model_dump(by_alias=True))
            rocrate_metadata_file.seek(0)
            json.dump(rocrate_metadata, rocrate_metadata_file, indent=2)


    def registerDataset(self, Dataset):
        # TODO check for entailment
        self.registerObject(model=Dataset)
        

    def registerSoftware(self, Software):
        # TODO check for entailment
        self.registerObject(model=Software)


    def registerComputation(self, Computation):
        # TODO check for entailment
        self.registerObject(model=Computation)



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



def ReadROCrateMetadata(
        cratePath: str
)-> ROCrate:
    """ Given a path read the rocrate metadata into a pydantic model
    """

    # if cratePath has metadata.json inside
    if "ro-crate-metadata.json" in cratePath:
        metadataCratePath = cratePath
    else:
        metadataCratePath = cratePath + "/ro-crate-metadata.json"

    if cratePath.exists() != True:
        raise Exception(f'ro-crate-metadata.json not found at path {metadataCratePath}')

    with open(metadataCratePath, "r") as metadataFile:
        crateMetadata = json.load(metadataFile)
        readCrate = ROCrate.model_validate(crateMetadata)
    
    return readCrate


def AppendCrate(
    cratePath: pathlib.Path,
    elements: List[Union[Dataset, Software, Computation]]
):

    if len(elements) == 0:
        return None

    with cratePath.open("r+") as rocrate_metadata_file:
        rocrate_metadata = json.load(rocrate_metadata_file)
            
        # add to the @graph
        for register_elem in elements:
            rocrate_metadata['@graph'].append(
                register_elem.model_dump(
                    by_alias=True, 
                    exclude_none=True
                    ))
        
        rocrate_metadata_file.seek(0)
        json.dump(rocrate_metadata, rocrate_metadata_file, indent=2)

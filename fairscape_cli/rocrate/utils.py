import pathlib
import json

def generate_id(rocrate_metadata_path: pathlib.Path, name: str, metadata_type: str)-> str: 
    """
    Given ROCrate metadata generate an id for the element based on name
    """

    with rocrate_metadata_path.open('r') as rocrate_metadata_file:
        # read the rocrate_metadata
        rocrate_metadata = json.load(rocrate_metadata_file)
        rocrate_id = rocrate_metadata.get("@id")
       
    return f"{rocrate_id}/{name.replace(' ', '_')}-{metadata_type}"


class DestinationCrateError(Exception):
    
    def __init__(self, crate_path, destination_path):
        self.message = "\n".join([
            "Destination Filepath isnt inside the Crate",
            f"ROCrate Path: {str(crate_path)}", 
            f"DestinationPath: {str(destination_path)}"
            ])


def inside_crate(rocrate_path: pathlib.Path, destination_path: pathlib.Path):
    """
    Function to determine if the destination_path for a file is inside the crate
    """

    rocrate_path_absolute = rocrate_path.absolute()
    destination_path_absolute = destination_path.absolute() 

    for crate_part, dest_part in zip(rocrate_path_abolute.parts, 
        destination_path_absolute.parts):
        if crate_part != dest_part:
            raise DestinationCrateError(rocrate_path, destination_path) 
    


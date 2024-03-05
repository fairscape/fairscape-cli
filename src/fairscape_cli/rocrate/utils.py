class DestinationCrateError(Exception):    
    def __init__(self, crate_path, destination_path):
        self.message = "\n".join([
            "Destination Filepath isnt inside the Crate",
            f"ROCrate Path: {str(crate_path)}", 
            f"DestinationPath: {str(destination_path)}"
            ])

    


import pathlib
import shutil
import hashlib
import os
from pydantic import (
    BaseModel,
    Field,
    ConfigDict
)
from typing import (
    Optional
)


class BagIt(BaseModel):
    """
    The BagIt class represents the optional reserved metadata file bag-info.txt
    It is not considered a required element and created for human consumption.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True
    )
    rocrate_path: pathlib.Path
    bagit_path: pathlib.Path
    source_organization: str = Field(alias="Source-Organization")
    organization_address: str = Field(alias="Organization-Address")
    contact_name: str = Field(alias="Contact-Name")
    contact_phone: str = Field(alias="Contact-Phone")
    contact_email: str = Field(alias="Contact-Email")
    external_description: str = Field(alias="External-Description")
    bagging_date: str = Field(alias="Bagging-Date")
    bag_size: Optional[str] = Field(alias="Bag-Size")
    payload_Oxum: Optional[str] = Field(alias="Payload-Oxum")
    
 
    def create_bagit_directory(self):        
        self.bagit_path.mkdir(parents=True, exist_ok=True)        
        
        
    def create_bagit_declaration(self):
        """Create BagIt version and encoding.
        """
        VERSION = 1.0
        ENCODING = "UTF-8"
        bag_declaration_lines = [
            f"BagIt-Version: {VERSION}\n",
            f"Tag-File-Character-Encoding: {ENCODING}"
        ]
        bagit_declaration_path = self.bagit_path / 'bagit.txt'

        with bagit_declaration_path.open(mode="w") as bag_declaration_file:            
            bag_declaration_file.writelines(bag_declaration_lines)
                

    
    def create_payload_directory(self):
        """Create BagIt payload directory and populate objects from RO-Crate.
        """
        shutil.copytree(self.rocrate_path, self.bagit_path / 'data', dirs_exist_ok = True)

    

    def create_bagit_metadata(self):
        """Create BagIt metadata for human consumption with reserved keywords  
        """

        payload_dir = self.bagit_path / 'data'

        # Payload-Oxum requires octetstream sum and count for detecting incomplete bags before checksum validation
        octet_count = sum(f.stat().st_size for f in pathlib.Path(payload_dir).rglob('*') if f.is_file())
        stream_count = sum(f.is_file() for f in pathlib.Path(payload_dir).rglob('*'))

        self.payload_Oxum = f"{octet_count}.{stream_count}"

        # Bag-Size is the approximate size of the bag for human consumption
        octet_in_bytes = float(octet_count)
        octet_in_kilo_bytes = octet_in_bytes / 1024
        octet_in_mega_bytes = octet_in_kilo_bytes / 1024
        octet_in_giga_bytes = octet_in_mega_bytes / 1024
        octet_in_tera_bytes = octet_in_giga_bytes / 1024

        if octet_in_tera_bytes > 1:
            self.bag_size = f'{octet_in_tera_bytes:.2f} TB'
        elif octet_in_giga_bytes > 1:
            self.bag_size = f'{octet_in_giga_bytes:.2f} GB'
        elif octet_in_mega_bytes > 1:
            self.bag_size = f'{octet_in_mega_bytes:.2f} MB'
        elif octet_in_kilo_bytes > 1:
            self.bag_size = f'{octet_in_kilo_bytes:.2f} KB'
        else:
            self.bag_size = f'{octet_in_bytes} B'

        bagit_info_path = self.bagit_path / 'bag-info.txt'
        
        with bagit_info_path.open(mode="w") as bag_info_file:                        
            for key, value in self.model_dump(by_alias=True).items():                              
                if key != 'bagit_path' and key != 'rocrate_path':                    
                    bag_info_file.write('%s: %s\n' % (key, value))


    
    def create_payload_manifest_sha256(self):
        """Create checksum for each payload file for checking data integrity.
        """
        payload_dir = self.bagit_path / 'data'
        payload_manifest_path = self.bagit_path / 'manifest-sha256.txt'
        

        with payload_manifest_path.open(mode="w") as payload_manifest_file:
            for path in pathlib.Path(payload_dir).rglob("*"):
                if path.is_file():                    
                    sha256_hash = hashlib.sha256()                   
                    with open(path,"rb") as f:
                        for byte_block in iter(lambda: f.read(4096),b""):
                            sha256_hash.update(byte_block)                        
                        payload_manifest_file.write('%s %s\n' % (sha256_hash.hexdigest(), os.path.relpath(path, self.bagit_path)))
                        


    def create_payload_manifest_sha512(self):
        
        payload_dir = self.bagit_path / 'data'
        payload_manifest_path = self.bagit_path / 'manifest-sha512.txt'
        

        with payload_manifest_path.open(mode="w") as payload_manifest_file:
            for path in pathlib.Path(payload_dir).rglob("*"):
                if path.is_file(): 
                    sha512_hash = hashlib.sha512()                   
                    with open(path,"rb") as f:
                        for byte_block in iter(lambda: f.read(4096),b""):
                            sha512_hash.update(byte_block)                        
                        payload_manifest_file.write('%s %s\n' % (sha512_hash.hexdigest(), os.path.relpath(path, self.bagit_path)))
                        


    def create_payload_manifest_md5(self):
        
        payload_dir = self.bagit_path / 'data'
        payload_manifest_path = self.bagit_path / 'manifest-md5.txt'
        

        with payload_manifest_path.open(mode="w") as payload_manifest_file:
            for path in pathlib.Path(payload_dir).rglob("*"):
                if path.is_file(): 
                    md5_hash = hashlib.md5()                  
                    with open(path,"rb") as f:
                        for byte_block in iter(lambda: f.read(4096),b""):
                            md5_hash.update(byte_block)                        
                        payload_manifest_file.write('%s %s\n' % (md5_hash.hexdigest(), os.path.relpath(path, self.bagit_path)))

    
    def create_tag_manifest_md5(self):
        
        exclude_payload_dir = 'data'
        tag_manifest_path = self.bagit_path / 'tagmanifest-md5.txt'
        

        with tag_manifest_path.open(mode="w") as tag_manifest_file:
            for path in pathlib.Path(self.bagit_path).rglob("*"):
               if exclude_payload_dir not in path.parts: 
                #print(path.stem, path.name, path)
                if path.is_file() and not path.name.startswith('tagmanifest-'): 
                    md5_hash = hashlib.md5()                  
                    with open(path,"rb") as f:
                        for byte_block in iter(lambda: f.read(4096),b""):
                            md5_hash.update(byte_block)                        
                        tag_manifest_file.write('%s %s\n' % (md5_hash.hexdigest(), os.path.relpath(path, self.bagit_path)))

    
    def create_tag_manifest_sha256(self):
        
        exclude_payload_dir = 'data'
        tag_manifest_path = self.bagit_path / 'tagmanifest-sha256.txt'
        
        with tag_manifest_path.open(mode="w") as tag_manifest_file:
            for path in pathlib.Path(self.bagit_path).rglob("*"):
               if exclude_payload_dir not in path.parts: 
                #print(path.stem, path.name, path)
                if path.is_file() and not path.name.startswith('tagmanifest-'):  
                    sha256_hash = hashlib.sha256()                  
                    with open(path,"rb") as f:
                        for byte_block in iter(lambda: f.read(4096),b""):
                            sha256_hash.update(byte_block)                        
                        tag_manifest_file.write('%s %s\n' % (sha256_hash.hexdigest(), os.path.relpath(path, self.bagit_path)))


    def create_tag_manifest_sha512(self):
        
        exclude_payload_dir = 'data'
        tag_manifest_path = self.bagit_path / 'tagmanifest-sha512.txt'
        
        with tag_manifest_path.open(mode="w") as tag_manifest_file:
            for path in pathlib.Path(self.bagit_path).rglob("*"):
               if exclude_payload_dir not in path.parts: 
                print(path.stem, path.name, path)
                if path.is_file() and not path.name.startswith('tagmanifest-'):  
                    sha512_hash = hashlib.sha512()                  
                    with open(path,"rb") as f:
                        for byte_block in iter(lambda: f.read(4096),b""):
                            sha512_hash.update(byte_block)                        
                        tag_manifest_file.write('%s %s\n' % (sha512_hash.hexdigest(), os.path.relpath(path, self.bagit_path)))

    
                        

import pathlib
import shutil
import hashlib
import os
from prettytable import PrettyTable
from pydantic import BaseModel, ConfigDict, Field
from typing import (
    Optional,
    Union,
    List
)


class BagIt(BaseModel):
    rocrate_path: pathlib.Path
    bagit_path: pathlib.Path
    source_organization: str
    organization_address: str
    contact_name: str 
    contact_phone: str 
    contact_email: str 
    external_description: str
    bagging_date: str
    bag_size: Optional[str]
    payload_Oxum: Optional[str] 
    
    class Config:
        allow_population_by_field_name = True
        validate_assignment = True    
        fields={
            "source_organization": {                
                "alias": "Source-Organization"
            },
            "organization_address": {                
                "alias": "Organization-Address"
            },
            "contact_name": {
                "alias": "Contact-Name"
            },
            "contact_phone": {
                "alias": "Contact-Phone"
            },
            "contact_email": {
                "alias": "Contact-Email"
            },
            "external_description": {
                "alias": "External-Description"
            },
            "bagging_date": {
                "alias": "Bagging-Date"
            },
            "bag_size": {
                "alias": "Bag-Size"
            },
            "payload_Oxum": {
                "alias": "Payload-Oxum"
            }
        }

    def create_bagit_directory(self):        
        self.bagit_path.mkdir(parents=True, exist_ok=True)        
        
        

    def create_bagit_declaration(self):
        """Create a BagIt Declaration file
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
                

    
    def create_bagit_metadata(self):
        """Create a BagIt metadata file
        """

        payload_dir = self.bagit_path / 'data'
        octet_count = sum(f.stat().st_size for f in pathlib.Path(payload_dir).rglob('*') if f.is_file())
        #print(octet_count)
        stream_count = sum(f.is_file() for f in pathlib.Path(payload_dir).rglob('*'))
        #print(stream_count)



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
        
        self.payload_Oxum = f"{octet_count}.{stream_count}"

        bagit_info_path = self.bagit_path / 'bag-info.txt'
        print(self.dict())
        with bagit_info_path.open(mode="w") as bag_info_file:                        
            for key, value in self.dict(by_alias=True).items():              
                
                if key != 'bagit_path' and key != 'rocrate_path':
                    print(key, repr(key))
                    bag_info_file.write('%s: %s\n' % (key, value))


    def create_payload_directory(self):
        print(self.rocrate_path)
        shutil.copytree(self.rocrate_path, self.bagit_path / 'data')

    

    
    def create_payload_manifest_sha256(self):
        
        payload_dir = self.bagit_path / 'data'
        payload_manifest_path = self.bagit_path / 'manifest-sha256.txt'
        tag_manifest_path = self.bagit_path / 'tagmanifest-sha256.txt'

        with payload_manifest_path.open(mode="w") as payload_manifest_file, tag_manifest_path.open(mode="w") as tag_manifest_file:
            for path in pathlib.Path(payload_dir).rglob("*"):
                if path.is_file():                    
                    sha256_hash = hashlib.sha256()                   
                    with open(path,"rb") as f:
                        for byte_block in iter(lambda: f.read(4096),b""):
                            sha256_hash.update(byte_block)                        
                        payload_manifest_file.write('%s %s\n' % (sha256_hash.hexdigest(), os.path.relpath(path, self.bagit_path)))
                        tag_manifest_file.write('%s\n' % (sha256_hash.hexdigest()))


    def create_payload_manifest_sha512(self):
        
        payload_dir = self.bagit_path / 'data'
        payload_manifest_path = self.bagit_path / 'manifest-sha512.txt'
        tag_manifest_path = self.bagit_path / 'tagmanifest-sha512.txt'

        with payload_manifest_path.open(mode="w") as payload_manifest_file, tag_manifest_path.open(mode="w") as tag_manifest_file:
            for path in pathlib.Path(payload_dir).rglob("*"):
                if path.is_file(): 
                    sha512_hash = hashlib.sha512()                   
                    with open(path,"rb") as f:
                        for byte_block in iter(lambda: f.read(4096),b""):
                            sha512_hash.update(byte_block)                        
                        payload_manifest_file.write('%s %s\n' % (sha512_hash.hexdigest(), os.path.relpath(path, self.bagit_path)))
                        tag_manifest_file.write('%s\n' % (sha512_hash.hexdigest()))


    def create_payload_manifest_md5(self):
        
        payload_dir = self.bagit_path / 'data'
        payload_manifest_path = self.bagit_path / 'manifest-md5.txt'
        tag_manifest_path = self.bagit_path / 'tagmanifest-md5.txt'

        with payload_manifest_path.open(mode="w") as payload_manifest_file, tag_manifest_path.open(mode="w") as tag_manifest_file:
            for path in pathlib.Path(payload_dir).rglob("*"):
                if path.is_file(): 
                    md5_hash = hashlib.md5()                  
                    with open(path,"rb") as f:
                        for byte_block in iter(lambda: f.read(4096),b""):
                            md5_hash.update(byte_block)                        
                        payload_manifest_file.write('%s %s\n' % (md5_hash.hexdigest(), os.path.relpath(path, self.bagit_path)))
                        tag_manifest_file.write('%s\n' % (md5_hash.hexdigest()))

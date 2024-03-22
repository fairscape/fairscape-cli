# Changelog

All notable changes to this project will be documented in this file.

## 0.2.0 (2024-03-25)

[GitHub release](https://github.com/fairscape/fairscape-cli/releases/tag/0.2.0)


### What's Changed

* Stable and unique GUIDs are used as PIDs 
* Added commands to create and validate schemas
* RO-Crate
   - Interfaces and methods were improved for generating and transferring objects and their metadata
   - Unit tests were added

* Schema generation
   - Pydantic data validation models to describe schemas for dataset objects were defined
   - Added support for tabular dataset object
   - Six native JSON datatypes are currently supported for describing the schemas
   - Loading of local and default schemas is currently supported
   - Unit tests were added

* Schema validation
   - A feature to validate the generated schema against the dataset was added
   - A simple custom parsing of the schema has been implemented
   - Validation includes examining data types, location of the header, regex pattern, and constraints on the values
   - An option for mapping to a standard vocabulary term from an existing ontology has been added
   - Helpful messages are shown at the end of the validation step

* Examples have been added to the documentation to illustrate the invocations of the commands

# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Changed

* Datasheet visual redesign: hero header with version/DOI/license/size badges, stat cards, pure-SVG AI-readiness donut, carded sections, improved print/PDF styling. Templates are themed via CSS custom properties in `base.html`.
* Evidence graph HTML rebuilt from a 1,000-line Python f-string into a Jinja template (`templates/evidence_graph/`) plus a real JavaScript asset. React/ReactDOM/dagre are now vendored and inlined, so the generated file is fully self-contained and works offline (previously required CDN access). Added a node-type legend, hover tooltips, and a reset-view button.
* Embedded RO-Crate JSON in evidence graph HTML is now `<`-escaped, preventing `</script>` breakout from metadata values.
* RO-Crate root entities are resolved via the `ro-crate-metadata.json` descriptor's `about` reference instead of assuming `@graph[1]`.
* Metadata files are rewritten atomically (temp file + rename), so an interrupted run can no longer corrupt `ro-crate-metadata.json`.
* Subcrate metadata is loaded and validated once per datasheet build instead of three times.
* Datasheet generation errors now go through `logging` instead of bare prints.

### Fixed

* `build datasheet --template-dir` was accepted but silently ignored; it is now honored.

## 0.2.0 (2024-03-28)

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

# fairscape-cli
A utility for packaging objects and validating metadata for FAIRSCAPE.

---
**Documentation**: [https://fairscape.github.io/fairscape-cli/](https://fairscape.github.io/fairscape-cli/)
---

## Features

fairscape-cli provides a Command Line Interface (CLI) that allows the client side to create:

* [RO-Crate](https://www.researchobject.org/ro-crate/) - a light-weight approach to packaging research data with their metadata. The CLI allows users to:
    * Create Research Object Crates (RO-Crates)
    * Add (transfer) digital objects to the RO-Crate
    * Register metadata of the objects
    * Describe the schema of tabular dataset objects as metadata and perform validation.

## Requirements

Python 3.8+

## Installation
```console
$ pip install fairscape-cli
```

## Minimal example 

### Basic command

* Show all commands, arguments, and options

```console
$ fairscape-cli --help
```

* Create an RO-Crate

```console
$ fairscape-cli rocrate create \
  --name "test rocrate" \
  --description "Example RO Crate for Tests" \  
  --organization-name "UVA" \
  --project-name "B2AI"  \
  --keywords "b2ai" \
  --keywords "cm4ai" \
  --keywords "U2OS" \
  "/path/to/test_rocrate"
  ```

* Add a dataset to the RO-Crate

```console
$ fairscape-cli rocrate create \
  --name "test rocrate" \
  --description "Example RO Crate for Tests" \  
  --organization-name "UVA" \
  --project-name "B2AI"  \
  --keywords "b2ai" \
  --keywords "cm4ai" \
  --keywords "U2OS" \
  "/path/to/test_rocrate"
  ```

* Add a software to the RO-Crate

```console
$ fairscape-cli rocrate create \
  --name "test rocrate" \
  --description "Example RO Crate for Tests" \  
  --organization-name "UVA" \
  --project-name "B2AI"  \
  --keywords "b2ai" \
  --keywords "cm4ai" \
  --keywords "U2OS" \
  "/path/to/test_rocrate"
  ```

* Register a computation to the RO-Crate

```console
$ fairscape-cli rocrate register computation \
  --name "calibrate pairwise distance" \
  --run-by "Qin, Y." \
  --date-created "2021-05-23" \
  --description "Average the predicted proximities" \
  --keywords "b2ai" \
  --keywords "cm4ai" \
  --keywords "U2OS" \
  "/path/to/test_rocrate"
  ```


## Contribution

If you'd like to request a feature or report a bug, please create a [GitHub Issue](https://github.com/fairscape/fairscape-cli/issues) using one of the templates provided.


## License

This project is licensed under the terms of the MIT license.

# fairscape-cli
----------------
A data validation and packaging utility for the FAIRSCAPE ecosystem.

## Features

fairscape-cli provides a Command Line Interface (CLI) that allows the client side remote teams to create:

* [RO-Crate](https://www.researchobject.org/ro-crate/) - a light-weight approach to packaging research data with their metadata. The CLI allows users to:
    * Add digital objects to an RO-Crate
    * Register metadata about the objects
    * Validate metadata about the objects (work in progress)
* [BagIt](https://datatracker.ietf.org/doc/html/rfc8493) - a packaging format for storing and transferring digital content in a `Bag` from an existing RO-Crate. The CLI allows users to create a bagit by creating:
    * a required element payload directory `data/` containing digital content (i.e. objects in RO-Crate)
    * a required element bag declaration `bag.txt` containing the version and encoding information 
    * a required element payload manifest `manifest-algorithm.txt` containing checksum and file path
    * an optional element bag metadata `bag-info.txt` containing reserved metadata elements as key, value pairs.
    * an optional element tag manifest `tagmanifest-algorithm.txt` containing checksum.


!!! note

    The prerequisite of creating a BagIt is to create RO-Crate. The FAIRSCAPE ecosystem 
    currently accepts reserved metadata elements that are generated when RO-Crate is created
    by the CLI. Therefore, adding BagIt support will become easier in the future when the 
    metadata is also included.  





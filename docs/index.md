# fairscape-cli
----------------
A utility for packaging digital objects and validating their metadata for the FAIRSCAPE ecosystem.

## Features

fairscape-cli provides a Command Line Interface (CLI) that allows the client side to create:

* [RO-Crate](https://www.researchobject.org/ro-crate/) - a light-weight approach to packaging research data with their metadata. The CLI allows users to:
    * Create Research Object Crates (RO-Crates)
    * Add (transfer) digital objects to the RO-Crate
    * Register metadata of the objects
    * Describe schema of dataset objects (CSV, TSV) as metadata and perform shallow validation.    
* [BagIt](https://datatracker.ietf.org/doc/html/rfc8493) - a packaging format for storing and transferring digital content in a `Bag` from an existing RO-Crate. This is an experimental feature where the CLI allows users to create a BagIt by creating:
    * a required element payload directory `data/` containing digital content (i.e. objects in RO-Crate)
    * a required element bag declaration `bag.txt` containing the version and encoding information 
    * a required element payload manifest `manifest-algorithm.txt` containing checksum and file path
    * an optional element bag metadata `bag-info.txt` containing reserved metadata elements as key, value pairs.
    * an optional element tag manifest `tagmanifest-algorithm.txt` containing checksum.




!!! note

    The prerequisite of creating a BagIt is to create an RO-Crate. The FAIRSCAPE ecosystem 
    currently accepts reserved metadata elements that are generated when an RO-Crate is created
    by the CLI. Therefore, supporting BagIt will become easier in the future when the 
    metadata is also included.  




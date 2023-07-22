# fairscape-cli
----------------
A data validation and packaging utility for the FAIRSCAPE ecosystem.

# Features

The fairscape-cli provides a command line interface that allows the client side remote teams to create:

* [RO-Crate](https://www.researchobject.org/ro-crate/) - a light-weight approach to packaging research data with their metadata. The CLI allows:
    * Adding digital objects to an RO-Crate
    * Registering metadata about the objects
    * Validating metadata about the objects (work in progress)
* [BagIt](https://datatracker.ietf.org/doc/html/rfc8493) - a packaging format for storing and transferring digital content in a `Bag`. The CLI allows:
    * Adding a required element bag declaration `bag.txt` contaiing the version and encoding information 
    * Adding a required element payload directory `data/` containing digital content
    * Adding a required element payload manifest `manifest-algorithm.txt` containing checksum and file path
    * Adding an optional element bag metadata `bag-info.txt` containing reserved metadata elements as key, value pairs.
    * Adding an optional element tag manifest `tagmanifest-algorithm.txt` containing checksum.







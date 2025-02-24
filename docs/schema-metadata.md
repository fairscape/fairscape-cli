The Command Line Interface (CLI) offers users more than just the ability to transfer and register dataset objects. It also enables the addition of metadata to describe schemas and perform basic validation of objects. As of this release, the CLI solely supports tabular datasets.


## Tabular Dataset
To illustrate, let's consider the tabular data frame named `APMS_embedding_MUSIC.csv`. This particular dataset comprises 1026 columns. The first column, `Internal Experiment Identifier`, identifies the experiment that generated the source data, while the second column, `Gene Symbol`, contains the Gene name for the bait protien. The remaining columns, from `Embedding0` to `Embedding1023`, are a 1024 length embedding vector. The original data frame has no headers, but after consulting with a domain expert, headers are added for clarity, and based on these headers, the schema will be described.  


|Internal Experiment Identifier|Gene Symbol|Embedding0|Embedding1|Embedding2| ... |Embedding1023|
|------------------------------|-----------|----------|----------|----------|-----|-------------|
|APMS_1                        |RRS1       |0.07591   |0.161315  |-0.025731 |...  |-0.172205    |
|APMS_2                        |SNRNP70    |-0.019872 |0.083736  |0.151332  |...  |0.042429     |
|APMS_3                        |RPL18      |0.067353  |0.099565  |0.308037  |...  |0.049538     |
|APMS_4                        |JMJD6      |0.087387  |-0.17969  |0.036929  |...  |0.068675     |
|APMS_5                        |NCAPH2     |0.007115  |0.118820  |-0.059649 |...  |0.119648     |
|APMS_6                        |BSG	       |0.143906  |-0.034937 |-0.141535 |...  |-0.178751    |
|APMS_7                        |FAM189B	   |-0.107395 |0.284882  |0.065763  |...  |0.044294     |
|APMS_8                        |MRPS11	   |-0.051772 |0.045301  |0.08211   |...  |0.079971     |
|APMS_9                        |TRIM28	   |-0.17398  |0.209120  |0.021203  |...  |-0.092368    |
|APMS_10                       |LAMP3	   |0.048065  |0.087677  |0.000867  |...  |0.047628     |


Throughout the rest of the document, we will use this tabular dataset as a guide to walk through the step-by-step process of creating, populating and validating the schema.   

### Create schema 
To create a schema for a tabular dataset, the `create-tabular` command must be invoked, requiring a `name`, a brief `description`, a `separator` character, and an optional boolean value for `header` to specify the presence of column headers. Once created, the schema will be located in the destination specified by the `SCHEMA_FILE`.

```bash
fairscape-cli schema create-tabular [OPTIONS] SCHEMA_FILE

Options:
  --name TEXT         [required]
  --description TEXT  [required]
  --guid TEXT
  --separator TEXT    [required]
  --header BOOLEAN
  --help              Show this message and exit.
```

In the schema creation example below, the symbol `,` (comma) is used as the `separator` and the `header` is set to `False`. The CLI will autogenerate a value for the `guid`. 

```bash
fairscape-cli schema create-tabular \
    --name 'APMS Embedding Schema' \
    --description 'Tabular format for APMS music embeddings from PPI networks from the music pipeline from the B2AI Cellmaps for AI project' \
    --separator ',' \
    --header False \
    ./schema_apms_music_embedding.json
```

### Populate schema
To populate the schema for a tabular dataset, we describe its syntactic and semantic properties through a series of unique properties, each representing a single column or an array of similar columns. To add a property, we use the `fairscape-cli schema add-property` command.

The first step in adding a property is to choose the datatype it represents in the column or array of columns. For example, if a column represents a `string` datatype, we create a string property by using the `fairscape-cli schema add-property string` command. We can use a similar command for other datatypes as well. The CLI supports five datatypes for a tabular dataset, which are listed in the table below.

| Datatype       | Description      |
| -------------- | -----------------|
| `string`       | Strings of text  |
| `number`       | Any numeric type |
| `integer`      | Integral numbers |
| `array`        | Ordered elements |
| `boolean`      | True and False   |

After choosing the datatype, we must fill in additional information about the column or array of columns it represents. The table headers below display all available options for each datatype. For a `string` property, this includes a unique `name`, an integer value for the `index` (where 0 represents the first column, 1 represents the second, and so on), a human-readable `description`, a standard vocabulary term for the `value-url`, and a regular expression for the data `pattern` in that column. While the first three options are required, the rest are optional.

| Datatype |   name   |   index  | description | value-url |  pattern | items-datatype | min-items | max-items | unique-items |
|----------|:--------:|:--------:|:-----------:|:---------:|:--------:|:--------------:|:---------:|:---------:|:------------:|
| `string` | required | required |   required  |  optional | optional |                |           |           |              |
| `number` | required | required |   required  |  optional |          |                |           |           |              |
| `integer`| required | required |   required  |  optional |          |                |           |           |              |
| `array`  | required | required |   required  |  optional |          |    required    |  optional |  optional |   optional   |
| `boolean`| required | required |   required  |  optional |          |                |           |           |              |

To view all available options and arguments, including those for the string datatype, we can use the command `fairscape-cli schema add-property string --help`, which will display a complete list of options.

```bash
fairscape-cli schema add-property string [OPTIONS] SCHEMA_FILE

Options:
  --name TEXT         [required]
  --index INTEGER     [required]
  --description TEXT  [required]
  --value-url TEXT
  --pattern TEXT
  --help              Show this message and exit.
```

#### Add a String Property

Columns index 0 and 1 have string values. 
Both can be constrained with an optional regex pattern.
For our first column we have the experiment identifier, and add this to the schema with the following command.

```bash
fairscape-cli schema add-property string \
    --name 'Experiment Identifier' \
    --index 0 \
    --description 'Identifier for the APMS experiment responsible for generating the raw PPI used to create this embedding vector' \
    --pattern '^APMS_[0-9]*$' \
    ./schema_apms_music_embedding.json
```

For the second column we have Gene Symbols for values, 
We can choose then to provide the optional flag `--value-url` to align these values to an ontology.
Using the (EDAM ontology of bioscientific data analysis and data management)[], we can specify that these are Gene Symbols.
This can be usefull for specifying the Database of a particular Gene Identifier. Which enables linking Identifiers across databases.
Any ontology can be used to align data.


```bash
fairscape-cli schema add-property string \
    --name 'Gene Symbol' \
    --index 1 \
    --description 'Gene Symbol for the APMS bait protien' \
    --pattern '^[A-Za-z0-9\-]*$' \
    --value-url 'http://edamontology.org/data_1026' \
    ./schema_apms_music_embedding.json
```

#### Add an Array Property

Instead of registering properties for 1024 individual columns we can add a property for an array of 1024 elements.
We can accomplish this with a slice expression for the index.
The following slice expressions are supported.

|Slice Expression |Description                            |
|-----------------|---------------------------------------|
|`i::`            | starting at index i to the final index|
|`::i`            | starting at index 0 to index i        |
|`i:j`            | starting at index i to index j        |

We then must specify that the type of the data inside this array is numeric.
Items are not contstrained to unique values.
And that for every row we expect there to be exactly 1024 elements.

```bash
fairscape-cli schema add-property array \
    --name 'MUSIC APMS Embedding' \
    --index '2::' \
    --description 'Embedding Vector values for genes determined by running node2vec on APMS PPI networks. Vector has 1024 values for each bait protien' \
    --items-datatype 'number' \
    --unique-items False \
    --min-items 1024 \
    --max-items 1024 \
    ./schema_apms_music_embedding.json
```

### Generated schema

Looking at our schema we should have a json document equivalent to the following
```json
{
    "@context": {
        "@vocab": "https://schema.org/",
        "EVI": "https://w3,org/EVI#"
    },
    "@id": "ark:59852/schema-apms-music-embedding-izNjXSs",
    "@type": "EVI:Schema",
    "name": "APMS Embedding Schema",    
    "description": "Tabular format for APMS music embeddings from PPI networks from the music pipeline from the B2AI Cellmaps for AI project",    
    "properties": {    
    "Experiment Identifier": {    
        "description": "Identifier for the APMS experiment responsible for generating the raw PPI used to create this embedding vector",    
        "index": 0,                                 
        "valueURL": null,    
        "type": "string",    
        "pattern": "^APMS_[0-9]*$" 
    },                                 
    "Gene Symbol": {                                             
        "description": "Gene Symbol for the APMS bait protien",    
        "index": 1,    
        "valueURL": "http://edamontology.org/data_1026",    
        "type": "string",          
        "pattern": "^[A-Za-z0-9\-]*$"    
    },                                                                          
    "MUSIC APMS Embedding": {                                                                
        "description": "Embedding Vector values for genes determined by running node2vec on APMS PPI networks. Vector has 1024 values for each bait protien",    
        "index": "2::",                                                           
        "valueURL": null,    
        "type": "array",    
        "maxItems": 1024,                               
        "minItems": 1024,                                    
        "uniqueItems": false,                                        
        "items": {    
            "type": "number"
            }
        }                                                              
    },                        
    "type": "object",                                   
    "additionalProperties": true,                                               
    "required": ["Experiment Identifier", "Gene Symbol", "MUSIC APMS Embedding"],    
    "seperator": ",",                         
    "header": false,    
    "examples": []    
}
```

### Validate schema

With our schema we can execute the validation rules against some example data, and explore how errors are reported.
In the github repo, example data is provided to evaluate the same schema we have just created.
When validating against data where every row conforms to the schema, a simple success message is displayed.


```bash
fairscape-cli schema validate \
    --data ./examples/schemas/MUSIC_embedding/APMS_embedding_MUSIC.csv  \
    --schema ./examples/schemas/MUSIC_embedding/music_apms_embedding_schema.json

Validation Success
```

However when validating against data that contains issues, a table of errors is printed out.
For this purpose we provide some intentionally corrupted data to demonstrate how these errors are reported.

```bash
fairscape-cli schema validate \
    --data examples/schemas/MUSIC_embedding/APMS_embedding_corrupted.csv \
    --schema examples/schemas/MUSIC_embedding/music_apms_embedding_schema.json 

+-----+-----------------+----------------+-------------------------------------------------------+
| row |    error_type   | failed_keyword |                        message                        |
+-----+-----------------+----------------+-------------------------------------------------------+
|  3  |   ParsingError  |      None      | ValueError: Failed to Parse Attribute embed for Row 3 |
|  4  |   ParsingError  |      None      | ValueError: Failed to Parse Attribute embed for Row 4 |
|  0  | ValidationError |    pattern     |        'APMS_A' does not match '^APMS_[0-9]*$'        |
|  1  | ValidationError |    pattern     |          ' -8- ' does not match '^[A-Z0-9]*$'         |
|  2  | ValidationError |    pattern     |           '-`~' does not match '^[A-Z0-9]*$'          |
+-----+-----------------+----------------+-------------------------------------------------------+
```

When errors are found there are two sources of these errors.
Parsing errors which occur when attempting convert a row of tabular data into the specified json structure.
This can happen when either the number of specified rows is incorrect, or the data for a specific column cannot be coerced to the datatype specified of the schema.
When this occurs the row is marked as a failure and reported as a ParsingError. Rows that report a ParsingError are not validated against the jsonschema. 

Validation Errors occur when a data element violates the contraints specified by the schema.
In our example we show multiple examples of strings that defy the regex specified by the pattern attribute.
Other constraints include min and max for numeric and integer properties, length for string, etc.
In future work we will expand to cover the entire json schema specification.

#### Using default schemas

For conveineince a collection of default schemas are provided for the [Cell Maps for AI pipeline](https://github.com/idekerlab/cellmaps_pipeline).
These schemas have their own [repo](https://github.com/fairscape/cm4ai-schemas), and will track the progress of the pipeline as new data modalities are added.
These default schemas are packaged and provided as part of the fairscape-cli, and can be implemented using the respective identifier for the schema.
Examples for all of the existing default schemas are provided below.

```bash 
    # validate imageloader files
    fairscape-cli schema validate \
        --data "examples/schemas/cm4ai-rocrates/imageloader/samplescopy.csv" \
        --schema "ark:59852/schema-cm4ai-imageloader-samplescopy" 
    
    fairscape-cli schema validate \
        --data "examples/schemas/cm4ai-rocrates/imageloader/uniquecopy.csv" \
        --schema "ark:59852/schema-cm4ai-imageloader-uniquecopy"
       
    # validate image embedding outputs
    fairscape-cli schema validate \
        --data "examples/schemas/cm4ai-rocrates/image_embedding/image_emd.tsv" \
        --schema "ark:59852/schema-cm4ai-image-embedding-image-emd"
     
    fairscape-cli schema validate \
        --data "examples/schemas/cm4ai-rocrates/image_embedding/labels_prob.tsv" \
        --schema "ark:59852/schema-cm4ai-image-embedding-labels-prob"

    # validate apsm loader input
    fairscape-cli schema validate \
        --data "examples/schemas/cm4ai-rocrates/apmsloader/ppi_gene_node_attributes.tsv" \
        --schema "ark:59852/schema-cm4ai-apmsloader-gene-node-attributes"

    fairscape-cli schema validate \
        --data "examples/schemas/cm4ai-rocrates/apmsloader/ppi_edgelist.tsv" \
        --schema "ark:59852/schema-cm4ai-apmsloader-ppi-edgelist"

    # validate apms embedding 
    fairscape-cli schema validate \
        --data "examples/schemas/cm4ai-rocrates/apms_embedding/ppi_emd.tsv" \
        --schema "ark:59852/schema-cm4ai-apms-embedding"    

    # validate coembedding 
    fairscape-cli schema validate \
        --data "examples/schemas/cm4ai-rocrates/coembedding/coembedding_emd.tsv" \
        --schema "ark:59852/schema-cm4ai-coembedding"
```

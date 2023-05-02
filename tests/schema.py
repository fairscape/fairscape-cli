import pathlib
from fairscape_cli.models.schema import (
    ImageSchema,
    ImageValidation,
    ImageValidationException,
    ImagePathNotFoundException,
    DatatypeSchema,
    ColumnSchema,
    TabularDataSchema
)

apms_datatype = DatatypeSchema(
    name="APMS Experiment",
    description="Identifier for APMS experiment corresponding to the given node2vec vector",
    base="string",
    format="APMS_[0-9]*"
)

apms_column = ColumnSchema(
    name="APMS Experiment",
    description="APMS_column",
    ordered=False,
    required=True,
    number=0,
    datatype=apms_datatype,
    titles=["APMS Experiment"]
)

gene_symbol_datatype = DatatypeSchema(
    name="Gene Symbol",
    description="Gene Symbol in String Form",
    base="string",
    format="[A-Z0-9]*",
    minLength=3,
    maxLength=20
)

gene_symbol_column = ColumnSchema(
    name="Gene Symbol",
    description="gene symbol for apms embedding vector",
    ordered=False,
    required=True,
    number=0,
    datatype=gene_symbol_datatype,
    valueURL="http://edamontology.org/data_1026",
    titles=["Gene Symbol"]
)

embedding_column = ColumnSchema(
    name="embedding values",
    datatype = "float",
    required = True,
    description="node2vec embedding vector values for genes",
    number="2::",
    titles=["node2vec embedding vector"]
)

embedding_schema = TabularDataSchema(
    guid="ark:99999/schema/apms_embedding_schema",
    name="apms embedding schema",
    description="embedding vector values for genes determined by running node2vec on APMS networks",
    seperator=",",
    header=False,
    columns=[
        apms_column,
        gene_symbol_column,
        embedding_column
    ]
)

# test reading the data with the specified schema
embedding_path = pathlib.Path("./tests/data/APMS_embedding_MUSIC.csv")

embedding_df = embedding_schema.ReadTabularData(embedding_path)

col_schema = embedding_schema.columns[0]
column = embedding_df.iloc[:,0]

# if values are required check if any missing values are present
if col_schema.required == True:

    if any(column.isna()):
        raise Exception

    if any(column == None):
        pass

    # compare to passed null value
    if any(column == col_schema.null):
        raise Exception
        

match type(col_schema.datatype):

    case DatatypeSchema:
        print("DatatypeSchema")

        # get the base and format
        datatype_base = col_schema.datatype.base
        datatype_format = col_schema.datatype.format

        # get length

        # get maxLength
        
        # get minLength

        # get min

        # get maximum
        pass

    case DatatypeEnum:
        print("str")

        # cast the column as the 
        try:

        except ValueError as e:
            
        pass


# validation function

# col_schema.validate(column)

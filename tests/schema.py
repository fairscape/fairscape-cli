import pathlib
from fairscape_cli.models.schema import (
    ImageSchema,
    ImageValidation,
    ImageValidationException,
    ImagePathNotFoundException,
    DatatypeEnum,
    DatatypeSchema,
    ColumnSchema,
    TabularDataSchema,
    DataValidationException,
    NAValidationException,
    PathNotFoundException
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
def ValidateNullValue(null_value: str, column) -> None:
    if any(column.isna()): 
        raise NAValidationException()

    if any(column == None):
        raise NAValidationException()

    # compare to passed null value
    if any(column == null_value):
        raise NAValidationException()

    return None



# check if datatype matches schema

def ValidateDatatype(datatype_schema: DatatypeSchema, column) -> List[Exception]:
        validation_failures = []


        # validate length
        if datatype_schema.length != None:
            if all(len(column) == datatype_schema.length) != True:
                exception_message = "DatatypeValidationException: " + 
                    "length validation failure" +
                    f"\n all values do not have length {datatype_schema.length}"

                validation_failures.append(
                    DatatypeValidationException(
                        error="length", 
                        message=exception_message
                    ) 
                )
                

        # validate maxLength
        if datatype_schema.maxLength != None:
            if any(len(column)>datatype_schema.maxLength):
                exception_message = "DatatypeValidationException: " +
                "maxLength validation failure" +
                f"\n some values have lengths > maxLength {datatype_schema.maxLength}"

                validation_failures.append(
                    DatatypeValidationException(
                        error="maxLength", 
                        message=exception_message
                    ) 
                )

        # validate minLength
        if datatype_schema.minLength != None:
            if any(len(column)<datatype_schema.minLength):
                exception_message = "DatatypeValidationException: " +
                "minLength validation failure" +
                f"\n some values have lengths < minLength {datatype_schema.minLength}"

                validation_failures.append(
                    DatatypeValidationException(
                        error="minLength", 
                        message=exception_message
                    ) 
                )

        # get min
        if datatype_schema.min != None:
            if any(column<datatype_schema.min):

                exception_message = "DatatypeValidationException: " +
                "min validation failure" +
                f"\n some values have values < min {datatype_schema.min}"

                validation_failures.append(
                    DatatypeValidationException(
                        error="max", 
                        message=exception_message
                    ) 
                )

        # get maximum
        if datatype_schema.maximum != None:
            if any(column<datatype_schema.max):

                exception_message = "DatatypeValidationException: " +
                "max validation failure" +
                f"\n some values have values > max {datatype_schema.max}"

                validation_failures.append(
                    DatatypeValidationException(
                        error="max", 
                        message=exception_message
                    ) 
                )

        # validateFormat        
        # get the base and format
        datatype_base = col_schema.datatype.base
        datatype_format = col_schema.datatype.format

        try:
            ValidateDatatypeFormat(column, datatype_base, datatype_format)
        except Exception as e:
            validation_failures.append(e)

        return validation_failures


def ValidateDatatypeFormat(column, datatype_base, datatype_format)-> None:
    """ Validate format constraints for various types according to CSV On the Web Schema
    """

        switch datatype_base:
            case DatatypeEnum("str"):
                pass

            case DatatypeEnum(""):
                pass

    pass

def ValidateDatatypeEnum(column, datatype_enum: DatatypeEnum):
    pass


def ValidateColumn(column_schema: ColumnSchema, column):
    failures = []

    if column_schema.required == True:
        try:
            ValidateNullValue(column_schema.null, column) 
        except NAValidationException as e:
            print(e)

    # validate the datatype
    match type(col_schema.datatype):

        case DatatypeSchema():
            datatype_validation_failures = ValidateDatatype(column, datatype_schema) 


        case DatatypeEnum():
            try:
                ValidateDatatypeEnum(column, datatype_schema.datatype)
            except ValueError as e:
                failures.append(e) 


# validation function

# col_schema.validate(column)

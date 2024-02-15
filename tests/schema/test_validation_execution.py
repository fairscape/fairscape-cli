import os
import sys

sys.path.insert(
    0, 
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), 
        '../..')
    )
)

from fairscape_cli.models.schema.tabular import (
    ReadSchema
)
# set up CLI test runner
from click.testing import CliRunner
from fairscape_cli.__main__ import cli as fairscape_cli_app
runner = CliRunner()


class TestExecutionSuccess():
    output_path = "tests/data/schema/apms_embedding_schema.json"
    data_path = "tests/data/APMS_embedding_MUSIC.csv"

    def test_0_json_conversion(self):
        ''' test the conversion of data into json array according to a schema
        '''

        test_schema = ReadSchema(self.output_path)
        test_df = test_schema.load_data(self.data_path)
        json_output = test_schema.convert_data_to_json(test_df)


    def test_1_execute_validation(self):
        ''' test the execution of validation for a valid schema
        '''
        test_schema = ReadSchema(self.output_path)
        validation_errors = test_schema.execute_validation(self.data_path)

        assert len(validation_errors)==0

 
    def test_2_cli_validation_success(self):
        ''' test the CLI interface for a successfull validation execution
        '''

        # create a test schema
        test_command = [
            "schema",
            "validate",
            "--schema",
            self.output_path,
            "--data",
            self.data_path
        ]

        result = runner.invoke(
            fairscape_cli_app, 
            test_command
            )

        print(result.output)
        assert result.exit_code == 0 

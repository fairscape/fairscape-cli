import PySimpleGUI as sg
from pathlib import Path
import pandas as pd
from pydantic import ValidationError
import json

from fairscape_cli.models.schema.tabular import (
    BooleanProperty,
    IntegerProperty,
    StringProperty,
    NumberProperty,
    ArrayProperty,
    Items,
    TabularValidationSchema)

# Layout GUI title
WINDOW_TITLE = 'Data Schema Entry Form'

# Options for PySimpleGUI Combo Elements
eligible_datatypes = ['string', 'boolean', 'number', 'integer', 'array']
eligible_array_datatypes = ['null', 'string', 'boolean', 'number', 'integer', 'array']

# File types for validating against the user input
eligible_tabular_filetypes = (('Tabular Files', '*.csv *.tsv'),)

# Edge width value for highlighting a PySimpleGUI element
HIGHLIGHT_WIDTH = 1
NO_HIGHLIGHT_WIDTH = 0

# Index for each row containing property and its attributes
row_counter = 0
# Total number of rows created, default=1
total_num_rows = 1
# Tracker for row id when a property is removed i.e. rendered invisible
deleted_row_index = set()

def create_string_property(description, index, datatype, value_url=None, pattern=None):
    """
    Creates an instance of string typed property.
    :param description:
    :param number:
    :param datatype:
    :param value_url:
    :param pattern:
    :return: instance of StringProperty
    """
    if value_url == '':
        value_url = None
    if pattern == '':
        pattern = None
    return StringProperty(
        description=description,
        index=index,
        datatype=datatype,
        valueURL=value_url,
        pattern=pattern
    )


def create_boolean_property(description, index, datatype, value_url=None):
    """
    Creates an instance of boolean typed property.
    :param description:
    :param number:
    :param datatype:
    :param value_url:
    :return: instance of BooleanProperty
    """
    if value_url == '':
        value_url = None
    return BooleanProperty(
        description=description,
        index=index,
        datatype=datatype,
        valueURL=value_url
    )


def create_number_property(description, index, datatype, value_url=None):
    """
    Creates an instance of number typed property.
    :param description:
    :param number:
    :param datatype:
    :param value_url:
    :return: instance of NumberProperty
    """
    if value_url == '':
        value_url = None
    return NumberProperty(
        description=description,
        index=index,
        datatype=datatype,
        valueURL=value_url
    )


def create_integer_property(description, index, datatype, value_url=None):
    """
    Creates an instance of integer typed property.
    :param description:
    :param number:
    :param datatype:
    :param value_url:
    :return: instance of IntegerProperty
    """
    if value_url == '':
        value_url = None
    return IntegerProperty(
        description=description,
        index=index,
        datatype=datatype,
        valueURL=value_url
    )


def create_items(datatype):
    """
    Creates an instance of Item.
    :param datatype:
    :return: instance of type Item
    """
    return Items(
        datatype=datatype
    )


def create_array_property(description, index, datatype, max, unique, items: Items, value_url=None, min=None):
    """
    Creates an instance of array typed property.
    :param description:
    :param number:
    :param datatype:
    :param max:
    :param unique:
    :param items:
    :param value_url:
    :param min:
    :return: instance of ArrayProperty
    """
    if value_url == '':
        value_url = None
    if min == '':
        min = None
    return ArrayProperty(
        description=description,
        index=index,
        datatype=datatype,
        maxItems=max,
        uniqueItems=unique,
        items=items,
        valueURL=value_url,
        minItems=min
    )


def create_properties_metadata(values):
    properties = {}
    required = []

    for row_id in range(total_num_rows):
        if row_id not in deleted_row_index:

            if values[('-REQUIRED_VALUE-', row_id)]:
                required.append(values[('-NAME_VALUE-', row_id)])

            if values[('-DATATYPE_VALUE-', row_id)] == 'string':
                string_prop = create_string_property(
                    values[('-DESCRIPTION_VALUE-', row_id)],
                    values[('-NUMBER_VALUE-', row_id)],
                    values[('-DATATYPE_VALUE-', row_id)],
                    values[('-URL_VALUE-', row_id)],
                    values[('-PATTERN_VALUE-', row_id)]
                )
                properties[values[('-NAME_VALUE-', row_id)]] = string_prop

            if values[('-DATATYPE_VALUE-', row_id)] == 'boolean':
                boolean_prop = create_boolean_property(
                    values[('-DESCRIPTION_VALUE-', row_id)],
                    values[('-NUMBER_VALUE-', row_id)],
                    values[('-DATATYPE_VALUE-', row_id)],
                    values[('-URL_VALUE-', row_id)]
                )
                properties[values[('-NAME_VALUE-', row_id)]] = boolean_prop

            if values[('-DATATYPE_VALUE-', row_id)] == 'number':
                number_prop = create_number_property(
                    values[('-DESCRIPTION_VALUE-', row_id)],
                    values[('-NUMBER_VALUE-', row_id)],
                    values[('-DATATYPE_VALUE-', row_id)],
                    values[('-URL_VALUE-', row_id)]
                )
                properties[values[('-NAME_VALUE-', row_id)]] = number_prop

            if values[('-DATATYPE_VALUE-', row_id)] == 'integer':
                integer_prop = create_integer_property(
                    values[('-DESCRIPTION_VALUE-', row_id)],
                    values[('-NUMBER_VALUE-', row_id)],
                    values[('-DATATYPE_VALUE-', row_id)],
                    values[('-URL_VALUE-', row_id)]
                )
                properties[values[('-NAME_VALUE-', row_id)]] = integer_prop

            if values[('-DATATYPE_VALUE-', row_id)] == 'array':
                items = create_items(values[('-ITEM_VALUE-', row_id)])

                array_prop = create_array_property(
                    values[('-DESCRIPTION_VALUE-', row_id)],
                    values[('-NUMBER_VALUE-', row_id)],
                    values[('-DATATYPE_VALUE-', row_id)],
                    values[('-MAX_ITEM_VALUE-', row_id)],
                    values[('-UNIQUE_ITEM_VALUE-', row_id)],
                    items,
                    values[('-URL_VALUE-', row_id)],
                    values[('-MIN_ITEM_VALUE-', row_id)]
                )
                properties[values[('-NAME_VALUE-', row_id)]] = array_prop

    return properties, required
    # for key, value in window.key_dict.items():
    #    print(key, value)


def create_schema_instance(values):
    """
    Create instance of tabular schema against the model.
    :return: instance of the model created.
    """
    properties, required = create_properties_metadata(values)

    schema_title = values["-SCHEMA_TITLE-"]
    schema_description = values["-SCHEMA_DESC-"]
    header = values["-HEADER-"]
    additional_properties = values["-ADDITIONAL_PROPERTIES-"]
    separator = values["-FIELD_SEPARATOR-"]

    data = dict(
            name=schema_title,
            description=schema_description,
            properties=properties,
            additionalProperties=additional_properties,
            required=required,            
            seperator=separator,
            header=header            
        )
    try:     
        schema_model_instance = TabularValidationSchema(**data)
    except ValidationError as e:
        sg.popup_error_with_traceback(f'An error occurred:', e.errors())
    return schema_model_instance


def get_required_schema_field_key():
    """
    Enlist required schema-level metadata fields.
    :return: List of required schema-level metadata fields.
    """
    required_schema_field_key = ['-SCHEMA_TITLE-', '-SCHEMA_DESC-', '-FIELD_SEPARATOR-']
    return required_schema_field_key


def get_required_property_field_key():
    """
    Enlist required property-level metadata fields
    :return: required property-level metadata fields.
    """
    required_property_field_key = []

    for row in range(total_num_rows):
        if row not in deleted_row_index:
            required_property_field_key.append(('-NAME_VALUE-', row))
            required_property_field_key.append(('-DESCRIPTION_VALUE-', row))
            required_property_field_key.append(('-NUMBER_VALUE-', row))

    return required_property_field_key


def get_required_property_dropdown_key(values):
    """
    Enlist required property-level metadata datatypes
    :return:
    """
    required_property_dropdown_key = []

    for row in range(total_num_rows):
        if row not in deleted_row_index:
            if values[('-DATATYPE_VALUE-', row)] not in eligible_datatypes:
                sg.popup_error('Datatype must be one of ', eligible_datatypes)
                break
            elif values[('-DATATYPE_VALUE-', row)] == 'array':
                if values[('-ITEM_VALUE-', row)] not in eligible_array_datatypes:
                    sg.popup_error('Items must be one of ', eligible_array_datatypes)
                    break
                required_property_dropdown_key.append(('-MAX_ITEM_VALUE-', row))
    return required_property_dropdown_key


def get_required_array_item_field_key(values):
    """
    Enlist required metadata when array type datatype is selected
    :return:
    """
    # only Max is required when array datatype is selected
    required_array_item_field_key = []

    for row in range(total_num_rows):
        if row not in deleted_row_index:
            if values[('-DATATYPE_VALUE-', row)] == 'array':                
                required_array_item_field_key.append(('-MAX_ITEM_VALUE-', row))
    return required_array_item_field_key


def is_valid_required_field(values, window, required_element_key=None):
    is_valid = True

    for element_key in required_element_key:
        if not values[element_key]:
            is_valid = False
            set_border_color(window[element_key], 'red', HIGHLIGHT_WIDTH)
        else:
            set_border_color(window[element_key], None, NO_HIGHLIGHT_WIDTH)
    return is_valid


def is_required_field_filled_in(values, window, element_keys=None):
    
    # assume fields are filled in with data
    is_filled_in=True

    for element_key in element_keys:
        if not values[element_key] or values[element_key].isspace() :
            is_filled_in=False
            set_border_color(window[element_key], 'red', HIGHLIGHT_WIDTH)
        else:
            set_border_color(window[element_key], None, NO_HIGHLIGHT_WIDTH)
    return is_filled_in


def is_datatype_selected(values, window):
    # assume datatype is selected
    is_eligible_datatype=True

    for row in range(total_num_rows):
        if row not in deleted_row_index:
            if values[('-DATATYPE_VALUE-', row)] not in eligible_datatypes:
                is_eligible_datatype=False
                #sg.popup_error('Datatype must be one of ', eligible_datatypes)
                break
    return is_eligible_datatype


def is_arraytype_selected(values, window):
    # assume datatype is NOT selected
    is_eligible_arraytype=True

    required_property_dropdown_key = []

    for row in range(total_num_rows):
        if row not in deleted_row_index:
            if values[('-DATATYPE_VALUE-', row)] == 'array':
                if values[('-ITEM_VALUE-', row)] not in eligible_array_datatypes:
                    is_eligible_arraytype=False
                    #sg.popup_error('Items must be one of ', eligible_array_datatypes)
                    break
                required_property_dropdown_key.append(('-MAX_ITEM_VALUE-', row))
    return is_eligible_arraytype


def check_form_validity(values, window):
    is_valid = True

    required_schema_field_key = get_required_schema_field_key()
    required_property_field_key = get_required_property_field_key()

    if not is_required_field_filled_in(values, window, required_schema_field_key):            
        is_valid=False
        sg.popup_error('Missing required field!', title='Invalid Form')
        return is_valid
    if not is_required_field_filled_in(values, window, required_property_field_key):
        is_valid=False
        sg.popup_error('Missing required field!', title='Invalid Form')
        return is_valid
    if not is_datatype_selected(values, window):
        is_valid=False
        sg.popup_error('Datatype must be one of ', eligible_datatypes, title='Invalid Form')
        return is_valid
    else:
        if not is_arraytype_selected(values, window):
            is_valid=False
            sg.popup_error('Item must be one of ', eligible_array_datatypes, title='Invalid Form')
            return is_valid
        required_array_item_field_key = get_required_array_item_field_key(values)
        if not is_required_field_filled_in(values, window, required_array_item_field_key):            
            is_valid=False
            sg.popup_error('Missing required field!', title='Invalid Form', )
            return is_valid
        
    
    return is_valid   


def validate_required_input(values, window):
    required_schema_field_key = get_required_schema_field_key()
    required_property_field_key = get_required_property_field_key()
    if is_valid_required_field(values, window, required_schema_field_key) and is_valid_required_field(values, window, required_property_field_key):
        required_property_dropdown_key = get_required_property_dropdown_key(values)
        if not is_valid_required_field(values, window, required_property_dropdown_key):
            sg.popup_error('Missing required field!', title='Invalid Form')
    else:
        sg.popup_error('Missing required field!', title='Invalid Form')


def set_border_color(element, color=None, width=HIGHLIGHT_WIDTH):
    '''
    Color the border of an element with a specific color and width.
    :param element: The element to color.
    :param color: The specific color to use.
    :param width: The specific width around the element.
    :return:
    '''
    if color is None:
        color = sg.theme_background_color()
    element.Widget.configure(highlightcolor=color, highlightbackground=color,
                             highlightthickness=width)


def create_property_row(row_id):
    '''
    Create a row of multiple PySimpleGUI elements in a single column pinned to the layout.
    :param row_id: Index of the row (0,1,...,n)
    :return: Row containing PySimpleGUI elements.
    '''
    row = [
        sg.pin(
            sg.Col([
                [
                    sg.Text('X', border_width=0, text_color='red', enable_events=True, key=('-DELETE_ROW-', row_id)),
                    sg.Text('Name:', tooltip='A unique name representing values from one or more column. Names cannot have white space.'),
                    sg.Input(size=(20, 1), tooltip='Unique names are strings without whitespace e.g. "gene_symbol"', key=('-NAME_VALUE-', row_id)),
                    sg.Text('Description:', tooltip='Description about the name of the property'),
                    sg.Multiline(size=(40, 3), tooltip='The property "gene_symbol" can be described as "gene symbol for apms embedding vector"',
                                 key=('-DESCRIPTION_VALUE-', row_id)),
                    sg.Text('Column Number:', tooltip='Index of the property using digits "0, 1, ..." and the delimiter ":" for the slice syntax.'),
                    sg.Input(size=(4, 1), key=('-NUMBER_VALUE-', row_id), tooltip='0 indicates the first column, 1 indicates the second, 2:: ranges from 3rd till the end'),
                    sg.Checkbox('Required', tooltip='Required properties include the list of essential properties to document the schema of the data.',
                                key=('-REQUIRED_VALUE-', row_id)),
                    sg.Text('Vocab URL:', tooltip='Standard vocabulary to represent the property'),
                    sg.Input(size=(20, 1), tooltip='A concept or a property from schema.org or an existing ontology', key=('-URL_VALUE-', row_id)),
                    sg.Text('Datatype:'),
                    sg.Combo(eligible_datatypes,
                             default_value='Select',
                             enable_events=True,
                             key=('-DATATYPE_VALUE-', row_id)),
                    sg.Text('Pattern:', tooltip='REGEX pattern', visible=False, key=('-PATTERN_LABEL-', row_id)),
                    sg.Input(size=(10, 1), disabled=True, visible=False, key=('-PATTERN_VALUE-', row_id)),
                    sg.Text('Max:', tooltip='Maximum items in array', visible=False,
                            key=('-MAX_ITEM_LABEL-', row_id)),
                    sg.Input(size=(4, 1), disabled=True, visible=False, key=('-MAX_ITEM_VALUE-', row_id)),
                    sg.Text('Min:',
                            tooltip='Minimum items in array', visible=False, key=('-MIN_ITEM_LABEL-', row_id)),
                    sg.Input(size=(4, 1), disabled=True, visible=False, key=('-MIN_ITEM_VALUE-', row_id)),
                    sg.Checkbox('Unique', disabled=True, visible=False,
                                key=('-UNIQUE_ITEM_VALUE-', row_id)),
                    sg.Text('Item:', visible=False, key=('-ITEM_LABEL-', row_id)),
                    sg.Combo(eligible_array_datatypes,
                             default_value='Select',
                             enable_events=True,
                             disabled=True,
                             visible=False,
                             key=('-ITEM_VALUE-', row_id))
                ]
            ],
                key=('-ROW-', row_id))
        )
    ]
    return row


# Main GUI Layout
layout = [
    [sg.Text('Schema Title:', size=(20, 1), justification='left', tooltip='Meaningful title of the data schema'),
     sg.InputText(size=(40, 1), tooltip='For example, "APMS Embedding Schema"',
                  enable_events=True,
                  default_text='APMS Embedding Schema',
                  key='-SCHEMA_TITLE-')],
    [sg.Text('Schema Description:', size=(20, 1), justification='left',
             tooltip='Brief description of the content of the data schema'),
     sg.Multiline(no_scrollbar=False, size=(40, 3), tooltip='For example, "Schema for APMS Embedding Results from pipeline"',
                  enable_events=True,
                  default_text='Schema for APMS Embedding Results from pipeline', key='-SCHEMA_DESC-')],
    [sg.Text('Separator:', size=(20, 1), justification='left', tooltip='Field seperator symbols such as comma, semicolon, tab separate values in a record'),
     sg.InputText(size=(1, 1), tooltip='Examples include comma(,), semicolon(;), vertical bar(|)', default_text=',',
                  enable_events=True, font='bold',
                  key='-FIELD_SEPARATOR-')],
    [sg.Text("Header:", size=(19, 1), tooltip='The first row of the tabular data sometimes use names to represent the values beneath them. These are referred to as headers.'),
     sg.Checkbox("", tooltip='Click yes (checked) if header information exists for the tabular data',
                 size=(4, 4), checkbox_color='white', text_color='black',
                 key='-HEADER-')],
    [sg.Text("Additional Properties:", size=(19, 1),
             tooltip='Additional properties are those that exist in the data although they are not among the added properties'),
     sg.Checkbox("", tooltip='Click yes (checked) if additional properties are not among the added properties',
                 size=(4, 4), checkbox_color='white', text_color='black',
                 key='-ADDITIONAL_PROPERTIES-')],
    [sg.HorizontalSeparator(pad=((0, 0), (10, 10)))],
    [sg.Button("Add Property", tooltip='Each property represents one or more columns in tabular data. Click to add more properties', key='-ADD_ROW-')],
    [sg.Column([create_property_row(0)], key='-ROW_PANEL-')],
    [
        sg.Button('Validate Form Submission', key='-VALIDATE_FORM-'),
        sg.Button('Display Schema', key='-DISPLAY_METADATA-'),
        #sg.B("Save Schema as File", s=16), sg.T("Select Destination Directory:", s=25, justification="l"), sg.I(key="-SAVE_METADATA-"), sg.FolderBrowse()
        sg.Button("Save Schema as File",
                      #target=(555666777, -1),
                      file_types=(('JSON', '*.json'),),
                      #initial_folder=None,
                      default_extension="json"
                      )
    ],
    [sg.Multiline(key='-DISPLAY_WINDOW-', size=(85, 20), background_color='#ffffff', do_not_clear=True)],
    [sg.HorizontalSeparator(pad=((0, 0), (10, 10)))],
    [sg.T("Select Dataset for Schema:", s=30, justification="l"), sg.I(key="-INPUT_SCHEMA_FILE-"),
     sg.FileBrowse(file_types=eligible_tabular_filetypes)],
    [#sg.B("Display Source File", s=16, key='-DISPLAY_SCHEMA_FILE-'),
     sg.B("Validate Dataset against Schema", s=28, key='-VALIDATE_SCHEMA_FILE-')],
    #[sg.Output(size=(110, 20), font='Helvetica 10', key='-DISPLAY_WINDOW-')],

    [sg.Exit(key='-EXIT-')]
]


def create_window():
    # Set window attributes
    window = sg.Window(WINDOW_TITLE, layout=layout, resizable=True, finalize=True)
    return window


def is_valid_path(filepath):
    if filepath and Path(filepath).exists():
        return True
    sg.popup_error("File path does not exist", title="File Error")
    return False


def clear_display(element_key, window):
    """
    Clear content from output window.
    :param element_key: element identifier key
    :return:
    """
    window[element_key].Update('')


def display_tabular_file(file_path):
    """
    Display tabular files: CSV, TSV
    :param file_path:
    :return:'
    """
    try:
        df = pd.read_csv(file_path)
        file_name = Path(file_path).name
        sg.popup_scrolled(df.dtypes, "=" * 50, df, title=file_name)
    except pd.errors.ParserError as e:
        sg.popup_error_with_traceback(f'An error occurred:', e)

def initialize_gui(window):

    while True:

        event, values = window.read()
        # print(event, values)
        if event in (sg.WINDOW_CLOSED, 'Exit', '-EXIT-'):
            break

        if event == '-ADD_ROW-':  # Adds
            # Using 'global' resolves UnboundLocalError: local variable 'row_counter' referenced before assignment
            global row_counter
            row_counter = row_counter + 1
            window.extend_layout(window['-ROW_PANEL-'], [create_property_row(row_counter)])
            # Using 'global' resolves UnboundLocalError: local variable 'total_num_rows' referenced before assignment
            global total_num_rows
            total_num_rows = total_num_rows + 1
        elif event[0] == '-DELETE_ROW-':
            window[('-ROW-', event[1])].update(visible=False)
            # capture reference key to the deleted row
            (row_key_name, row_key_index) = window[('-ROW-', event[1])].key
            deleted_row_index.add(row_key_index)

        if event[0] == '-DATATYPE_VALUE-':
            key, index = window.find_element_with_focus().key

            if values[window.find_element_with_focus().key] == 'string':
                window[('-PATTERN_LABEL-', index)].update(visible=True)
                window[('-PATTERN_VALUE-', index)].update(disabled=False, visible=True)

            if values[window.find_element_with_focus().key] in ['boolean', 'integer', 'number', 'array']:
                window[('-PATTERN_LABEL-', index)].update(visible=False)
                window[('-PATTERN_VALUE-', index)].update("", disabled=True, visible=False)

            if values[window.find_element_with_focus().key] == 'array':
                window[('-MAX_ITEM_LABEL-', index)].update(visible=True)
                window[('-MAX_ITEM_VALUE-', index)].update(disabled=False, visible=True)
                window[('-MIN_ITEM_LABEL-', index)].update(visible=True)
                window[('-MIN_ITEM_VALUE-', index)].update(disabled=False, visible=True)
                window[('-UNIQUE_ITEM_VALUE-', index)].update(disabled=False, visible=True)
                window[('-ITEM_LABEL-', index)].update(visible=True)
                window[('-ITEM_VALUE-', index)].update(disabled=False, visible=True)

            if values[window.find_element_with_focus().key] in ['string', 'boolean', 'integer', 'number']:
                window[('-MAX_ITEM_LABEL-', index)].update(visible=False)
                window[('-MAX_ITEM_VALUE-', index)].update("", disabled=True, visible=False)
                window[('-MIN_ITEM_LABEL-', index)].update(visible=False)
                window[('-MIN_ITEM_VALUE-', index)].update("", disabled=True, visible=False)
                window[('-UNIQUE_ITEM_VALUE-', index)].update(False, disabled=True, visible=False)
                window[('-ITEM_LABEL-', index)].update(visible=False)
                window[('-ITEM_VALUE-', index)].update("Select", disabled=True, visible=False)

        if event == '-DISPLAY_METADATA-':
            if check_form_validity(values, window):
                instance_model = create_schema_instance(values)
                #clear_display(window, '-DISPLAY_WINDOW-')
                test = json.dumps(instance_model.model_dump(by_alias=True), indent=4)
                window['-DISPLAY_WINDOW-'].update(test)
            #else:
            #    sg.popup_error('Invalid Form Data! Unable to generate metadata', title='Invalid Form')


        #if event == "-DISPLAY_SCHEMA_FILE-":
        #    if is_valid_path(values["-INPUT_SCHEMA_FILE-"]):
        #        display_tabular_file(values["-INPUT_SCHEMA_FILE-"])

        if event == "-VALIDATE_SCHEMA_FILE-":
            if is_valid_path(values["-INPUT_SCHEMA_FILE-"]):
                try:
                    embed_data = pd.read_csv(values["-INPUT_SCHEMA_FILE-"], header=None)
                    schema_json = create_schema_instance().execute_validation(data_frame=embed_data)
                except pd.errors.ParserError as e:
                    sg.popup_error_with_traceback(f'An error occurred:', e)

        if event == '-VALIDATE_FORM-':
            #validate_required_input(values, window)            
            #TODO
            if check_form_validity(values, window):
                print('form is valid')
            else:
                print('invalid form')

        if event == "Save Schema as File":

            schema_displayed = values['-DISPLAY_WINDOW-']
            if schema_displayed:
                file_name = sg.PopupGetFile('Please enter filename to save',
                                            save_as=True,
                                            file_types=(("JSON", "*.json"),)
                                            )
                with open(file_name, 'w') as outfile:
                    outfile.write(json.dumps(json.loads(schema_displayed), indent=4))
            else:
                sg.popup_error('Display Schema before saving', title='Error saving schema')

    window.close()
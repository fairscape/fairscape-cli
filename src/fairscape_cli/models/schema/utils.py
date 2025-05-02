import re
from typing import (
    Union,
    List
)


class PropertyNameException(Exception):
    def __init__(self, propertyName):
        self.propertyName = propertyName
        self.message = f"PropertyNameException: Property with name '{propertyName}' already present in schema"
        super().__init__(self.message)


class InvalidRangeException(Exception):
    def __init__(self, slice_value):
        self.slice_value
        self.message = f"InvalidRangeException: Error Parsing Range Expression {slice_value}" 
        super().__init__(self.message)


def GenerateSlice(range_string: str, row_length: int)-> slice:
    """ Given a range string from a property generate an appropriate python slice.
    """
    
    n_to_end_slice_match = re.search("^([0-9]*)::$", range_string)
    start_to_n_slice_match = re.search("^::([0-9]*)$", range_string)
    n_to_m_slice_match = re.search("^([0-9]*):([0-9]*)$", range_string)

    if n_to_end_slice_match:
        start = int(n_to_end_slice_match.group(1))
        generated_slice = slice(start, row_length)
       
        #TODO raise an error if start<0

    elif start_to_n_slice_match:
        end = int(start_to_n_slice_match.group(1))
        generated_slice = slice(0,end)

        # TODO raise an error if end>row_length

    elif n_to_m_slice_match:
        start = int(n_to_m_slice_match.group(1))
        end = int(n_to_m_slice_match.group(2))
        generated_slice = slice(start, end)
        
        # TODO raise an error if end>row_length
        # TODO raise an error if start<0

    else:
        # raise exception for improperly passing a slice 
        raise InvalidRangeException(range_string)

    return generated_slice


class RangeOverlapException(Exception):
    def __init__(self, range_one, range_two):
        self.message = f"RangeOverlapException: Ranges {str(range_one)} and {str(range_two)} have overlap" 
        super().__init__(self.message)


class ColumnIndexException(Exception):
    def __init__(self, index):
        self.index = index 
        self.message = f"ColumnIndexException: Column number '{index}' already present in schema"
        super().__init__(self.message)


def CheckSliceSliceOverlap(new_slice: slice, comparison_slice: slice) -> None:
    """ Given two python slices check that two slice expressions don't have overlap
    """
    # TODO consider step size for collisions

    if new_slice.stop >= comparison_slice.start and new_slice.start < comparison_slice.start:
       raise RangeOverlapException(new_slice, comparison_slice) 

    if comparison_slice.stop >= new_slice.start and comparison_slice.start < new_slice.start:
       raise RangeOverlapException(new_slice, comparison_slice) 

    # check that slices aren't equivalent
    if new_slice.start == comparison_slice.start and new_slice.stop == comparison_slice.stop:
       raise RangeOverlapException(new_slice, comparison_slice) 

    return None



def CheckIntSliceOverlap(passed_int: int, passed_slice: slice) ->None:
    """ Given a Slice and an Integer Check that no overlap exists
    """

    if passed_int > passed_slice.start and passed_int < passed_slice.stop:
        raise RangeOverlapException(passed_slice, passed_int)

    if passed_int == passed_slice.start or passed_int == passed_slice.stop:
        raise RangeOverlapException(passed_slice, passed_int)

    return None
        



def CheckOverlap(property_index: Union[str,int], schema_indicies: List[Union[str,int]])->None:
    """ Given a new property index either as an integer or a slice expression, 
        check that there exists no overlap with existing schema indicies
    """
    # convert all Ranges from strings into Slices 
    schema_slice_indicies = [ 
        GenerateSlice(schema_range_elem) for schema_range_elem 
        in filter(lambda index: isinstance(index, str), schema_indicies)
        ]
    schema_int_indicies = list(filter(lambda index: isinstance(index, int), schema_indicies))

    # check that int indicies dont overlap any other int indicies
    int_overlap_count = [ schema_int_indicies.count(elem) != 1 for elem in schema_int_indicies]
    
    if any(int_overlap_count): 
        # TODO find offending overlap
        raise ColumnIndexException()

    # check that slice indicies don't overlap any int indicies
    for slice_elem in schema_slice_indicies:
        inside_slice = [
            int_index > slice_elem.start and int_index < slice_elem.stop for 
            int_index in schema_int_indicies
            ]
        inside_bound = [
            int_index == slice_elem.start or int_index == slice_elem.stop for 
            int_index in schema_int_indicies
            ]
        
        if any(inside_slice):
            # TODO find the offending overlap values
            raise RangeOverlapException(slice_elem, None)

        if any(inside_bound):
            # TODO find the offending overlap values
            raise RangeOverlapException(slice_elem, None)

    # TODO check that slice indicies don't overlap any other slice indicies
    
    return None
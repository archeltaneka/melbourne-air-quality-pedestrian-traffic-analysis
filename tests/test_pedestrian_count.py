from datetime import datetime
from pathlib import Path
import time

import pytest
import pandas as pd
import numpy as np

from unittest.mock import Mock, patch, call
from pandas.testing import assert_frame_equal

import sys
# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pedestrian_count import PedestrianCountProcessor


class TestPedestrianCountProcessorInit:
    """Test suite for the PedestrianCountProcessor.__init__ method"""

    ### Test initialization ###
    def test_init_creates_instance(self):
        """Test that __init__ creates a valid instance"""
        processor = PedestrianCountProcessor()
        
        assert processor is not None
        assert isinstance(processor, PedestrianCountProcessor)
        assert processor.logger is not None


    def test_init_sets_location_mapping(self):
        """Test that location_mapping is set correctly"""
        processor = PedestrianCountProcessor()
        
        assert hasattr(processor, 'location_mapping')
        assert isinstance(processor.location_mapping, dict)
        assert len(processor.location_mapping) == 4

    
    def test_init_location_mapping_has_correct_rules(self):
        """Test that location_mapping has all expected rules"""
        processor = PedestrianCountProcessor()
        
        expected_keys = {
            "Lincoln - Swanston (W)": "Lincoln - Swanston (West)",
            "Harbour Esplanade - Pedestrian Path": "Harbour Esplanade (West) - Pedestrian Path",
            "Harbour Esplanade - Bike Path": "Harbour Esplanade (West) - Bike Path",
            "Rmit Bld 80 - 445 Swanston Street": "Rmit Building 80"
        }
        
        for key, value in expected_keys.items():
            assert key in processor.location_mapping
            assert processor.location_mapping[key] == value

    
    def test_init_location_mapping_values_are_strings(self):
        """Test that all location_mapping values are strings"""
        processor = PedestrianCountProcessor()
        
        for key, value in processor.location_mapping.items():
            assert isinstance(key, str)
            assert isinstance(value, str)

    
    def test_init_location_mapping_no_empty_strings(self):
        """Test that location_mapping has no empty strings"""
        processor = PedestrianCountProcessor()
        
        for key, value in processor.location_mapping.items():
            assert len(key) > 0
            assert len(value) > 0


    def test_init_sets_nominatim_mapping_rules(self):
        """Test that nominatim_mapping_rules is set correctly"""
        processor = PedestrianCountProcessor()
        
        assert hasattr(processor, 'nominatim_mapping_rules')
        assert isinstance(processor.nominatim_mapping_rules, dict)
        assert len(processor.nominatim_mapping_rules) == 7


    def test_init_nominatim_mapping_rules_has_correct_rules(self):
        """Test that nominatim_mapping_rules has all expected rules"""

        processor = PedestrianCountProcessor()
        
        expected_mapping = {
            "Bourke St Bridge": "Bourke St",
            "Flinders Street Station Underpass": "Flinders Street Station",
            "Melbourne Convention Exhibition Centre": "MCEC",
            "Qv Market": "Queen Victoria Market",
            "Qvm": "Queen Victoria Market",
            "Rmit Building 14": "RMIT Building",
            "Rmit Building 80": "RMIT Building"
        }

        for key, value in expected_mapping.items():
            assert key in processor.nominatim_mapping_rules
            assert processor.nominatim_mapping_rules[key] == value


    def test_init_nominatim_mapping_values_are_strings(self):
        """Test that all nominatim_mapping_rules values are strings"""
        processor = PedestrianCountProcessor()
        
        for key, value in processor.nominatim_mapping_rules.items():
            assert isinstance(key, str)
            assert isinstance(value, str)


    def test_init_nominatim_mapping_no_empty_strings(self):
        """Test that nominatim_mapping_rules has no empty strings"""
        processor = PedestrianCountProcessor()
        
        for key, value in processor.nominatim_mapping_rules.items():
            assert len(key) > 0
            assert len(value) > 0


    def test_init_sets_cols_to_add(self):
        """Test that cols_to_add is set correctly"""
        processor = PedestrianCountProcessor()
        
        assert hasattr(processor, 'cols_to_add')
        assert isinstance(processor.cols_to_add, list)
        assert len(processor.cols_to_add) == 5


    def test_init_cols_to_add_has_correct_values(self):
        """Test that cols_to_add has all expected values"""
        processor = PedestrianCountProcessor()
        
        expected_cols = [
            "William St - Little Lonsdale St (West)",
            "Errol St (West)",
            "Flagstaff Station (East)",
            "380 Elizabeth St",
            "La Trobe St - William St (South)"
        ]
        
        assert processor.cols_to_add == expected_cols


    def test_init_cols_to_add_all_strings(self):
        """Test that all cols_to_add values are strings"""
        processor = PedestrianCountProcessor()
        
        for col in processor.cols_to_add:
            assert isinstance(col, str)


    def test_init_cols_to_add_no_empty_strings(self):
        """Test that cols_to_add has no empty strings"""
        processor = PedestrianCountProcessor()
        
        for col in processor.cols_to_add:
            assert len(col) > 0


    def test_init_cols_to_add_no_duplicates(self):
        """Test that cols_to_add has no duplicate entries"""
        processor = PedestrianCountProcessor()
        
        assert len(processor.cols_to_add) == len(set(processor.cols_to_add))

    ### End of test initialization ###

    ### Test _clean_columns method ###
    def test_clean_columns_returns_dataframe(self, pedestrian_count_processor):
        """Test that _clean_columns returns a DataFrame"""
        df = pd.DataFrame({'column1': [1, 2, 3]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert isinstance(result, pd.DataFrame)


    def test_clean_columns_preserves_data(self, pedestrian_count_processor):
        """Test that _clean_columns preserves data values"""
        df = pd.DataFrame({'column1': [1, 2, 3], 'column2': [4, 5, 6]})
        result = pedestrian_count_processor._clean_columns(df)
        
        # Data should be unchanged
        assert result.shape == df.shape
        assert result.iloc[0, 0] == 1
        assert result.iloc[1, 1] == 5


    def test_clean_columns_converts_to_title_case(self, pedestrian_count_processor):
        """Test that column names are converted to title case"""
        df = pd.DataFrame({'lowercase': [1], 'UPPERCASE': [2], 'MiXeD': [3]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'Lowercase' in result.columns
        assert 'Uppercase' in result.columns
        assert 'Mixed' in result.columns


    def test_clean_columns_standardizes_hyphens(self, pedestrian_count_processor):
        """Test that hyphens are standardized with spaces"""
        df = pd.DataFrame({'word-word': [1], 'a-b': [2]})
        result = pedestrian_count_processor._clean_columns(df)
        
        # Should have spaces around hyphens
        assert 'Word - Word' in result.columns
        assert 'A - B' in result.columns


    def test_clean_columns_removes_extra_spaces(self, pedestrian_count_processor):
        """Test that extra spaces are removed"""
        df = pd.DataFrame({
            'word  with   spaces': [1],
            'multiple    spaces': [2],
            'tab\there': [3]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        # Should have single spaces only
        expected_cols = ['Word With Spaces', 'Multiple Spaces', 'Tab Here']
        for col in expected_cols:
            assert col in result.columns

    
    def test_clean_columns_strips_leading_trailing_spaces(self, pedestrian_count_processor):
        """Test that leading and trailing spaces are removed"""
        df = pd.DataFrame({
            '  leading': [1],
            'trailing  ': [2],
            '  both  ': [3]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        # No leading/trailing spaces
        for col in result.columns:
            assert col == col.strip()


    def test_clean_columns_handles_single_hyphen(self, pedestrian_count_processor):
        """Test handling of single hyphen without spaces"""
        df = pd.DataFrame({'a-b': [1]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'A - B' in result.columns


    def test_clean_columns_handles_multiple_hyphens(self, pedestrian_count_processor):
        """Test handling of multiple hyphens"""
        df = pd.DataFrame({'a-b-c-d': [1]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'A - B - C - D' in result.columns


    def test_clean_columns_handles_hyphen_with_existing_spaces(self, pedestrian_count_processor):
        """Test handling of hyphens that already have spaces"""
        df = pd.DataFrame({'word - word': [1], 'a - b - c': [2]})
        result = pedestrian_count_processor._clean_columns(df)
        
        # Should still be properly formatted
        assert 'Word - Word' in result.columns
        assert 'A - B - C' in result.columns


    def test_clean_columns_preserves_numbers(self, pedestrian_count_processor):
        """Test that numbers in column names are preserved"""
        df = pd.DataFrame({'column1': [1], 'test2name': [2], '123abc': [3]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'Column1' in result.columns
        assert 'Test2Name' in result.columns
        assert '123Abc' in result.columns


    def test_clean_columns_handles_parentheses(self, pedestrian_count_processor):
        """Test handling of parentheses in column names"""
        df = pd.DataFrame({'word(test)': [1], '(start)': [2], 'end(test)': [3]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'Word(Test)' in result.columns
        assert '(Start)' in result.columns
        assert 'End(Test)' in result.columns


    def test_clean_columns_handles_underscores(self, pedestrian_count_processor):
        """Test handling of underscores"""
        df = pd.DataFrame({'word_with_underscore': [1], 'test_123': [2]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'Word_With_Underscore' in result.columns
        assert 'Test_123' in result.columns


    def test_clean_columns_handles_dots(self, pedestrian_count_processor):
        """Test handling of dots/periods"""
        df = pd.DataFrame({'word.name': [1], 'test.2.name': [2]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'Word.Name' in result.columns
        assert 'Test.2.Name' in result.columns


    def test_clean_columns_handles_special_characters(self, pedestrian_count_processor):
        """Test handling of various special characters"""
        df = pd.DataFrame({
            'word@test': [1],
            'test#name': [2],
            'data$value': [3]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        # Special characters should be preserved
        assert 'Word@Test' in result.columns
        assert 'Test#Name' in result.columns
        assert 'Data$Value' in result.columns


    def test_clean_columns_title_case_after_hyphen(self, pedestrian_count_processor):
        """Test that words after hyphens are capitalized"""
        df = pd.DataFrame({'first-second-third': [1]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'First - Second - Third' in result.columns


    def test_clean_columns_title_case_after_space(self, pedestrian_count_processor):
        """Test that words after spaces are capitalized"""
        df = pd.DataFrame({'first second third': [1]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'First Second Third' in result.columns


    def test_clean_columns_title_case_with_abbreviations(self, pedestrian_count_processor):
        """Test title case with common abbreviations"""
        df = pd.DataFrame({'abc def': [1], 'xyz test': [2]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'Abc Def' in result.columns
        assert 'Xyz Test' in result.columns


    def test_clean_columns_title_case_single_letter(self, pedestrian_count_processor):
        """Test title case with single letters"""
        df = pd.DataFrame({'a b c': [1], 'x-y-z': [2]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'A B C' in result.columns
        assert 'X - Y - Z' in result.columns


    def test_clean_columns_multiple_columns(self, pedestrian_count_processor):
        """Test cleaning multiple columns at once"""
        df = pd.DataFrame({
            'first-column': [1],
            'second  column': [2],
            '  third-column  ': [3],
            'FOURTH COLUMN': [4]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'First - Column' in result.columns
        assert 'Second Column' in result.columns
        assert 'Third - Column' in result.columns
        assert 'Fourth Column' in result.columns
        assert len(result.columns) == 4


    def test_clean_columns_preserves_column_order(self, pedestrian_count_processor):
        """Test that column order is preserved"""
        df = pd.DataFrame({
            'col3': [1],
            'col1': [2],
            'col2': [3]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        # Order should be preserved
        expected_order = ['Col3', 'Col1', 'Col2']
        assert list(result.columns) == expected_order


    def test_clean_columns_handles_duplicate_names_after_cleaning(self, pedestrian_count_processor):
        """Test handling when cleaning results in duplicate column names"""
        df = pd.DataFrame({
            'test-name': [1],
            'test name': [2],
            'TEST-NAME': [3]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        # All three should become 'Test - Name' or 'Test Name'
        # This will cause duplicate columns - pandas handles this
        assert len(result.columns) == 3


    def test_clean_columns_empty_dataframe(self, pedestrian_count_processor):
        """Test cleaning empty dataframe"""
        df = pd.DataFrame()
        # Should raise an error when the dataframe is empty
        with pytest.raises(Exception):
            pedestrian_count_processor._clean_columns(df)


    def test_clean_columns_single_column(self, pedestrian_count_processor):
        """Test cleaning single column"""
        df = pd.DataFrame({'test-column': [1, 2, 3]})
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'Test - Column' in result.columns
        assert len(result.columns) == 1


    def test_clean_columns_very_long_column_name(self, pedestrian_count_processor):
        """Test handling of very long column names"""
        long_name = 'this-is-a-very-long-column-name-with-many-hyphens-and-words'
        df = pd.DataFrame({long_name: [1]})
        result = pedestrian_count_processor._clean_columns(df)
        
        # Should still be properly formatted
        expected = 'This - Is - A - Very - Long - Column - Name - With - Many - Hyphens - And - Words'
        assert expected in result.columns


    def test_clean_columns_numeric_column_names(self, pedestrian_count_processor):
        """Test handling of numeric column names"""
        df = pd.DataFrame({0: [1], 1: [2], 2: [3]})
        df.columns = df.columns.astype(str)
        result = pedestrian_count_processor._clean_columns(df)
        
        assert '0' in result.columns
        assert '1' in result.columns
        assert '2' in result.columns


    def test_clean_columns_mixed_types_in_names(self, pedestrian_count_processor):
        """Test handling of mixed alphanumeric names"""
        df = pd.DataFrame({
            'col-123': [1],
            '456-test': [2],
            'abc-456-def': [3]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'Col - 123' in result.columns
        assert '456 - Test' in result.columns
        assert 'Abc - 456 - Def' in result.columns


    def test_clean_columns_real_location_names(self, pedestrian_count_processor):
        """Test with realistic Melbourne location names"""
        df = pd.DataFrame({
            'bourke-st-mall': [1],
            'flinders  street  station': [2],
            '  federation-square  ': [3],
            'MELBOURNE-CENTRAL': [4]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'Bourke - St - Mall' in result.columns
        assert 'Flinders Street Station' in result.columns
        assert 'Federation - Square' in result.columns
        assert 'Melbourne - Central' in result.columns


    def test_clean_columns_with_directional_indicators(self, pedestrian_count_processor):
        """Test with directional indicators (West, East, etc.)"""
        df = pd.DataFrame({
            'lincoln-swanston-(w)': [1],
            'elizabeth st (north)': [2],
            'collins-st-(south)': [3]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        assert 'Lincoln - Swanston - (W)' in result.columns
        assert 'Elizabeth St (North)' in result.columns
        assert 'Collins - St - (South)' in result.columns


    def test_clean_columns_preserves_data_integrity(self, pedestrian_count_processor):
        """Test that data values remain unchanged after cleaning"""
        df = pd.DataFrame({
            'col-1': [1, 2, 3],
            'col  2': [4, 5, 6],
            '  col-3  ': [7, 8, 9]
        })
        
        original_values = df.values.copy()
        result = pedestrian_count_processor._clean_columns(df)
        
        # Values should be identical
        np.testing.assert_array_equal(result.values, original_values)

    def test_clean_columns_preserves_index(self, pedestrian_count_processor):
        """Test that DataFrame index is preserved"""
        df = pd.DataFrame(
            {'col-1': [1, 2, 3]},
            index=['a', 'b', 'c']
        )
        result = pedestrian_count_processor._clean_columns(df)
        
        assert list(result.index) == ['a', 'b', 'c']


    def test_clean_columns_preserves_dtype(self, pedestrian_count_processor):
        """Test that column dtypes are preserved"""
        df = pd.DataFrame({
            'int-col': [1, 2, 3],
            'float-col': [1.1, 2.2, 3.3],
            'str-col': ['a', 'b', 'c']
        })
        
        result = pedestrian_count_processor._clean_columns(df)
        
        assert result['Int - Col'].dtype == np.int64
        assert result['Float - Col'].dtype == np.float64
        assert result['Str - Col'].dtype == object


    # Whitespace variations
    def test_clean_columns_various_whitespace_types(self, pedestrian_count_processor):
        """Test handling of various whitespace characters"""
        df = pd.DataFrame({
            'word\twith\ttab': [1],
            'word\nwith\nnewline': [2],
            'word\r\nwith\r\ncrlf': [3]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        # All whitespace should be normalized to single space
        for col in result.columns:
            assert '\t' not in col
            assert '\n' not in col
            assert '\r' not in col
            assert '  ' not in col  # No double spaces


    def test_clean_columns_consecutive_hyphens(self, pedestrian_count_processor):
        """Test handling of consecutive hyphens"""
        df = pd.DataFrame({'word--hyphen': [1], 'test---name': [2]})
        result = pedestrian_count_processor._clean_columns(df)
        
        # Each hyphen should get spaces
        assert 'Word - - Hyphen' in result.columns
        assert 'Test - - - Name' in result.columns


    def test_clean_columns_hyphen_at_start_end(self, pedestrian_count_processor):
        """Test handling of hyphens at start/end of names"""
        df = pd.DataFrame({
            '-starting': [1],
            'ending-': [2],
            '-both-': [3]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        # Should handle gracefully
        assert len(result.columns) == 3


    # Idempotency test (Applied multiple times after the initial operation without any further change)
    def test_clean_columns_idempotent(self, pedestrian_count_processor):
        """Test that running clean_columns twice gives same result"""
        df = pd.DataFrame({'test-column': [1, 2, 3]})
        
        result1 = pedestrian_count_processor._clean_columns(df)
        result2 = pedestrian_count_processor._clean_columns(result1)
        
        assert list(result1.columns) == list(result2.columns)


    def test_clean_columns_unicode_characters(self, pedestrian_count_processor):
        """Test handling of unicode characters"""
        df = pd.DataFrame({
            'café-name': [1],
            'señor-test': [2],
            '测试-column': [3]
        })
        result = pedestrian_count_processor._clean_columns(df)
        
        # Should handle unicode properly
        assert 'Café - Name' in result.columns
        assert 'Señor - Test' in result.columns
        assert '测试 - Column' in result.columns


    def test_clean_columns_empty_string_column_name(self, pedestrian_count_processor):
        """Test handling of empty string as column name"""
        df = pd.DataFrame({'': [1, 2, 3]})
        result = pedestrian_count_processor._clean_columns(df)
        
        # Empty string should remain (or be handled gracefully)
        assert '' in result.columns


    def test_clean_columns_only_hyphens(self, pedestrian_count_processor):
        """Test column name that is only hyphens"""
        df = pd.DataFrame({'---': [1]})
        result = pedestrian_count_processor._clean_columns(df)
        
        # Should handle gracefully
        assert len(result.columns) == 1

    ### End of test _clean_columns method ###


    ### Test _standardize_column_names method ###
    def test_standardize_column_names_returns_string(self, pedestrian_count_processor):
        """Test that method returns a string"""
        result = pedestrian_count_processor._standardize_column_names("Test Column")
        
        assert isinstance(result, str)


    def test_standardize_column_names_maps_exact_match(self, pedestrian_count_processor):
        """Test that exact matches are mapped correctly"""
        col = "Lincoln - Swanston (W)"
        result = pedestrian_count_processor._standardize_column_names(col)
        
        assert result == "Lincoln - Swanston (West)"


    def test_standardize_column_names_all_location_mappings(self, pedestrian_count_processor):
        """Test all predefined location mappings"""
        test_cases = {
            "Lincoln - Swanston (W)": "Lincoln - Swanston (West)",
            "Harbour Esplanade - Pedestrian Path": "Harbour Esplanade (West) - Pedestrian Path",
            "Harbour Esplanade - Bike Path": "Harbour Esplanade (West) - Bike Path",
            "Rmit Bld 80 - 445 Swanston Street": "Rmit Building 80"
        }
        
        for old_name, expected_new_name in test_cases.items():
            result = pedestrian_count_processor._standardize_column_names(old_name)
            assert result == expected_new_name, f"Failed for {old_name}"


    def test_standardize_column_names_returns_original_if_no_match(self, pedestrian_count_processor):
        """Test that original column name is returned if no mapping exists"""
        col = "Unknown Location"
        result = pedestrian_count_processor._standardize_column_names(col)
        
        assert result == col

    
    def test_standardize_column_names_empty_or_whitespaces_string(self, pedestrian_count_processor):
        """Test with empty string or whitespaces string"""
        empty_string = ""
        whitespaces_string = "       "
        empty_string_result = pedestrian_count_processor._standardize_column_names(empty_string)
        whitespaces_string_result = pedestrian_count_processor._standardize_column_names(whitespaces_string)
        
        assert empty_string_result == ""
        assert whitespaces_string_result == "       "

    
    def test_standardize_column_names_none_input(self, pedestrian_count_processor):
        """Test behavior with None input"""
        # This might raise an error or handle gracefully depending on implementation
        try:
            result = pedestrian_count_processor._standardize_column_names(None)
            # If it doesn't raise, check what it returns
            assert result is None or isinstance(result, str)
        except (TypeError, AttributeError):
            # It's acceptable to raise an error for None input
            assert True

    
    def test_standardize_column_names_numeric_string(self, pedestrian_count_processor):
        """Test with numeric string"""
        col = "12345"
        result = pedestrian_count_processor._standardize_column_names(col)
        
        assert result == "12345"


    def test_standardize_column_names_special_characters(self, pedestrian_count_processor):
        """Test with special characters"""
        col = "Test@#$%Column"
        result = pedestrian_count_processor._standardize_column_names(col)
        
        assert result == col


    def test_standardize_column_names_unicode_characters(self, pedestrian_count_processor):
        """Test with unicode characters"""
        col = "测试Column名称"
        result = pedestrian_count_processor._standardize_column_names(col)
        
        assert result == col


    ### End of test _standardize_column_names tests ###

    ### Test _cast_column_types method ###
    def test_cast_column_types_returns_dataframe(self, pedestrian_count_processor):
        """Test that method returns a dataframe"""
        result = pedestrian_count_processor._cast_column_types(pd.DataFrame({'Date': ['01/01/2022', '02/01/2022']}))
        
        assert isinstance(result, pd.DataFrame)


    def test_cast_column_types_empty_dataframe(self, pedestrian_count_processor):
        """Test casting empty dataframe"""
        df = pd.DataFrame()
        # Should raise an error when the dataframe is empty
        with pytest.raises(Exception):
            pedestrian_count_processor._cast_column_types(df)

    
    def test_cast_column_types_correct_date_format(self, pedestrian_count_processor):
        """Test that date column is cast to datetime with the correct format"""
        df = pd.DataFrame({'Date': ['01/01/2022', '02/01/2022']})
        result = pedestrian_count_processor._cast_column_types(df)
        expected = pd.DataFrame({'Date': pd.to_datetime(['01/01/2022', '02/01/2022'], format='%d/%m/%Y')})

        assert_frame_equal(result, expected)
        assert result['Date'].dtype == 'datetime64[ns]'

    
    def test_cast_column_types_invalid_date_format(self, pedestrian_count_processor):
        """Test that invalid date format is handled gracefully"""
        df = pd.DataFrame({'Date': ['not a date', '2022-01-01', '02/31/2022']})
        # Should raise an exception when invalid date format is provided
        with pytest.raises(Exception):
            result = pedestrian_count_processor._cast_column_types(df)
        
    
    def test_cast_column_types_int_values(self, pedestrian_count_processor):
        """Test that numeric values are cast to float"""
        df = pd.DataFrame({
            'Date': ['01/01/2022', '01/01/2022', '01/01/2022'],
            'Value': ['123', '678', '901']
            })
        result = pedestrian_count_processor._cast_column_types(df)
        expected = pd.DataFrame({
            'Date': pd.to_datetime(['01/01/2022', '01/01/2022', '01/01/2022'], format='%d/%m/%Y'),
            'Value': [123, 678, 901]
        })

        assert_frame_equal(result, expected)
        assert result['Value'].dtype == 'int64'

    
    def test_cast_column_types_invalid_int_values(self, pedestrian_count_processor):
        """Test that numeric values with decimal are cast to float"""
        df = pd.DataFrame({
            'Date': ['01/01/2022', '01/01/2022', '01/01/2022'],
            'Value': ['123.45', 'asdf', '901.23']
            })
        # Should raise an exception when invalid int values are provided in pedestrian count
        with pytest.raises(Exception):
            result = pedestrian_count_processor._cast_column_types(df)


    ### End of test _cast_column_types method ###


    ### Test _handle_null_values method ###
    def test_handle_null_values_returns_dataframe(self, pedestrian_count_processor):
        """Test that method returns a dataframe"""
        result = pedestrian_count_processor._handle_null_values(pd.DataFrame({'Date': ['01/01/2022', '02/01/2022']}))
        
        assert isinstance(result, pd.DataFrame)


    def test_handle_null_values_empty_dataframe(self, pedestrian_count_processor):
        """Test handling null values in empty dataframe"""
        df = pd.DataFrame()
        # Should raise an error when the dataframe is empty
        with pytest.raises(Exception):
            pedestrian_count_processor._handle_null_values(df)


    def test_handle_null_values_null_date(self, pedestrian_count_processor):
        """Test that null date values are handled gracefully"""
        df = pd.DataFrame({'Date': pd.to_datetime([pd.NaT, '02/01/2022'], format='%d/%m/%Y'), 'Value': [123, 123]})
        result = pedestrian_count_processor._handle_null_values(df)
        expected = pd.DataFrame({'Date': pd.to_datetime(['02/01/2022'], format='%d/%m/%Y'), 'Value': [123]}, index=[1])

        assert_frame_equal(result, expected)

    
    def test_handle_null_values_replaces_null_values(self, pedestrian_count_processor):
        """Test that null values are replaced with 0"""
        df = pd.DataFrame({'Date': pd.to_datetime(['01/01/2022', '02/01/2022', '03/01/2022', '04/01/2022', '05/01/2022'], format='%d/%m/%Y'), 'Value': [123, None, 'abc', '', '    ']})
        result = pedestrian_count_processor._handle_null_values(df)
        expected = pd.DataFrame({'Date': pd.to_datetime(['01/01/2022', '02/01/2022', '03/01/2022', '04/01/2022', '05/01/2022'], format='%d/%m/%Y'), 'Value': [123.0, 0.0, 0.0, 0.0, 0.0]})

        assert_frame_equal(result, expected)

    ### End of test _handle_null_values method ###


    ### Test _add_missing_areas method ###
    def test_add_missing_areas_returns_dataframe(self, pedestrian_count_processor):
        """Test that method returns a dataframe"""
        result = pedestrian_count_processor._add_missing_areas(pd.DataFrame({'Date': ['01/01/2022', '02/01/2022']}))
        
        assert isinstance(result, pd.DataFrame)


    def test_add_missing_areas_empty_dataframe(self, pedestrian_count_processor):
        """Test adding missing areas in empty dataframe"""
        df = pd.DataFrame()
        # Should raise an error when the dataframe is empty
        result = pedestrian_count_processor._add_missing_areas(df)
        expected = pd.DataFrame({
            '380 Elizabeth St': [],
            'Errol St (West)': [],
            'Flagstaff Station (East)': [],
            'La Trobe St - William St (South)': [],
            'William St - Little Lonsdale St (West)': [],
        }, dtype='int')

        assert_frame_equal(result, expected)

    
    def test_add_missing_areas_adds_missing_areas(self, pedestrian_count_processor):
        """Test that missing areas are added"""
        df = pd.DataFrame({'Date': pd.to_datetime(['01/01/2022', '02/01/2022'], format='%d/%m/%Y'), 'Area A': [123, 123]})
        result = pedestrian_count_processor._add_missing_areas(df)
        expected = pd.DataFrame({
            'Date': pd.to_datetime(['01/01/2022', '02/01/2022'], format='%d/%m/%Y'), 
            'Area A': [123, 123],
            '380 Elizabeth St': [0, 0],
            'Errol St (West)': [0, 0],
            'Flagstaff Station (East)': [0, 0],
            'La Trobe St - William St (South)': [0, 0],
            'William St - Little Lonsdale St (West)': [0, 0],
        })

        assert_frame_equal(result, expected)

    
    def test_add_missing_areas_with_existing_areas(self, pedestrian_count_processor):
        """Test that existing areas are not added"""
        df = pd.DataFrame({
            'Date': pd.to_datetime(['01/01/2022', '02/01/2022'], format='%d/%m/%Y'), 
            'Area A': [123, 123], 
            '380 Elizabeth St': [90, 80]
        })
        result = pedestrian_count_processor._add_missing_areas(df)
        expected = pd.DataFrame({
            'Date': pd.to_datetime(['01/01/2022', '02/01/2022'], format='%d/%m/%Y'), 
            'Area A': [123, 123],
            '380 Elizabeth St': [90, 80],
            'Errol St (West)': [0, 0],
            'Flagstaff Station (East)': [0, 0],
            'La Trobe St - William St (South)': [0, 0],
            'William St - Little Lonsdale St (West)': [0, 0],
        })

        assert_frame_equal(result, expected)

    ### End of test _add_missing_areas method ###


    ### Test _extract_area method ###
    def test_extract_area_returns_string(self, pedestrian_count_processor):
        """Test that method returns a string"""
        result = pedestrian_count_processor._extract_area('Area A')
        
        assert isinstance(result, str)

    
    @pytest.mark.parametrize(
        "area",
        [123, None]
    )
    def test_extract_area_input_not_string(self, pedestrian_count_processor, area):
        """Test that method raises an exception when input is not a string"""
        with pytest.raises(Exception):
            pedestrian_count_processor._extract_area(area)


    @pytest.mark.parametrize(
        "area, extracted_area", 
        [
            ("Area A", "Area A, Victoria, Australia"),
            ("Melbourne Central - Little Londsdale St (East)", "Melbourne Central, Victoria, Australia"),
            ("380 Elizabeth St", "380 Elizabeth St, Victoria, Australia"),
            ("", ", Victoria, Australia")
        ]
    )
    def test_extract_area_extracted_areas(self, pedestrian_count_processor, area, extracted_area):
        """Test that areas are correctly extracted"""
        result = pedestrian_count_processor._extract_area(area)
        
        assert result == extracted_area

    @pytest.mark.parametrize(
        "area, extracted_area", 
        [
            ("Area A", "Area A, Victoria, Australia"),
            ("Rmit Building 80 - Little Londsdale St (East)", "RMIT Building, Victoria, Australia"),
            ("Qv Market - 380 Elizabeth St", "Queen Victoria Market, Victoria, Australia"),
            ("Melbourne Central - Flinders Street Station Underpass", "Melbourne Central, Victoria, Australia")
        ]
    )
    def test_extract_area_with_nominatim_mapping_rules(self, pedestrian_count_processor, area, extracted_area):
        """Test that areas are correctly extracted with Nominatim mapping rules"""
        result = pedestrian_count_processor._extract_area(area)
        
        assert result == extracted_area

    ### End of test _extract_area method ###


    ### Test clean method ###
    def test_clean_returns_dataframe(self, pedestrian_count_processor, sample_raw_pedestrian_count_data):
        """Test that method returns a dataframe"""
        result = pedestrian_count_processor.clean(sample_raw_pedestrian_count_data)
        expected = pd.DataFrame({
            'Date': ['01/01/2022', '02/01/2022'],
            'Area A': [100, 200],
            'Melbourne Central': [100, 200],
            'Little Londsdale St (East)': [100, 200],
            '380 Elizabeth St': [100, 200],
            'Flinders Street Station Underpass': [100, 200],
            'Queen Victoria Market': [100, 200],
            'Queen Victoria Market - Elizabeth St': [100, 200]
        })
        
        assert isinstance(result, pd.DataFrame)

    
    def test_clean_empty_dataframe(self, pedestrian_count_processor):
        """Test clean method on empty dataframe"""
        df = pd.DataFrame()
        # Should raise an error when the dataframe is empty
        with pytest.raises(Exception):
            pedestrian_count_processor.clean(df)

    
    def test_clean_correctly_cleans_data(self, pedestrian_count_processor, sample_raw_pedestrian_count_data):
        """Test that method correctly cleans data"""
        result = pedestrian_count_processor.clean(sample_raw_pedestrian_count_data)
        expected = pd.DataFrame({
            'Date': pd.to_datetime(['01/01/2022', '01/01/2022'], format='%d/%m/%Y'),
            'Hour': [10, 11],
            'Area A': [100, 200],
            'Melbourne Central': [100, 200],
            'Little Londsdale St (East)': [100, 200],
            '380 Elizabeth St': [100, 200],
            'Rmit Building 80': [200, 400],
            'Queen Victoria Market': [100, 200],
            "William St - Little Lonsdale St (West)": [0, 0],
            "Errol St (West)": [0, 0],
            "Flagstaff Station (East)": [0, 0],
            "La Trobe St - William St (South)": [0, 0]
        })
        
        assert_frame_equal(result[expected.columns], expected)

    ### End of test clean method ###


    ### Test wrangle method ###
    def test_wrangle_check_added_columns(self, pedestrian_count_processor, sample_clean_pedestrian_count_data):
        result = pedestrian_count_processor.wrangle(sample_clean_pedestrian_count_data)

        assert 'datetime_AEST' in result.columns
        assert 'area' in result.columns
        assert 'pedestrian_count' in result.columns
        assert 'nominatim_area' in result.columns


    def test_wrangle_returns_dataframe(self, pedestrian_count_processor, sample_clean_pedestrian_count_data):
        """Test that method returns a dataframe"""
        result = pedestrian_count_processor.wrangle(sample_clean_pedestrian_count_data)
        
        assert isinstance(result, pd.DataFrame)

    
    def test_wrangle_empty_dataframe(self, pedestrian_count_processor):
        """Test wrangle method on empty dataframe"""
        df = pd.DataFrame()
        # Should raise an error when the dataframe is empty
        with pytest.raises(Exception):
            pedestrian_count_processor.wrangle(df)

    
    def test_wrangle_correctly_wrangles_data(self, pedestrian_count_processor, sample_clean_pedestrian_count_data):
        result = pedestrian_count_processor.wrangle(sample_clean_pedestrian_count_data)
        expected = pd.DataFrame({
            'datetime_AEST': pd.to_datetime(['01/01/2022 10:00:00', '01/01/2022 11:00:00'] * 9, format='%d/%m/%Y %H:%M:%S'),
            'area': [
                'Melbourne Central',
                'Melbourne Central',
                'Little Londsdale St (East)',
                'Little Londsdale St (East)', 
                '380 Elizabeth St', 
                '380 Elizabeth St', 
                'Rmit Building 80',
                'Rmit Building 80', 
                'Queen Victoria Market', 
                'Queen Victoria Market', 
                "William St - Little Lonsdale St (West)", 
                "William St - Little Lonsdale St (West)", 
                "Errol St (West)", 
                "Errol St (West)", 
                "Flagstaff Station (East)", 
                "Flagstaff Station (East)", 
                "La Trobe St - William St (South)",
                "La Trobe St - William St (South)"
            ],
            'pedestrian_count': [100, 200, 100, 200, 100, 200, 200, 400, 100, 200, 0, 0, 0, 0, 0, 0, 0, 0],
            'nominatim_area': [
                'melbourne central, victoria, australia',
                'melbourne central, victoria, australia', 
                'little londsdale st, victoria, australia',
                'little londsdale st, victoria, australia',
                '380 elizabeth st, victoria, australia',
                '380 elizabeth st, victoria, australia',
                'rmit building, victoria, australia',
                'rmit building, victoria, australia',
                'queen victoria market, victoria, australia',
                'queen victoria market, victoria, australia',
                "william st, victoria, australia",
                "william st, victoria, australia",
                "errol st, victoria, australia",
                "errol st, victoria, australia",
                "flagstaff station, victoria, australia",
                "flagstaff station, victoria, australia",
                "la trobe st, victoria, australia",
                "la trobe st, victoria, australia"
            ]
        })

        assert_frame_equal(result, expected)

    ### End of test wrangle method ###


    ### Test transform method ###
    def test_transform_returns_dataframe(self, pedestrian_count_processor, sample_raw_pedestrian_count_data):
        """Test that method returns a dataframe"""
        result = pedestrian_count_processor.transform(sample_raw_pedestrian_count_data)
        
        assert isinstance(result, pd.DataFrame)

    def test_transform_empty_dataframe(self, pedestrian_count_processor):
        """Test transform method on empty dataframe"""
        df = pd.DataFrame()
        # Should raise an error when the dataframe is empty
        with pytest.raises(Exception):
            pedestrian_count_processor.transform(df)

    
    def test_transform_correctly_transforms(self, pedestrian_count_processor, sample_raw_pedestrian_count_data):
        """Test transform method correctly transforms a raw data"""
        result = pedestrian_count_processor.transform(sample_raw_pedestrian_count_data)
        expected = pd.DataFrame({
            'datetime_AEST': pd.to_datetime(['01/01/2022 10:00:00', '01/01/2022 11:00:00'] * 10, format='%d/%m/%Y %H:%M:%S'),
            'area': [
                '380 Elizabeth St', 
                '380 Elizabeth St',
                'Area A',
                'Area A',
                "Errol St (West)", 
                "Errol St (West)", 
                "Flagstaff Station (East)", 
                "Flagstaff Station (East)", 
                "La Trobe St - William St (South)",
                "La Trobe St - William St (South)",
                'Little Londsdale St (East)',
                'Little Londsdale St (East)',
                'Melbourne Central',
                'Melbourne Central', 
                'Queen Victoria Market', 
                'Queen Victoria Market',
                'Rmit Building 80',
                'Rmit Building 80', 
                "William St - Little Lonsdale St (West)", 
                "William St - Little Lonsdale St (West)"
            ],
            'pedestrian_count': [100, 200, 100, 200, 0, 0, 0, 0, 0, 0, 100, 200, 100, 200, 100, 200, 200, 400, 0, 0],
            'nominatim_area': [
                '380 elizabeth st, victoria, australia',
                '380 elizabeth st, victoria, australia',
                'area a, victoria, australia',
                'area a, victoria, australia',
                "errol st, victoria, australia",
                "errol st, victoria, australia",
                "flagstaff station, victoria, australia",
                "flagstaff station, victoria, australia",
                "la trobe st, victoria, australia",
                "la trobe st, victoria, australia",
                'little londsdale st, victoria, australia',
                'little londsdale st, victoria, australia',
                'melbourne central, victoria, australia',
                'melbourne central, victoria, australia', 
                'queen victoria market, victoria, australia',
                'queen victoria market, victoria, australia',
                'rmit building, victoria, australia',
                'rmit building, victoria, australia',
                "william st, victoria, australia",
                "william st, victoria, australia"
            ]
        })

        assert_frame_equal(result, expected)

    ### End of test transform method ###
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

from src.air_quality import AirQualityProcessor


class TestAirQualityProcessor:
    """Test suite for the AirQualityProcessor class"""

    ### Test initialization ###
    def test_init_creates_instance(self):
        """Test that __init__ creates a valid instance"""
        air_quality_processor = AirQualityProcessor()
        
        assert air_quality_processor is not None
        assert isinstance(air_quality_processor, AirQualityProcessor)


    def test_init_sets_correct_attributes(self):
        """Test that __init__ sets up correct attributes"""
        proc = AirQualityProcessor()
        
        assert proc.measurements_to_exclude == ["BSP", "SWS", "VWD", "VWS", "Sigma05", "BPM2.5", "SIG05"]
        assert isinstance(proc.measurements_to_exclude, list)
        assert len(proc.measurements_to_exclude) == 7

        assert proc.cols_to_drop == [
            "datetime_local", "location_id", "validation_flag", "parameter_method_name", 
            "parameter_description", "unit_of_measure", "method_quality", "analysis_method_name"
        ]
        assert isinstance(proc.cols_to_drop, list)
        assert len(proc.cols_to_drop) == 8
        
        assert proc.num_cols == ['latitude', 'longitude', 'CO', 'DBT', 'NO2', 'O3', 'PM10', 'PM2.5', 'SO2']
        assert isinstance(proc.num_cols, list)
        assert len(proc.num_cols) == 9

        assert proc.logger is not None

    ### End of test initialization ###

    
    ### Test _cast_column_types method ###
    def test_cast_column_types_converts_to_float(self, air_quality_processor):
        """Test that numeric columns are converted to float"""
        df = pd.DataFrame({
            'datetime_AEST': ['2022-01-01 00:00:00'],
            'latitude': ['37.8136'],
            'longitude': ['144.9631'],
            'CO': ['0.5'],
            'DBT': ['25.0'],
            'NO2': ['15'],
            'O3': ['40'],
            'PM10': ['20'],
            'PM2.5': ['8'],
            'SO2': ['2']
        })
        
        result = air_quality_processor._cast_column_types(df)
        
        for col in air_quality_processor.num_cols:
            assert result[col].dtype == float


    def test_cast_column_types_converts_datetime(self, air_quality_processor):
        """Test that datetime_AEST is converted to datetime"""
        df = pd.DataFrame({
            'datetime_AEST': ['2022-01-01 00:00:00', '2022-01-01 01:00:00'],
            'latitude': [37.8136, 37.8136],
            'longitude': [144.9631, 144.9631],
            'CO': [0.5, 0.6],
            'DBT': [25.0, 26.0],
            'NO2': [15.0, 16.0],
            'O3': [40.0, 41.0],
            'PM10': [20.0, 21.0],
            'PM2.5': [8.0, 9.0],
            'SO2': [2.0, 2.1]
        })
        
        result = air_quality_processor._cast_column_types(df)
        
        assert pd.api.types.is_datetime64_any_dtype(result['datetime_AEST'])

    
    def test_cast_column_types_handles_invalid_datetime(self, air_quality_processor):
        """Test that invalid datetime strings raise error"""
        df = pd.DataFrame({
            'datetime_AEST': ['invalid-date'],
            'latitude': [37.8136],
            'longitude': [144.9631],
            'CO': [0.5],
            'DBT': [25.0],
            'NO2': [15.0],
            'O3': [40.0],
            'PM10': [20.0],
            'PM2.5': [8.0],
            'SO2': [2.0]
        })
        
        with pytest.raises(Exception):
            air_quality_processor._cast_column_types(df)


    def test_cast_column_types_handles_nan_values(self, air_quality_processor):
        """Test that NaN values are preserved during casting"""
        df = pd.DataFrame({
            'datetime_AEST': ['2022-01-01 00:00:00'],
            'latitude': [np.nan],
            'longitude': [144.9631],
            'CO': [np.nan],
            'DBT': [25.0],
            'NO2': [15.0],
            'O3': [40.0],
            'PM10': [20.0],
            'PM2.5': [8.0],
            'SO2': [2.0]
        })
        
        result = air_quality_processor._cast_column_types(df)
        
        assert pd.isna(result['latitude'].iloc[0])
        assert pd.isna(result['CO'].iloc[0])

    def test_cast_column_types_with_invalid_datetime(self, air_quality_processor):
        """Test _cast_column_types with non-datetime column"""
        df = pd.DataFrame({
            'datetime_AEST': ['not a datetime'],
            'latitude': [37.8136],
            'longitude': [144.9631],
            'CO': [0.5],
            'DBT': [25.0],
            'NO2': [15.0],
            'O3': [40.0],
            'PM10': [20.0],
            'PM2.5': [8.0],
            'SO2': [2.0]
        })
        
        with pytest.raises(Exception):
            air_quality_processor._cast_column_types(df)

    
    def test_cast_column_types_with_invalid_numeric_values(self, air_quality_processor):
        """Test _cast_column_types with non-numeric values"""
        df = pd.DataFrame({
            'datetime_AEST': ['2022-01-01 00:00:00'],
            'latitude': ['not a number'],
            'longitude': ['not a number'],
            'CO': ['not a number'],
            'DBT': ['not a number'],
            'NO2': ['not a number'],
            'O3': ['not a number'],
            'PM10': ['not a number'],
            'PM2.5': ['not a number'],
            'SO2': ['not a number']
        })
        
        with pytest.raises(Exception):
            air_quality_processor._cast_column_types(df)

    ### End of test _cast_column_types method ###


    ### Test _fill_null_values method
    def test_fill_null_values_imputes_missing_data(self, air_quality_processor):
        """Test that missing values are imputed"""
        df = pd.DataFrame({
            'datetime_AEST': pd.to_datetime(['2022-01-01', '2022-01-02', '2022-01-03']),
            'latitude': [-37.8136, -37.8136, -37.8136],
            'longitude': [144.9631, 144.9631, 144.9631],
            'CO': [0.5, np.nan, 0.6],
            'DBT': [25.0, 26.0, 27.0],
            'NO2': [15.0, 16.0, np.nan],
            'O3': [40.0, 41.0, 42.0],
            'PM10': [20.0, 21.0, 22.0],
            'PM2.5': [8.0, 9.0, 10.0],
            'SO2': [2.0, 2.1, 2.2]
        })
        
        result = air_quality_processor._fill_null_valuse(df)
        
        # Check that no NaN values remain in numeric columns
        assert not result[air_quality_processor.num_cols].isna().any().any()


    def test_fill_null_values_preserves_non_null_values(self, air_quality_processor):
        """Test that non-null values are preserved"""
        df = pd.DataFrame({
            'datetime_AEST': pd.to_datetime(['2022-01-01', '2022-01-02']),
            'latitude': [-37.8136, -37.8136],
            'longitude': [144.9631, 144.9631],
            'CO': [0.5, 0.6],
            'DBT': [25.0, 26.0],
            'NO2': [15.0, 16.0],
            'O3': [40.0, 41.0],
            'PM10': [20.0, 21.0],
            'PM2.5': [8.0, 9.0],
            'SO2': [2.0, 2.1]
        })
        
        original_values = df[air_quality_processor.num_cols].copy()
        result = air_quality_processor._fill_null_valuse(df)
        
        # Values should be identical (or very close due to imputer)
        pd.testing.assert_frame_equal(result[air_quality_processor.num_cols], original_values, check_exact=False, atol=1e-6)


    def test_fill_null_values_handles_all_missing_column(self, air_quality_processor):
        """Test handling when entire column is missing"""
        df = pd.DataFrame({
            'datetime_AEST': pd.to_datetime(['2022-01-01', '2022-01-02']),
            'latitude': [-37.8136, -37.8136],
            'longitude': [144.9631, 144.9631],
            'CO': [np.nan, np.nan],
            'DBT': [25.0, 26.0],
            'NO2': [15.0, 16.0],
            'O3': [40.0, 41.0],
            'PM10': [20.0, 21.0],
            'PM2.5': [8.0, 9.0],
            'SO2': [2.0, 2.1]
        })
        
        result = air_quality_processor._fill_null_valuse(df)
        
        # Should still produce a result (imputer should handle this)
        assert result is not None

    ### End of test _fill_null_values method ###


    ### Test _get_season method
    def test_get_season_months(self, air_quality_processor):
        """Test that seasons are correctly identified"""
        df = pd.DataFrame({
            'month': [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        })
        
        result = air_quality_processor._get_season(df)
        
        assert all(result['season'] == ['summer', 'summer', 'summer', 'autumn', 'autumn', 'autumn', 'winter', 'winter', 'winter', 'spring', 'spring', 'spring'])

    ### End of test _get_season method ###


    ### Test clean method ###
    def test_clean_removes_excluded_measurements(self, air_quality_processor, sample_raw_data):
        """Test that excluded measurements are removed"""
        # Add an excluded measurement
        excluded_data = sample_raw_data.copy()
        excluded_row = excluded_data.iloc[0].copy()
        excluded_row['parameter_name'] = 'BSP'
        excluded_data = pd.concat([excluded_data, excluded_row.to_frame().T], ignore_index=True)
        
        result = air_quality_processor.clean(excluded_data)
        
        # Excluded measurements should not be in the columns
        forbidden = set(air_quality_processor.measurements_to_exclude)
        assert forbidden.isdisjoint(result.columns)


    def test_clean_drops_specified_columns(self, air_quality_processor, sample_raw_data):
        """Test that specified columns are dropped"""
        result = air_quality_processor.clean(sample_raw_data)
        
        for col in air_quality_processor.cols_to_drop:
            assert col not in result.columns


    def test_clean_pivots_data_correctly(self, air_quality_processor, sample_raw_data):
        """Test that data is pivoted correctly"""
        result = air_quality_processor.clean(sample_raw_data)
        
        # Should have parameter names as columns
        assert all([col in result.columns for col in air_quality_processor.num_cols])
        
        # Should have fewer rows after pivoting
        assert len(result) < len(sample_raw_data)

    
    def test_clean_handles_negative_values(self, air_quality_processor, sample_raw_data_has_negative_values):
        """Test that negative values are handled correctly"""
        result = air_quality_processor.clean(sample_raw_data_has_negative_values)
        
        # Should not have any negative values in numeric columns except for temperature (DBT)
        assert result['CO'].iloc[0] == 0
        assert result['NO2'].iloc[0] == 0
        assert result['PM10'].iloc[0] == 0
        assert result['DBT'].iloc[0] == -19
        assert result['O3'].iloc[0] == 0
        assert result['PM2.5'].iloc[0] == 0
        assert result['SO2'].iloc[0] == 0


    def test_clean_with_empty_dataframe(self, air_quality_processor):
        """Test clean with empty dataframe"""
        df = pd.DataFrame(columns=[
            'datetime_AEST', 'datetime_local', 'location_id', 'location_name',
            'latitude', 'longitude', 'parameter_name', 'parameter_method_name',
            'parameter_description', 'value', 'unit_of_measure', 'validation_flag',
            'method_quality', 'analysis_method_name'
        ])
        
        # Should handle gracefully or raise appropriate error
        try:
            result = air_quality_processor.clean(df)
            assert len(result) == 0
        except Exception as e:
            # It's acceptable to raise an error for empty data
            assert True

    
    def test_clean_with_missing_columns(self, air_quality_processor):
        """Test clean with missing required columns"""
        df = pd.DataFrame({
            'datetime_AEST': ['2022-01-01 00:00:00'],
            'parameter_name': ['CO'],
            'value': [0.5]
        })
        
        with pytest.raises(KeyError):
            air_quality_processor.clean(df)

    ### End of test clean ###


    ### Test wrangle method ###
    def test_wrangle_extracts_time_features(self, air_quality_processor, sample_clean_data):
        """Test that time features are correctly extracted"""
        result = air_quality_processor.wrangle(sample_clean_data)
        
        assert 'month' in result.columns
        assert 'date' in result.columns
        assert 'day' in result.columns
        assert 'hour' in result.columns
        assert 'season' in result.columns


    def test_wrangle_correct_month_extraction(self, air_quality_processor, sample_clean_data):
        """Test that month is extracted correctly"""
        result = air_quality_processor.wrangle(sample_clean_data)
        expected_result = pd.DataFrame({
            'month': [1, 1, 1, 1, 1, 1, 1]
        }, dtype='int32')
        
        assert_frame_equal(result[['month']], expected_result)

    
    def test_wrangle_correct_hour_extraction(self, air_quality_processor, sample_clean_data):
        """Test that hour is extracted correctly"""
        result = air_quality_processor.wrangle(sample_clean_data)
        expected_result = pd.DataFrame({
            'hour': [1, 1, 1, 1, 1, 1, 1]
        }, dtype='int32')
        
        assert_frame_equal(result[['hour']], expected_result)


    def test_wrangle_correct_season_assignment(self, air_quality_processor, sample_clean_data):
        """Test that seasons are assigned correctly"""
        result = air_quality_processor.wrangle(sample_clean_data)
        expected_result = pd.DataFrame({
            'season': ['summer', 'summer', 'summer', 'summer', 'summer', 'summer', 'summer']
        }, dtype='object')
        
        assert_frame_equal(result[['season']], expected_result)

    
    def test_wrangle_preserves_original_columns(self, air_quality_processor, sample_clean_data):
        """Test that original columns are preserved"""
        original_cols = list(sample_clean_data.columns)
        result = air_quality_processor.wrangle(sample_clean_data)
        
        for col in original_cols:
            assert col in result.columns

    ### End of test wrangle method ###

    ### Test aggregate method ###
    def test_aggregate_groups_by_datetime(self, air_quality_processor, sample_wrangled_data):
        """Test that data is grouped by datetime and time features"""
        result = air_quality_processor.aggregate(sample_wrangled_data)
        
        grouping_cols = ["datetime_AEST", "month", "date", "day", "hour", "season"]
        for col in grouping_cols:
            assert col in result.columns


    def test_aggregate_computes_median(self, air_quality_processor):
        """Test that median is computed for pollutants"""
        df = pd.DataFrame({
            'datetime_AEST': pd.to_datetime(['2022-01-01 10:00:00'] * 3),
            'month': [1, 1, 1],
            'date': [pd.Timestamp('2022-01-01').date()] * 3,
            'day': [1, 1, 1],
            'hour': [10, 10, 10],
            'season': ['summer', 'summer', 'summer'],
            'CO': [0.5, 0.6, 0.7],
            'DBT': [25.0, 26.0, 27.0],
            'NO2': [15.0, 16.0, 17.0],
            'O3': [40.0, 41.0, 42.0],
            'PM10': [20.0, 21.0, 22.0],
            'PM2.5': [8.0, 9.0, 10.0],
            'SO2': [2.0, 2.1, 2.2]
        })
        
        result = air_quality_processor.aggregate(df)
        
        # Should have one row after aggregation
        assert len(result) == 1
        
        # Check median values
        assert result['CO'].iloc[0] == 0.6
        assert result['DBT'].iloc[0] == 26.0
        assert result['NO2'].iloc[0] == 16.0
        assert result['O3'].iloc[0] == 41.0
        assert result['PM10'].iloc[0] == 21.0
        assert result['PM2.5'].iloc[0] == 9.0
        assert result['SO2'].iloc[0] == 2.1


    def test_aggregate_handles_single_value_groups(self, air_quality_processor, sample_wrangled_data):
        """Test aggregation with single values per group"""
        result = air_quality_processor.aggregate(sample_wrangled_data)
        
        # Should have same number of rows (each datetime is unique)
        assert len(result) == len(sample_wrangled_data)


    def test_aggregate_reduces_multiple_locations(self, air_quality_processor):
        """Test that multiple locations at same time are aggregated"""
        df = pd.DataFrame({
            'datetime_AEST': pd.to_datetime(['2022-01-01 10:00:00'] * 2),
            'month': [1, 1],
            'date': [pd.Timestamp('2022-01-01').date()] * 2,
            'day': [1, 1],
            'hour': [10, 10],
            'season': ['summer', 'summer'],
            'CO': [0.5, 0.7],
            'DBT': [25.0, 27.0],
            'NO2': [15.0, 17.0],
            'O3': [40.0, 42.0],
            'PM10': [20.0, 22.0],
            'PM2.5': [8.0, 10.0],
            'SO2': [2.0, 2.2]
        })
        
        result = air_quality_processor.aggregate(df)
        
        # Should aggregate to single row
        assert len(result) == 1

    ### End of test aggregate method ###

    ### Test transform method ###
    def test_transform_calls_all_steps(self, air_quality_processor, sample_raw_data):
        """Test that transform calls clean, wrangle, and aggregate"""
        with patch.object(air_quality_processor, 'clean', wraps=air_quality_processor.clean) as mock_clean, \
             patch.object(air_quality_processor, 'wrangle', wraps=air_quality_processor.wrangle) as mock_wrangle, \
             patch.object(air_quality_processor, 'aggregate', wraps=air_quality_processor.aggregate) as mock_aggregate:
            
            result = air_quality_processor.transform(sample_raw_data)
            
            mock_clean.assert_called_once()
            mock_wrangle.assert_called_once()
            mock_aggregate.assert_called_once()


    def test_transform_logs_progress(self, air_quality_processor, sample_raw_data):
        """Test that transform logs each step"""
        result = air_quality_processor.transform(sample_raw_data)
        
        # Check that all logging calls were made
        log_calls = [call[0][0] for call in air_quality_processor.logger.info.call_args_list]
        
        assert any("Cleaning" in msg for msg in log_calls)
        assert any("Wrangling" in msg for msg in log_calls)
        assert any("Aggregating" in msg for msg in log_calls)
        assert any("completed" in msg for msg in log_calls)


    def test_transform_returns_dataframe(self, air_quality_processor, sample_raw_data):
        """Test that transform returns a DataFrame"""
        result = air_quality_processor.transform(sample_raw_data)
        
        assert isinstance(result, pd.DataFrame)


    def test_transform_produces_expected_columns(self, air_quality_processor, sample_raw_data):
        """Test that transform produces expected columns"""
        result = air_quality_processor.transform(sample_raw_data)
        
        expected_cols = ["datetime_AEST", "month", "date", "day", "hour", "season",
                        "CO", "DBT", "NO2", "O3", "PM10", "PM2.5", "SO2"]
        
        for col in expected_cols:
            assert col in result.columns

    ### End of test transform method ###

    ### Test save_data method ###
    def test_save_data_creates_file(self, air_quality_processor, sample_wrangled_data, tmp_path):
        """Test that save_data creates a CSV file"""
        file_path = tmp_path / "test_output.csv"
        
        air_quality_processor.save_data(sample_wrangled_data, file_path)
        
        assert file_path.exists()


    def test_save_data_logs_save(self, air_quality_processor, sample_wrangled_data, tmp_path):
        """Test that save_data logs the save operation"""
        file_path = tmp_path / "test_output.csv"
        
        air_quality_processor.save_data(sample_wrangled_data, file_path)
        
        air_quality_processor.logger.info.assert_called_with(f"Saved air quality data to {file_path}")


    def test_save_data_content_correct(self, air_quality_processor, sample_wrangled_data, tmp_path):
        """Test that saved file contains correct data"""
        file_path = tmp_path / "test_output.csv"
        
        air_quality_processor.save_data(sample_wrangled_data, file_path)
        
        loaded_data = pd.read_csv(file_path)
        assert len(loaded_data) == len(sample_wrangled_data)
        assert list(loaded_data.columns) == list(sample_wrangled_data.columns)


    def test_save_data_handles_path_object(self, air_quality_processor, sample_wrangled_data, tmp_path):
        """Test that save_data works with Path objects"""
        file_path = tmp_path / "test_output.csv"
        
        # Should not raise exception
        air_quality_processor.save_data(sample_wrangled_data, file_path)
        assert file_path.exists()


    def test_save_data_overwrites_existing(self, air_quality_processor, sample_wrangled_data, tmp_path):
        """Test that save_data overwrites existing files"""
        file_path = tmp_path / "test_output.csv"
        
        # Create initial file
        air_quality_processor.save_data(sample_wrangled_data, file_path)
        initial_mtime = file_path.stat().st_mtime
        
        # Adds a delay before saving again
        time.sleep(0.1)
        air_quality_processor.save_data(sample_wrangled_data, file_path)
        new_mtime = file_path.stat().st_mtime
        
        assert new_mtime > initial_mtime

    ### End of test save_data method ###

    

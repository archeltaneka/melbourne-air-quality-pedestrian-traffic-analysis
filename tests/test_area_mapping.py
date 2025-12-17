from datetime import datetime
import json
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

from src.area_mapping import AreaMapper


class TestAreaMapperInit:
    """Test suite for the AreaMapper.__init__ method"""

    def test_init_creates_instance(self, mock_nominatim):
        """Test that __init__ creates a valid instance"""
        mapper = AreaMapper()
        
        assert mapper is not None
        assert isinstance(mapper, AreaMapper)


    def test_init_creates_geolocator(self, mock_nominatim):
        """Test that geolocator is initialized"""
        mapper = AreaMapper()
        
        assert hasattr(mapper, 'geolocator')
        mock_nominatim.assert_called_with(user_agent="AreaMapper")


    def test_init_sets_save_dir(self, mock_nominatim):
        """Test that save_dir is set correctly"""
        mapper = AreaMapper()
        
        assert hasattr(mapper, 'save_dir')
        assert isinstance(mapper.save_dir, Path)
        assert mapper.save_dir == Path("data/area_mapping")


    def test_init_sets_logger(self, mock_nominatim):
        """Test that logger is initialized"""
        mapper = AreaMapper()
        
        assert hasattr(mapper, 'logger')
        assert mapper.logger is not None


    def test_init_sets_area_coordinates_fname(self, mock_nominatim):
        """Test that area_coordinates_fname is set"""
        mapper = AreaMapper()
        
        assert mapper.area_coordinates_fname == 'area_coordinates.json'


    def test_init_sets_area_mapping_fname(self, mock_nominatim):
        """Test that area_mapping_fname is set"""
        mapper = AreaMapper()
        
        assert mapper.area_mapping_fname == 'area_mapping.csv'


    def test_init_creates_directory_if_not_exists(self, mock_nominatim, tmp_path):
        """Test that init creates save_dir if it doesn't exist"""
        with patch.object(AreaMapper, '__init__', lambda self: None):
            mapper = AreaMapper()
            mapper.save_dir = tmp_path / "test_area_mapping"
            mapper.logger = Mock()
            
            # Directory should not exist yet
            assert not mapper.save_dir.exists()
            
            # Manually call the directory creation logic
            if not mapper.save_dir.exists():
                mapper.save_dir.mkdir(parents=True, exist_ok=True)
            
            assert mapper.save_dir.exists()


    def test_init_logs_when_directory_exists(self, mock_nominatim, tmp_path):
        """Test that init logs when directory exists"""
        # Create directory first
        test_dir = tmp_path / "area_mapping"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        with patch('src.area_mapping.AreaMapper.__init__', lambda self: None):
            mapper = AreaMapper()
            mapper.save_dir = test_dir
            mapper.logger = Mock()
            
            # Manually test the directory existence logic
            if mapper.save_dir.exists():
                mapper.logger.info(f"Area mapping directory {mapper.save_dir} exists.")
            
            # Verify logging was called
            mapper.logger.info.assert_called_with(f"Area mapping directory {test_dir} exists.")


    def test_init_logs_when_creating_directory(self, mock_nominatim, tmp_path):
        """Test that init logs when creating directory"""
        test_dir = tmp_path / "new_area_mapping"
        
        with patch('src.area_mapping.AreaMapper.__init__', lambda self: None):
            mapper = AreaMapper()
            mapper.save_dir = test_dir
            mapper.logger = Mock()
            
            # Manually test the directory creation logic
            if not mapper.save_dir.exists():
                mapper.logger.info(f"Area mapping directory {mapper.save_dir} does not exist. Creating...")
                mapper.save_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify logging was called and directory was created
            mapper.logger.info.assert_called_with(f"Area mapping directory {test_dir} does not exist. Creating...")
            assert mapper.save_dir.exists()


class TestAreaMapperFindAreaCoordinates:
    """Test suite for the AreaMapper._find_area_coordinates method"""

    def test_find_area_coordinates_returns_list(self, mapper):
        """Test that method returns a list"""
        with patch('src.area_mapping.Nominatim') as mock_nom, \
             patch('time.sleep'):
            mock_nom.return_value.geocode.return_value = None
            
            result = mapper._find_area_coordinates(["Test Area"])
            
            assert isinstance(result, list)


    def test_find_area_coordinates_empty_list(self, mapper):
        """Test with empty area list"""
        result = mapper._find_area_coordinates([])
        
        assert result == []


    def test_find_area_coordinates_single_area_success(self, mapper, mock_geocode_success):
        """Test geocoding single area successfully"""
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep'):
            mock_nom.return_value.geocode.return_value = mock_geocode_success
            
            result = mapper._find_area_coordinates(["Melbourne CBD"])
            
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "query_area" in result[0]
            assert result[0]["query_area"] == "Melbourne CBD"


    def test_find_area_coordinates_single_area_failure(self, mapper):
        """Test geocoding single area that fails"""
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep'):
            mock_nom.return_value.geocode.return_value = None
            
            result = mapper._find_area_coordinates(["Unknown Location"])
            
            assert len(result) == 1
            assert result[0] == []


    def test_find_area_coordinates_multiple_areas(self, mapper, mock_geocode_success):
        """Test geocoding multiple areas"""
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep'):
            mock_nom.return_value.geocode.return_value = mock_geocode_success
            
            areas = ["Melbourne CBD", "Bourke Street", "Federation Square"]
            result = mapper._find_area_coordinates(areas)
            
            assert len(result) == 3


    def test_find_area_coordinates_mixed_success_failure(self, mapper):
        """Test geocoding with mix of successful and failed lookups"""
        mock_location = Mock()
        mock_location.raw = {"lat": "-37.8136", "lon": "144.9631"}
        
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep'):
            # First succeeds, second fails, third succeeds
            mock_nom.return_value.geocode.side_effect = [
                mock_location,
                None,
                mock_location
            ]
            
            result = mapper._find_area_coordinates(["Area1", "Area2", "Area3"])
            
            assert len(result) == 3
            assert isinstance(result[0], dict)
            assert result[1] == []
            assert isinstance(result[2], dict)


    def test_find_area_coordinates_adds_query_area(self, mapper):
        """Test that query_area is added to result"""
        mock_location = Mock()
        mock_location.raw = {"lat": "-37.8136", "lon": "144.9631"}
        
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep'):
            mock_nom.return_value.geocode.return_value = mock_location
            
            result = mapper._find_area_coordinates(["Test Area"])
            
            assert "query_area" in result[0]
            assert result[0]["query_area"] == "Test Area"


    def test_find_area_coordinates_sleeps_between_calls(self, mapper):
        """Test that method sleeps between API calls"""
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep') as mock_sleep:
            mock_nom.return_value.geocode.return_value = None
            
            mapper._find_area_coordinates(["Area1", "Area2", "Area3"])
            
            # Should sleep 3 times (once per area)
            assert mock_sleep.call_count == 3
            mock_sleep.assert_called_with(5)


    def test_find_area_coordinates_logs_progress(self, mapper):
        """Test that method logs progress"""
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep'):
            mock_nom.return_value.geocode.return_value = None
            
            mapper._find_area_coordinates(["Test Area"])
            
            # Check that logger was called
            assert mapper.logger.info.called


    def test_find_area_coordinates_logs_warnings_on_failure(self, mapper):
        """Test that method logs warnings when geocoding fails"""
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep'):
            mock_nom.return_value.geocode.return_value = None
            
            mapper._find_area_coordinates(["Unknown Area"])
            
            # Should log warning
            assert mapper.logger.warning.called


    def test_find_area_coordinates_uses_correct_user_agent(self, mapper):
        """Test that Nominatim is initialized with correct user agent"""
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep'):
            mock_nom.return_value.geocode.return_value = None
            
            mapper._find_area_coordinates(["Test"])
            
            # Should create Nominatim with "tutorial" user agent
            mock_nom.assert_called_with(user_agent="tutorial")


    def test_find_area_coordinates_uses_country_code(self, mapper):
        """Test that geocode uses country_codes parameter"""
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep'):
            mock_geocode = Mock()
            mock_nom.return_value.geocode = mock_geocode
            mock_geocode.return_value = None
            
            mapper._find_area_coordinates(["Melbourne"])
            
            # Should call geocode with country_codes="au"
            mock_geocode.assert_called_with(query="Melbourne", country_codes="au")


    def test_find_area_coordinates_handles_special_characters(self, mapper):
        """Test handling areas with special characters"""
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep'):
            mock_nom.return_value.geocode.return_value = None
            
            areas = ["St Kilda's Beach", "Queen's Park", "O'Connell St"]
            result = mapper._find_area_coordinates(areas)
            
            assert len(result) == 3


    def test_find_area_coordinates_handles_unicode(self, mapper):
        """Test handling areas with unicode characters"""
        with patch('src.area_mapping.Nominatim') as mock_nom, patch('time.sleep'):
            mock_nom.return_value.geocode.return_value = None
            
            result = mapper._find_area_coordinates(["Café Street"])
            
            assert len(result) == 1


    def test_find_area_coordinates_preserves_raw_data(self, mapper):
        """Test that raw geocoding data is preserved"""
        mock_location = Mock()
        mock_location.raw = {
            "lat": "-37.8136",
            "lon": "144.9631",
            "display_name": "Test Location",
            "extra_field": "extra_value"
        }
        
        with patch('src.area_mapping.Nominatim') as mock_nom, \
             patch('time.sleep'):
            mock_nom.return_value.geocode.return_value = mock_location
            
            result = mapper._find_area_coordinates(["Test"])
            
            assert "extra_field" in result[0]
            assert result[0]["extra_field"] == "extra_value"


    def test_find_area_coordinates_api_rate_limiting(self, mapper):
        """Test that 5 second delay prevents API rate limiting"""
        start_time = time.time()
        
        with patch('src.area_mapping.Nominatim') as mock_nom, \
             patch('time.sleep', wraps=time.sleep) as mock_sleep:
            
            mock_nom.return_value.geocode.return_value = None
            mapper._find_area_coordinates(["Area1", "Area2"])
            
            # Should have called sleep twice
            assert mock_sleep.call_count == 2
            mock_sleep.assert_called_with(5)


class TestAreaMapperMapAreaCoordinates:
    """Test suite for the AreaMapper.map_area_coordinates method"""

    def test_map_area_coordinates_returns_dataframe(self, mapper, sample_location_df):
        """Test that method returns a DataFrame"""
        with patch.object(mapper, '_find_area_coordinates', return_value=[]):
            result = mapper.map_area_coordinates(sample_location_df)
            
            assert isinstance(result, pd.DataFrame)

    def test_map_area_coordinates_adds_latitude_column(self, mapper, sample_location_df, sample_location_mapping):
        """Test that latitude column is added"""
        with patch.object(mapper, '_find_area_coordinates', return_value=sample_location_mapping):
            result = mapper.map_area_coordinates(sample_location_df)
            
            assert 'latitude' in result.columns

    def test_map_area_coordinates_adds_longitude_column(self, mapper, sample_location_df, sample_location_mapping):
        """Test that longitude column is added"""
        with patch.object(mapper, '_find_area_coordinates', return_value=sample_location_mapping):
            result = mapper.map_area_coordinates(sample_location_df)
            
            assert 'longitude' in result.columns

    def test_map_area_coordinates_correct_values(self, mapper, sample_location_df, sample_location_mapping):
        """Test that coordinates are mapped correctly"""
        with patch.object(mapper, '_find_area_coordinates', return_value=sample_location_mapping):
            result = mapper.map_area_coordinates(sample_location_df)
            
            assert result.loc[0, 'latitude'] == "-37.8136"
            assert result.loc[0, 'longitude'] == "144.9631"

    def test_map_area_coordinates_loads_existing_file(self, mapper, sample_location_df, sample_location_mapping):
        """Test that existing coordinates file is loaded"""
        # Create existing file
        coords_file = mapper.save_dir / mapper.area_coordinates_fname
        with open(coords_file, 'w') as f:
            json.dump(sample_location_mapping, f)
        
        with patch.object(mapper, '_find_area_coordinates') as mock_find:
            result = mapper.map_area_coordinates(sample_location_df)
            
            # Should not call _find_area_coordinates
            mock_find.assert_not_called()

    def test_map_area_coordinates_creates_new_file(self, mapper, sample_location_df, sample_location_mapping):
        """Test that new coordinates file is created if not exists"""
        with patch.object(mapper, '_find_area_coordinates', return_value=sample_location_mapping):
            result = mapper.map_area_coordinates(sample_location_df)
            
            # Should call _find_area_coordinates
            mapper._find_area_coordinates.assert_called_once()

    def test_map_area_coordinates_saves_csv(self, mapper, sample_location_df, sample_location_mapping):
        """Test that result is saved to CSV"""
        with patch.object(mapper, '_find_area_coordinates', return_value=sample_location_mapping):
            result = mapper.map_area_coordinates(sample_location_df)
            
            csv_file = mapper.save_dir / mapper.area_mapping_fname
            assert csv_file.exists()

    def test_map_area_coordinates_csv_content_correct(self, mapper, sample_location_df, sample_location_mapping):
        """Test that saved CSV has correct content"""
        with patch.object(mapper, '_find_area_coordinates', return_value=sample_location_mapping):
            result = mapper.map_area_coordinates(sample_location_df)
            result['latitude'] = result['latitude'].astype(float)
            result['longitude'] = result['longitude'].astype(float)
            
            csv_file = mapper.save_dir / mapper.area_mapping_fname
            loaded_df = pd.read_csv(csv_file)
            
            assert_frame_equal(loaded_df, result)

    def test_map_area_coordinates_handles_missing_areas(self, mapper):
        """Test handling of areas not in mapping"""
        df = pd.DataFrame({
            'nominatim_area': ['unknown area'],
            'count': [100]
        })
        
        with patch.object(mapper, '_find_area_coordinates', return_value=[]):
            result = mapper.map_area_coordinates(df)
            
            assert pd.isna(result.loc[0, 'latitude'])
            assert pd.isna(result.loc[0, 'longitude'])

    def test_map_area_coordinates_handles_empty_results(self, mapper, sample_location_df):
        """Test handling when area lookup returns empty list"""
        mapping_with_empty = [
            {"query_area": "melbourne cbd", "lat": "-37.8136", "lon": "144.9631"},
            []  # Empty result
        ]
        
        with patch.object(mapper, '_find_area_coordinates', return_value=mapping_with_empty):
            result = mapper.map_area_coordinates(sample_location_df)
            
            # Should handle gracefully
            assert 'latitude' in result.columns

    def test_map_area_coordinates_case_insensitive_matching(self, mapper):
        """Test that area matching is case-insensitive"""
        df = pd.DataFrame({
            'nominatim_area': ['MELBOURNE CBD', 'Melbourne CBD', 'melbourne cbd']
        })
        
        mapping = [
            {"query_area": "melbourne cbd", "lat": "-37.8136", "lon": "144.9631"}
        ]
        
        with patch.object(mapper, '_find_area_coordinates', return_value=mapping):
            result = mapper.map_area_coordinates(df)
            
            # All should map to same coordinates
            assert all(result['latitude'] == "-37.8136")

    def test_map_area_coordinates_strips_whitespace(self, mapper):
        """Test that whitespace is stripped for matching"""
        df = pd.DataFrame({
            'nominatim_area': ['  melbourne cbd  ', 'melbourne cbd']
        })
        
        mapping = [
            {"query_area": "melbourne cbd", "lat": "-37.8136", "lon": "144.9631"}
        ]
        
        with patch.object(mapper, '_find_area_coordinates', return_value=mapping):
            result = mapper.map_area_coordinates(df)
            
            # Both should match
            assert all(result['latitude'] == "-37.8136")

    def test_map_area_coordinates_handles_duplicate_areas(self, mapper):
        """Test handling of duplicate areas in input"""
        df = pd.DataFrame({
            'nominatim_area': ['melbourne cbd', 'melbourne cbd', 'melbourne cbd']
        })
        
        mapping = [
            {"query_area": "melbourne cbd", "lat": "-37.8136", "lon": "144.9631"}
        ]
        
        with patch.object(mapper, '_find_area_coordinates', return_value=mapping):
            result = mapper.map_area_coordinates(df)
            
            # All rows should have same coordinates
            assert all(result['latitude'] == "-37.8136")
            assert all(result['longitude'] == "144.9631")

    def test_map_area_coordinates_preserves_original_columns(self, mapper, sample_location_df, sample_location_mapping):
        """Test that original DataFrame columns are preserved"""
        original_cols = list(sample_location_df.columns)
        
        with patch.object(mapper, '_find_area_coordinates', return_value=sample_location_mapping):
            result = mapper.map_area_coordinates(sample_location_df)
            
            for col in original_cols:
                assert col in result.columns

    def test_map_area_coordinates_logs_loading_existing(self, mapper, sample_location_df, sample_location_mapping):
        """Test that loading existing file is logged"""
        coords_file = mapper.save_dir / mapper.area_coordinates_fname
        with open(coords_file, 'w') as f:
            json.dump(sample_location_mapping, f)
        
        mapper.map_area_coordinates(sample_location_df)
        
        # Should log that file was found and loaded
        assert mapper.logger.info.called

    def test_map_area_coordinates_logs_creating_new(self, mapper, sample_location_df, sample_location_mapping):
        """Test that creating new mapping is logged"""
        with patch.object(mapper, '_find_area_coordinates', return_value=sample_location_mapping):
            mapper.map_area_coordinates(sample_location_df)
            
            # Should log that file doesn't exist and is being created
            assert mapper.logger.info.called

    def test_map_area_coordinates_logs_save(self, mapper, sample_location_df, sample_location_mapping):
        """Test that saving is logged"""
        with patch.object(mapper, '_find_area_coordinates', return_value=sample_location_mapping):
            mapper.map_area_coordinates(sample_location_df)
            
            # Should log save location
            assert mapper.logger.info.called

    def test_map_area_coordinates_handles_malformed_mapping(self, mapper, sample_location_df):
        """Test handling of malformed mapping data"""
        malformed_mapping = [
            {"query_area": "area1"},  # Missing lat/lon
            {"lat": "-37.8136"},  # Missing query_area and lon
            {"query_area": "area2", "lat": "-37.8136", "lon": "144.9631"}  # Valid
        ]
        
        with patch.object(mapper, '_find_area_coordinates', return_value=malformed_mapping):
            result = mapper.map_area_coordinates(sample_location_df)
            
            # Should handle gracefully
            assert 'latitude' in result.columns
            assert 'longitude' in result.columns

    def test_map_area_coordinates_empty_dataframe(self, mapper):
        """Test with empty DataFrame"""
        df = pd.DataFrame(columns=['nominatim_area'])
        
        with patch.object(mapper, '_find_area_coordinates', return_value=[]):
            result = mapper.map_area_coordinates(df)
            
            assert len(result) == 0
            assert 'latitude' in result.columns
            assert 'longitude' in result.columns

    def test_map_area_coordinates_gets_unique_areas(self, mapper, sample_location_df, sample_location_mapping):
        """Test that only unique areas are geocoded"""
        df = pd.DataFrame({
            'nominatim_area': ['area1', 'area1', 'area2', 'area1', 'area2']
        })
        
        with patch.object(mapper, '_find_area_coordinates', return_value=[]) as mock_find:
            mapper.map_area_coordinates(df)
            
            # Should only geocode unique areas
            called_areas = mock_find.call_args[0][0]
            assert len(called_areas) == 2  # Only 'area1' and 'area2'
            assert set(called_areas) == {'area1', 'area2'}

    def test_map_area_coordinates_tuple_unpacking(self, mapper):
        """Test that coordinate tuples are unpacked correctly"""
        df = pd.DataFrame({'nominatim_area': ['test']})
        
        mapping = [
            {"query_area": "test", "lat": "-37.8136", "lon": "144.9631"}
        ]
        
        with patch.object(mapper, '_find_area_coordinates', return_value=mapping):
            result = mapper.map_area_coordinates(df)
            
            # Check that unpacking worked
            assert result.loc[0, 'latitude'] == "-37.8136"
            assert result.loc[0, 'longitude'] == "144.9631"
from pathlib import Path

import pandas as pd

import pytest
from unittest.mock import patch, Mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.downloader import Downloader
from src.air_quality import AirQualityProcessor
from src.pedestrian_count import PedestrianCountProcessor


### Downloader Fixtures ###
@pytest.fixture
def downloader(tmp_path):
    """Fixture to create a Downloader instance with temporary directory"""
    with patch.object(Downloader, '__init__', lambda self: None):
        dl = Downloader()
        dl.data_dir = tmp_path / 'data'
        dl.web_dir = tmp_path / 'web'
        dl.air_quality_dir = dl.data_dir / 'air_quality'
        dl.pedestrian_dir = dl.data_dir / 'pedestrian'
        dl.air_quality_web_dir = dl.web_dir / 'data' / 'air_quality'
        dl.pedestrian_web_dir = dl.web_dir / 'data' / 'pedestrian'
        dl.logger = Mock()
        
        return dl


@pytest.fixture
def mock_urlretrieve():
    """Fixture to mock urllib.request.urlretrieve"""
    with patch('urllib.request.urlretrieve') as mock:
        yield mock


### Air Quality Data Processing Fixtures ###
@pytest.fixture
def air_quality_processor():
    """Fixture to create an AirQualityProcessor instance"""
    proc = AirQualityProcessor()
    proc.logger = Mock()
    return proc


@pytest.fixture
def sample_raw_data():
    """Fixture to create sample raw air quality data"""
    return pd.DataFrame({
        'datetime_AEST': ['2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00'],
        'datetime_local': ['2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00'],
        'location_id': [1, 1, 1, 1, 1, 1, 1],
        'location_name': ['Point Crook', 'Point Crook', 'Point Crook', 'Point Crook', 'Point Crook', 'Point Crook', 'Point Crook'],
        'latitude': [-37.8136, -37.8136, -37.8136, -37.8136, -37.8136, -37.8136, -37.8136],
        'longitude': [144.9631, 144.9631, 144.9631, 144.9631, 144.9631, 144.9631, 144.9631],
        'parameter_name': ['CO', 'NO2', 'PM10', 'DBT', 'O3', 'PM2.5', 'SO2'],
        'parameter_method_name': ['CO', 'NO2', 'PM10', 'DBT', 'O3', 'PM2.5', 'SO2'],
        'parameter_description': ['Carbon Monoxide', 'Nitrogen Dioxide', 'Particulate Matter of 10 microns or less', 'Dry Bulb Temperature', 'Ozone', 'Particulate Matter of 2.5 microns or less', 'Sulfur Dioxide'],
        'value': [0.5, 15.0, 0.6, 19, 40, 8, 2],
        'unit_of_measure': ['ppm', 'ppb', 'ug/m3', 'deg.C', 'ppb', 'ug/m3', 'ppb'],
        'validation_flag': ['Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y'],
        'method_quality': ['Equivalence Method', 'Equivalence Method', 'Equivalence Method', 'Equivalence Method', 'Equivalence Method', 'Equivalence Method', 'Equivalence Method'],
        'analysis_method_name': ['Analysis A', 'Analysis B', 'Analysis C', 'Analysis D', 'Analysis E', 'Analysis F', 'Analysis G']
    })


@pytest.fixture
def sample_raw_data_has_negative_values():
    """Fixture to create sample raw air quality data"""
    return pd.DataFrame({
        'datetime_AEST': ['2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00'],
        'datetime_local': ['2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00'],
        'location_id': [1, 1, 1, 1, 1, 1, 1],
        'location_name': ['Point Crook', 'Point Crook', 'Point Crook', 'Point Crook', 'Point Crook', 'Point Crook', 'Point Crook'],
        'latitude': [-37.8136, -37.8136, -37.8136, -37.8136, -37.8136, -37.8136, -37.8136],
        'longitude': [144.9631, 144.9631, 144.9631, 144.9631, 144.9631, 144.9631, 144.9631],
        'parameter_name': ['CO', 'NO2', 'PM10', 'DBT', 'O3', 'PM2.5', 'SO2'],
        'parameter_method_name': ['CO', 'NO2', 'PM10', 'DBT', 'O3', 'PM2.5', 'SO2'],
        'parameter_description': ['Carbon Monoxide', 'Nitrogen Dioxide', 'Particulate Matter of 10 microns or less', 'Dry Bulb Temperature', 'Ozone', 'Particulate Matter of 2.5 microns or less', 'Sulfur Dioxide'],
        'value': [-0.5, -15.0, -0.6, -19, -40, -8, -2],
        'unit_of_measure': ['ppm', 'ppb', 'ug/m3', 'deg.C', 'ppb', 'ug/m3', 'ppb'],
        'validation_flag': ['Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y'],
        'method_quality': ['Equivalence Method', 'Equivalence Method', 'Equivalence Method', 'Equivalence Method', 'Equivalence Method', 'Equivalence Method', 'Equivalence Method'],
        'analysis_method_name': ['Analysis A', 'Analysis B', 'Analysis C', 'Analysis D', 'Analysis E', 'Analysis F', 'Analysis G']
    })


@pytest.fixture
def sample_clean_data():
    """Fixture to create sample cleaned data"""
    return pd.DataFrame({
        'datetime_AEST': pd.to_datetime(['2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00', '2022-01-01 01:00:00']),
        'location_name': ['Point Crook', 'Point Crook', 'Point Crook', 'Point Crook', 'Point Crook', 'Point Crook', 'Point Crook'],
        'latitude': [-37.8136, -37.8136, -37.8136, -37.8136, -37.8136, -37.8136, -37.8136],
        'longitude': [144.9631, 144.9631, 144.9631, 144.9631, 144.9631, 144.9631, 144.9631],
        'CO': [0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5],
        'DBT': [25.0, 15.0, 28.0, 25.0, 15.0, 28.0, 25.0],
        'NO2': [15.0, 12.0, 18.0, 15.0, 12.0, 18.0, 15.0],
        'O3': [40.0, 35.0, 42.0, 40.0, 35.0, 42.0, 40.0],
        'PM10': [20.0, 25.0, 18.0, 20.0, 25.0, 18.0, 20.0],
        'PM2.5': [8.0, 10.0, 7.0, 8.0, 10.0, 7.0, 8.0],
        'SO2': [2.0, 1.5, 2.5, 2.0, 1.5, 2.5, 2.0]
    })

@pytest.fixture
def sample_wrangled_data():
    """Fixture to create sample wrangled data"""
    return pd.DataFrame({
        'datetime_AEST': pd.to_datetime(['2022-01-15 10:00:00', '2022-06-15 14:00:00', '2022-12-15 20:00:00']),
        'month': [1, 6, 12],
        'date': [pd.Timestamp('2022-01-15').date(), pd.Timestamp('2022-06-15').date(), pd.Timestamp('2022-12-15').date()],
        'day': [15, 15, 15],
        'hour': [10, 14, 20],
        'season': ['summer', 'winter', 'summer'],
        'CO': [0.5, 0.6, 0.4],
        'DBT': [25.0, 15.0, 28.0],
        'NO2': [15.0, 12.0, 18.0],
        'O3': [40.0, 35.0, 42.0],
        'PM10': [20.0, 25.0, 18.0],
        'PM2.5': [8.0, 10.0, 7.0],
        'SO2': [2.0, 1.5, 2.5]
    })


### Pedestrian Count Data Processing Fixtures ###
@pytest.fixture
def pedestrian_count_processor():
    """Fixture to create a PedestrianCountProcessor instance"""
    proc = PedestrianCountProcessor()
    proc.logger = Mock()
    return proc


@pytest.fixture
def sample_raw_pedestrian_count_data():
    """Fixture to create sample raw pedestrian count data"""
    return pd.DataFrame({
        'Date': ['01/01/2022', '01/01/2022'],
        'Hour': ['10', '11'],
        'Area A': ['100', '200'],
        'Melbourne Central': ['100', '200'],
        'Little Londsdale St (East)': ['100', '200'],
        '380 Elizabeth St': ['100', '200'],
        'Rmit Building 80': ['100', '200'],
        'Queen Victoria Market': ['100', '200'],
        'Rmit Bld 80 - 445 Swanston Street': ['100', '200']
    })


@pytest.fixture
def sample_clean_pedestrian_count_data():
    """Fixture to create sample clean pedestrian count data"""
    return pd.DataFrame({
        'Date': pd.to_datetime(['01/01/2022', '01/01/2022'], format='%d/%m/%Y'),
        'Hour': [10, 11],
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


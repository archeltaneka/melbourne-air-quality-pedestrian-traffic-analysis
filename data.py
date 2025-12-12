from glob import glob
from pathlib import Path

import pandas as pd

from src.air_quality import AirQualityProcessor
from src.area_mapping import AreaMapper
from src.downloader import Downloader
from src.pedestrian_count import PedestrianCountProcessor


if __name__ == '__main__':
    DATA_DIR = Path('data')

    # Download air quality and pedestrian activity data
    data_downloader = Downloader()
    data_downloader.download()

    # Preprocess air quality data
    air_quality_processor = AirQualityProcessor()
    air_quality_df = pd.read_excel(DATA_DIR/'air_quality/2022_air_quality_vic.xlsx', sheet_name='AllData')
    air_quality_df = air_quality_processor.transform(air_quality_df)
    air_quality_processor.save_data(air_quality_df, DATA_DIR/'air_quality/air_quality_final.csv')

    # Preprocess pedestrian data
    pedestrian_processor = PedestrianCountProcessor()
    pedestrian_files = glob(str(DATA_DIR/'pedestrian/*_pedestrian_level.csv'))
    pedestrian_dfs = [pd.read_csv(file) for file in pedestrian_files if file != 'pedestrian_count_final.csv']
    pedestrian_df = pd.concat(pedestrian_dfs)
    pedestrian_df = pedestrian_processor.transform(pedestrian_df)

    # Create and save area and latlong mapping
    location_df = pedestrian_df[['nominatim_area']].copy()
    location_df = location_df.drop_duplicates(subset=["nominatim_area"])
    area_mapper = AreaMapper()
    location_df = area_mapper.map_area_coordinates(location_df)

    # Join the area and latlong mapping to the pedestrian data
    pedestrian_df = pd.merge(pedestrian_df, location_df, on="nominatim_area", how="left")
    pedestrian_df = pedestrian_df.drop(columns=["nominatim_area"], axis=1)
    pedestrian_processor.save_data(pedestrian_df, DATA_DIR/'pedestrian/pedestrian_count_final.csv')


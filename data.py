from glob import glob
from pathlib import Path

import pandas as pd

from src.air_quality import AirQualityProcessor
from src.downloader import Downloader
from src.pedestrian_count import PedestrianCountProcessor


if __name__ == '__main__':
    DATA_DIR = Path('data')

    data_downloader = Downloader()
    data_downloader.download()

    air_quality_processor = AirQualityProcessor()
    air_quality_df = pd.read_excel(DATA_DIR/'air_quality/2022_air_quality_vic.xlsx', sheet_name='AllData')
    air_quality_df = air_quality_processor.transform(air_quality_df)

    pedestrian_processor = PedestrianCountProcessor()
    pedestrian_files = glob(str(DATA_DIR/'pedestrian/*.csv'))
    pedestrian_dfs = [pd.read_csv(file) for file in pedestrian_files]
    pedestrian_df = pd.concat(pedestrian_dfs)
    pedestrian_df = pedestrian_processor.transform(pedestrian_df)

    print(air_quality_df.head())
    print(pedestrian_df.head())


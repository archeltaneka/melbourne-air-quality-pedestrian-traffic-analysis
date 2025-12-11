import logging
import os
from pathlib import Path
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class Downloader:
    def __init__(self):
        self.data_dir = Path('data')
        self.air_quality_dir = self.data_dir/'air_quality'
        self.pedestrian_dir = self.data_dir/'pedestrian'
        self.logger = logging.getLogger(__name__)
    
    def _setup(self):
        self.logger.info('Setting up data directory...')
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.air_quality_dir.exists():
            self.air_quality_dir.mkdir(parents=True, exist_ok=True)
        if not self.pedestrian_dir.exists():
            self.pedestrian_dir.mkdir(parents=True, exist_ok=True)

    def _download(self, url, save_path):
        self.logger.info(f"Downloading {url} to {save_path}...")
        try:
            urllib.request.urlretrieve(url, save_path)
            self.logger.info(f"Downloaded {url} to {save_path}")
        except Exception as e:
            self.logger.error(f"Failed to download {url}: {e}")

    def download(self):
        self._setup()

        air_quality_url = "https://apps.epa.vic.gov.au/datavic/Data_Vic/AirWatch/2022_All_sites_air_quality_hourly_avg_AIR-I-F-V-VH-O-S1-DB-M2-4-0.xlsx"
        air_quality_save_path = self.air_quality_dir/'2022_air_quality_vic.xlsx'
        self._download(url=air_quality_url, save_path=air_quality_save_path)

        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        base_pedestrian_url = "https://www.pedestrian.melbourne.vic.gov.au/datadownload/"
        for month in months:
            pedestrian_url = base_pedestrian_url + month + "_2022.csv"
            pedestrian_save_path = self.pedestrian_dir/f'{month}_2022_pedestrian_level.csv'
            self._download(url=pedestrian_url, save_path=pedestrian_save_path)

        self.logger.info("Download completed.")

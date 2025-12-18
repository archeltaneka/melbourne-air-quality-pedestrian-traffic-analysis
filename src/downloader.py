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
    """
    Downloader class for downloading air quality and pedestrian data.

    Attributes
    ----------
    data_dir: pathlib.Path
        Directory for storing downloaded data.
    web_dir: pathlib.Path
        Directory for storing downloaded web data.
    air_quality_dir: pathlib.Path
        Directory for storing downloaded air quality data.
    pedestrian_dir: pathlib.Path
        Directory for storing downloaded pedestrian data.
    air_quality_web_dir: pathlib.Path
        Directory for storing downloaded air quality web data.
    pedestrian_web_dir: pathlib.Path
        Directory for storing downloaded pedestrian web data.
    logger: logging.Logger
        Logger for logging messages.

    Methods
    -------
    _setup()
        Set up the data directory and its subdirectories.
    _download(url: str, save_path: Path)
        Download a file from a URL to a specified path.
    download()
        Download both air quality and pedestrian data.
    """

    def __init__(self):
        self.data_dir = Path('data')
        self.web_dir = Path('web')
        self.air_quality_dir = self.data_dir/'air_quality'
        self.pedestrian_dir = self.data_dir/'pedestrian'
        self.air_quality_web_dir = self.web_dir/'data/air_quality'
        self.pedestrian_web_dir = self.web_dir/'data/pedestrian'
        self.logger = logging.getLogger(__name__)
    
    def _setup(self) -> None:
        """
        Set up the data directory and its subdirectories.

        Parameters
        ---------
        None

        Returns
        -------
        None
        """

        self.logger.info('Setting up data directory...')
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.air_quality_dir.exists():
            self.air_quality_dir.mkdir(parents=True, exist_ok=True)
        if not self.pedestrian_dir.exists():
            self.pedestrian_dir.mkdir(parents=True, exist_ok=True)
        if not self.air_quality_web_dir.exists():
            self.air_quality_web_dir.mkdir(parents=True, exist_ok=True)
        if not self.pedestrian_web_dir.exists():
            self.pedestrian_web_dir.mkdir(parents=True, exist_ok=True)

    def _download(self, url: str, save_path: Path) -> None:
        """
        Download a file from a URL to a specified path.

        Parameters
        ---------
        url: str
            URL of the file to download.
        save_path: Path
            Path to save the downloaded file.

        Returns
        -------
        None
        """

        self.logger.info(f"Downloading {url} to {save_path}...")
        try:
            urllib.request.urlretrieve(url, save_path)
            self.logger.info(f"Downloaded {url} to {save_path}")
        except Exception as e:
            self.logger.error(f"Failed to download {url}: {e}")

    def download(self) -> None:
        """
        Download both air quality and pedestrian data.

        Parameters
        ---------
        None

        Returns
        -------
        None
        """

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

import json
import logging
from pathlib import Path
import re
import time

from geopy.geocoders import Nominatim


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class AreaMapper:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="AreaMapper")
        self.save_dir = Path("data/area_mapping")
        self.logger = logging.getLogger(__name__)
        self.area_coordinates_fname = 'area_coordinates.json'
        self.area_mapping_fname = 'area_mapping.csv'

        if not self.save_dir.exists():
            self.logger.info(f"Area mapping directory {self.save_dir} does not exist. Creating...")
            self.save_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.logger.info(f"Area mapping directory {self.save_dir} exists.")

    def _find_area_coordinates(self, area_list):
        self.logger.info("Creating location mapping for each pedestrian area...")
        location_mapping = []
        for area in area_list:
            self.logger.info(f"Querying {area}...")

            time.sleep(5) # Add a timeout to avoid overloading the API
            app = Nominatim(user_agent="tutorial")

            location = app.geocode(query=area, country_codes="au")
            if location is None:
                self.logger.warning(f"{area} can't be queried, appending empty list instead...")
                location = []
                location_mapping.append(location)
            else:
                result = location.raw
                result["query_area"] = area
                location_mapping.append(result)

        return location_mapping

        json_obj = json.dumps(location_mapping, indent=4)
        with open(self.save_dir/self.area_coordinates_fname, "w") as f:
            f.write(json_obj)
        self.logger.info(f"Location mapping saved to {self.save_dir/self.area_coordinates_fname}")

    def map_area_coordinates(self, location_df):
        self.logger.info("Creating area to coordinates mapping...")

        # Load location mapping directly if exists
        if (self.save_dir/self.area_coordinates_fname).exists():
            self.logger.info(f'Found existing location mapping file {self.save_dir/self.area_coordinates_fname}. Loading...')
            with open(self.save_dir/self.area_coordinates_fname, "r") as f:
                location_mapping = json.load(f)
        # Create area-coordinates mapping otherwise
        else:
            self.logger.info(f"Location mapping file {self.save_dir/self.area_coordinates_fname} does not exist. Creating...")
            area_list = location_df['nominatim_area'].unique().tolist()
            location_mapping = self._find_area_coordinates(area_list)

        area_to_coordinates = {
            result["query_area"].strip().lower(): (result["lat"], result["lon"])
            for result in location_mapping
            if isinstance(result, dict) and "query_area" in result and "lat" in result and "lon" in result
        }
        location_df['latitude'] = location_df['nominatim_area'].apply(
            lambda x: area_to_coordinates.get(x.strip().lower(), (None, None))[0]  # Get latitude or None
        )
        location_df['longitude'] = location_df['nominatim_area'].apply(
            lambda x: area_to_coordinates.get(x.strip().lower(), (None, None))[1]  # Get longitude or None
        )

        location_df.to_csv(self.save_dir/self.area_mapping_fname, index=False)
        self.logger.info(f"Area coordinates mapping saved to {self.save_dir/self.area_mapping_fname}")

        return location_df

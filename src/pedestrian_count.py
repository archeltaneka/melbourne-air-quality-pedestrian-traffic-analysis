import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class PedestrianCountProcessor:
    def __init__(self):
        self.location_mapping = {
            "Lincoln - Swanston (W)": "Lincoln - Swanston (West)",
            "Harbour Esplanade - Pedestrian Path": "Harbour Esplanade (West) - Pedestrian Path",
            "Harbour Esplanade - Bike Path": "Harbour Esplanade (West) - Bike Path",
            "Rmit Bld 80 - 445 Swanston Street": "Rmit Building 80" 
        }
        self.cols_to_add = [
            "William St - Little Lonsdale St (West)",
            "Errol St (West)",
            "Flagstaff Station (East)",
            "380 Elizabeth St",
            "La Trobe St - William St (South)"
        ]
        self.logger = logging.getLogger(__name__)

    def _clean_columns(self, df):
        df.columns = (
            df.columns
              .str.replace("-", " - ", regex=False)  # Standardize the spelling of place names
              .str.replace(r"\s+", " ", regex=True)  # Remove any extra spaces
              .str.strip()
              .str.title()
        )

        return df

    def _standardize_column_names(self, col):
        for old_name, new_name in self.location_mapping.items():
            if old_name in col:
                return new_name
        return col

    def _cast_column_types(self, df):
        object_cols = [col for col in df.columns if col != 'Date']
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        for col in object_cols:
            df[col] = df[col].astype(int)

        return df

    def _handle_null_values(self, df):
        df['Date'] = df['Date'].dropna(axis=0) # Remove rows with null Date values
        object_cols = [col for col in df.columns if col != 'Date']
        for col in object_cols:
            df[col] = df[col].replace(r'^(?!\d+\.?\d*$).*', 0, regex=True) # Replace non-numeric values with 0
            df[col] = df[col].fillna(0)

        return df

    def _add_missing_areas(self, df):
        missing_cols = set(self.cols_to_add) - set(df.columns)
        for col in missing_cols:
            df[col] = 0

        return df

    def _get_season(self, df):
        df['season'] = np.where(
            df['month'].isin([12, 1, 2]), 
            'summer', 
            np.where(
                df['month'].isin([3, 4, 5]), 
                'autumn', 
                np.where(
                    df['month'].isin([6, 7, 8]), 
                    'winter', 
                    'spring'
                )
            )
        )

        return df

    def clean(self, df):
        df = self._clean_columns(df)
        df = self._handle_null_values(df)
        df.columns = [self._standardize_column_names(col) for col in df.columns]
        df = self._cast_column_types(df)
        df = self._add_missing_areas(df)
        df = df.groupby(level=0, axis=1).sum() # Merge columns with the same name after mapping

        return df
    
    def wrangle(self, df):
        df['month'] = df['Date'].dt.month
        df['date'] = df['Date'].dt.date
        df['day'] = df['Date'].dt.day
        df = self._get_season(df)
        df['datetime_AEST'] = df['Date'].astype(str) + " " + df['Hour'].astype(str).str.zfill(2) + ":00:00"
        df['datetime_AEST'] = pd.to_datetime(df['datetime_AEST'], format='%Y-%m-%d %H:%M:%S')

        return df
    
    def transform(self, df):
        self.logger.info("Cleaning pedestrian count data...")
        df = self.clean(df)
        self.logger.info("Wrangling pedestrian count data...")
        df = self.wrangle(df)

        return df

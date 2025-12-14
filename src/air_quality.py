import logging
import pandas as pd
import numpy as np

from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class AirQualityProcessor:
    def __init__(self):
        self.measurements_to_exclude = ["BSP", "SWS", "VWD", "VWS", "Sigma05", "BPM2.5", "SIG05"]
        self.cols_to_drop = [
            "datetime_local", "location_id", "validation_flag", "parameter_method_name", 
            "parameter_description", "unit_of_measure", "method_quality", "analysis_method_name"
        ]
        self.num_cols = ['latitude', 'longitude', 'CO', 'DBT', 'NO2', 'O3', 'PM10', 'PM2.5', 'SO2'] 
        self.logger = logging.getLogger(__name__)

    def _cast_column_types(self, df):
        for col in self.num_cols:
            df[col] = df[col].astype(float)
        df['datetime_AEST'] = pd.to_datetime(df['datetime_AEST'])

        return df

    def _fill_null_valuse(self, df):
        knn_imputer = IterativeImputer(max_iter=10, random_state=0)
        features = df[self.num_cols]
        # IterativeImputer will raise an error when all values in the column are null
        # Thus, we just replace them with a constant value 0
        for col in features.columns:
            if features[col].isnull().all():
                features[col] = 0
        knn_imputer.fit(features)
        df[self.num_cols] = np.where(df[self.num_cols].isnull(), knn_imputer.transform(features), df[self.num_cols])

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
        df = df.query("parameter_name not in @self.measurements_to_exclude")
        df = df.drop(columns=self.cols_to_drop, axis=1)
        df = df.pivot(
            index=["datetime_AEST", "location_name", "latitude", "longitude"],
            columns="parameter_name", 
            values="value"
        ).reset_index()
        
        df = self._cast_column_types(df)
        df = self._fill_null_valuse(df)
        for col in self.num_cols:
            if col not in ['latitude', 'longitude', 'DBT']:
                df[col] = np.where(df[col] < 0, 0, df[col])

        return df

    def wrangle(self, df):
        df['month'] = df['datetime_AEST'].dt.month
        df['date'] = df['datetime_AEST'].dt.date
        df['day'] = df['datetime_AEST'].dt.day
        df['hour'] = df['datetime_AEST'].dt.hour
        df = self._get_season(df)

        return df

    def aggregate(self, df):
        df = df.groupby(["datetime_AEST", "month", "date", "day", "hour", "season"]).agg({
            "CO": "median",
            "DBT": "median",
            "NO2": "median",
            "O3": "median",
            "PM10": "median",
            "PM2.5": "median",
            "SO2": "median"
        }).reset_index()

        return df

    def transform(self, df):
        self.logger.info("Cleaning air quality data...")
        df = self.clean(df)
        self.logger.info("Wrangling air quality data...")
        df = self.wrangle(df)
        self.logger.info("Aggregating air quality data...")
        df = self.aggregate(df)
        self.logger.info("Processing air quality data completed.")

        return df

    def save_data(self, df, fname):
        df.to_csv(fname, index=False)
        self.logger.info(f"Saved air quality data to {fname}")

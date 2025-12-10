import pandas as pd
import numpy as np

from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer


class AirQualityProcessor:
    def __init__(self):
        self.measurements_to_include = ["BSP", "SWS", "VWD", "VWS", "Sigma05", "BPM2.5"]
        self.cols_to_drop = [
            "datetime_local", "location_id", "validation_flag", "parameter_method_name", 
            "parameter_description", "unit_of_measure", "method_quality", "analysis_method_name"
        ]
        self.num_cols = [
            'latitude', 'longitude', 'CO', 'DBT', 'NO2', 'O3', 
            'PM10', 'PM2.5', 'SIG05', 'SO2'
        ] 

    def _cast_column_types(self, df):
        for col in self.num_cols:
            df[col] = df[col].astype(float)
        df['datetime_AEST'] = pd.to_datetime(df['datetime_AEST'])

        return df

    def _fill_null_valuse(self, df):
        knn_imputer = IterativeImputer(max_iter=10, random_state=0)
        features = df[self.num_cols]
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
        df = df.query("parameter_name not in @self.measurements_to_include")
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

    def transform(self, df):
        df = self.clean(df)
        df = self.wrangle(df)
        
        return df
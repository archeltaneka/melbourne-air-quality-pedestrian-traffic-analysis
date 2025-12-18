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
    """
    Air quality data processor.

    Attributes
    ----------
    measurements_to_exclude: list
        List of measurements to exclude. We only care about temperature and 
        pollutant measurements (CO, NO2, O3, PM10, PM2.5, SO2)
    cols_to_drop: list
        List of unused columns to drop.
    num_cols: list
        List of numeric columns.
    logger: logging.Logger
        Logger for logging messages.

    Methods
    -------
    _cast_column_types(df: pd.DataFrame) -> pd.DataFrame
        Cast column types to numeric.
    _fill_null_valuse(df: pd.DataFrame) -> pd.DataFrame
        Fill null values using IterativeImputer.
    clean(df: pd.DataFrame) -> pd.DataFrame
        Clean the data.
    wrangle(df: pd.DataFrame) -> pd.DataFrame
        Wrangle the data.
    aggregate(df: pd.DataFrame) -> pd.DataFrame
        Aggregate the data.
    transform(df: pd.DataFrame) -> pd.DataFrame
        Transform the data.
    save_data(df: pd.DataFrame, fname: str) -> None
        Save the data to a CSV file.
    """

    def __init__(self):
        self.measurements_to_exclude = ["BSP", "SWS", "VWD", "VWS", "Sigma05", "BPM2.5", "SIG05"]
        self.cols_to_drop = [
            "datetime_local", "location_id", "validation_flag", "parameter_method_name", 
            "parameter_description", "unit_of_measure", "method_quality", "analysis_method_name"
        ]
        self.num_cols = ['latitude', 'longitude', 'CO', 'DBT', 'NO2', 'O3', 'PM10', 'PM2.5', 'SO2'] 
        self.logger = logging.getLogger(__name__)

    def _cast_column_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cast datetime_AEST to datetime and the rest of the columns to float.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to cast column types.

        Returns
        -------
        pd.DataFrame
            DataFrame with casted column types.
        """

        for col in self.num_cols:
            df[col] = df[col].astype(float)
        df['datetime_AEST'] = pd.to_datetime(df['datetime_AEST'])

        return df

    def _fill_null_valuse(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fill null values using IterativeImputer.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to fill null values.

        Returns
        -------
        pd.DataFrame
            DataFrame with filled null values.
        """

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

    def _get_season(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get season based on month.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to get season.

        Returns
        -------
        pd.DataFrame
            DataFrame with season.
        """

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

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the data by:
        - Filtering out unrelated measurements.
        - Dropping unused columns.
        - Pivoting the data from wide to long format.
        - Casting column types.
        - Imputing null values.
        - Converting negative values to 0 for numeric columns except latitude, longitude, and temperature values.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to clean.

        Returns
        -------
        pd.DataFrame
            Cleaned DataFrame.
        """

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

    def wrangle(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Wrangle the data by adding temporal features such as month, date, day, hour, and season.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to wrangle.

        Returns
        -------
        pd.DataFrame
            Wrangled DataFrame.
        """

        df['month'] = df['datetime_AEST'].dt.month
        df['date'] = df['datetime_AEST'].dt.date
        df['day'] = df['datetime_AEST'].dt.day
        df['hour'] = df['datetime_AEST'].dt.hour
        df = self._get_season(df)

        return df

    def aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate the data by their temporal features so that one row represents the air quality
        at a specific time by using the median aggregation function.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to aggregate.

        Returns
        -------
        pd.DataFrame
            Aggregated DataFrame.
        """

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

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the data by putting together cleaning, wrangling, and aggregating methods.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to transform.

        Returns
        -------
        pd.DataFrame
            Transformed DataFrame.
        """

        self.logger.info("Cleaning air quality data...")
        df = self.clean(df)
        self.logger.info("Wrangling air quality data...")
        df = self.wrangle(df)
        self.logger.info("Aggregating air quality data...")
        df = self.aggregate(df)
        self.logger.info("Processing air quality data completed.")

        return df

    def save_data(self, df: pd.DataFrame, fname: str) -> None:
        """
        Save the data to a CSV file.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to save.
        fname : str
            File name to save the DataFrame to.
        """

        df.to_csv(fname, index=False)
        self.logger.info(f"Saved air quality data to {fname}")

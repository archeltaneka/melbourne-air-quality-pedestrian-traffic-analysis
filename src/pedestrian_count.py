import logging
import re
from typing import List

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class PedestrianCountProcessor:
    """
    Pedestrian count data processor.

    Attributes
    ----------
    location_mapping : dict
        Dictionary mapping area names to their standard spellings.
    nominatim_mapping_rules : dict
        Dictionary mapping area names to their standard spellings for Nominatim API.
    cols_to_add : list
        List of area names to add to the dataset.
    logger : logging.Logger
        Logger for logging messages.

    Methods
    -------
    clean(df: pd.DataFrame) -> pd.DataFrame
        Clean the data by removing null values and adding missing areas.
    wrangle(df: pd.DataFrame) -> pd.DataFrame
        Wrangle the data by pivoting it into long format and extracting area names.
    transform(df: pd.DataFrame) -> pd.DataFrame
        Transform the data by cleaning, wrangling, and aggregating it.
    save_data(df: pd.DataFrame, fname: str) -> None
        Save the data to a CSV file.
    """

    def __init__(self):
        # These area names refer to the same location but with different spellings
        self.location_mapping = {
            "Lincoln - Swanston (W)": "Lincoln - Swanston (West)",
            "Harbour Esplanade - Pedestrian Path": "Harbour Esplanade (West) - Pedestrian Path",
            "Harbour Esplanade - Bike Path": "Harbour Esplanade (West) - Bike Path",
            "Rmit Bld 80 - 445 Swanston Street": "Rmit Building 80" 
        }

        # These nominatim mapping rules below is needed because the Nominatim API cannot find the exact location of these areas
        self.nominatim_mapping_rules = {
            "Bourke St Bridge": "Bourke St",
            "Flinders Street Station Underpass": "Flinders Street Station",
            "Melbourne Convention Exhibition Centre": "MCEC",
            "Qv Market": "Queen Victoria Market",
            "Qvm": "Queen Victoria Market",
            "Rmit Building 14": "RMIT Building",
            "Rmit Building 80": "RMIT Building"
        }

        # The pedestrian count data is not consistent
        # Some of these area names do not exist in the historical pedestrian count dataset
        self.cols_to_add = [
            "William St - Little Lonsdale St (West)",
            "Errol St (West)",
            "Flagstaff Station (East)",
            "380 Elizabeth St",
            "La Trobe St - William St (South)"
        ]
        
        self.logger = logging.getLogger(__name__)

    def _clean_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the columns by standardizing the spelling of place names.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to clean.

        Returns
        -------
        pd.DataFrame
            Cleaned DataFrame.

        Raises
        ------
        ValueError
            If the DataFrame is empty.
        """
        
        if len(df) == 0:
            raise ValueError("DataFrame is empty")

        df.columns = (
            df.columns
              .str.replace("-", " - ", regex=False)  # Standardize the spelling of place names
              .str.replace(r"\s+", " ", regex=True)  # Remove any extra spaces
              .str.strip()
              .str.title()
        )

        return df

    def _standardize_column_names(self, col: List[str]) -> List[str]:
        """
        Standardize the column names by replacing the old names with the new names.

        Parameters
        ----------
        col : List[str]
            List of column names to standardize.

        Returns
        -------
        List[str]
            Standardized column names.
        """

        for old_name, new_name in self.location_mapping.items():
            if old_name in col:
                return new_name
        return col

    def _cast_column_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cast the Date column to datetime with %d/%m/%Y format 
        and the other columns (pedestrian count in each area) to int.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to cast column types.

        Returns
        -------
        pd.DataFrame
            DataFrame with column types cast to int.
        """

        int_cols = [col for col in df.columns if col != 'Date']
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        for col in int_cols:
            df[col] = df[col].astype(int)

        return df

    def _handle_null_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle null values by removing rows with null Date values and replacing non-numeric values with 0.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to handle null values.

        Returns
        -------
        pd.DataFrame
            DataFrame with null values handled.
        """

        df = df.dropna(subset=['Date'], axis=0) # Remove rows with null Date values
        int_cols = [col for col in df.columns if col != 'Date']
        for col in int_cols:
            df[col] = df[col].replace(r'^(?!\d+\.?\d*$).*', 0, regex=True) # Replace non-numeric values with 0
            df[col] = df[col].fillna(0)

        return df

    def _add_missing_areas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add missing areas to the dataset by adding 0 to the missing areas.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to add missing areas to.

        Returns
        -------
        pd.DataFrame
            DataFrame with missing areas added.
        """

        missing_cols = sorted(set(self.cols_to_add) - set(df.columns))
        for col in missing_cols:
            df[col] = 0

        return df

    def _get_season(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get the season of each row based on the month.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to get season from.

        Returns
        -------
        pd.DataFrame
            DataFrame with season added.
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

    def _extract_area(self, area: str) -> str:
        """
        Extract the area name from the area column.

        Parameters
        ----------
        area : str
            Area name to extract.

        Returns
        -------
        str
            Extracted area name with ", Victoria, Australia" appended for clarity.
        """

        # If the area contains more than 1 area name, only take the first one
        match = re.split(r'[-(]', area, maxsplit=1)
        extracted_area = match[0].strip()
        if extracted_area not in self.nominatim_mapping_rules:
            return extracted_area + ", Victoria, Australia"  # Take the first part and strip whitespace
        return self.nominatim_mapping_rules[extracted_area] + ", Victoria, Australia"  # Fallback: return the entire first area name if no match

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the DataFrame by:
        - Removing null values.
        - Standardizing column names.
        - Casting column types.
        - Adding missing areas.
        - Aggregate and sum the pedestrian count for areas that have the same name after mapping.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to clean.

        Returns
        -------
        pd.DataFrame
            Cleaned DataFrame.
        """
        
        df = self._clean_columns(df)
        df = self._handle_null_values(df)
        df.columns = [self._standardize_column_names(col) for col in df.columns]
        df = self._cast_column_types(df)
        df = self._add_missing_areas(df)
        df = df.groupby(level=0, axis=1).sum() # Merge columns with the same name after mapping

        return df
    
    def wrangle(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Wrangle the DataFrame by:
        - Adding datetime_AEST temporal feature column.
        - Pivot the data from wide to long format.
        - Add nominatim_area column for the Nominatim API latitude-longitude search.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to wrangle.

        Returns
        -------
        pd.DataFrame
            Wrangled DataFrame.
        """

        df['datetime_AEST'] = df['Date'].astype(str) + " " + df['Hour'].astype(str).str.zfill(2) + ":00:00"
        df['datetime_AEST'] = pd.to_datetime(df['datetime_AEST'], format='%Y-%m-%d %H:%M:%S')
        # Pivot the data into long format for easier visualization
        df = pd.melt(
            df.drop(columns=['Date', 'Hour'], axis=1),
            id_vars=['datetime_AEST'],
            var_name='area',
            value_name='pedestrian_count'
        )
        df['nominatim_area'] = df["area"].apply(self._extract_area)
        df['nominatim_area'] = df['nominatim_area'].str.strip().str.lower()

        return df
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the DataFrame by combining cleaning and wrangling steps.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to transform.

        Returns
        -------
        pd.DataFrame
            Transformed DataFrame.
        """
        
        self.logger.info("Cleaning pedestrian count data...")
        df = self.clean(df)
        self.logger.info("Wrangling pedestrian count data...")
        df = self.wrangle(df)
        self.logger.info("Processing pedestrian count data completed.")

        return df

    def save_data(self, df: pd.DataFrame, fname: str) -> None:
        """
        Save the DataFrame to a CSV file.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to save.
        fname : str
            File name to save the DataFrame to.

        Returns
        -------
        None
        """

        df.to_csv(fname, index=False)
        self.logger.info(f"Saved pedestrian count data to {fname}")

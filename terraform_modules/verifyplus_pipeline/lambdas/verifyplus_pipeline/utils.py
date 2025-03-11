import re
import pandas as pd
import numpy as np


def to_camel_case(s):
    """
    Convert a string to camel case.
    """
    # Remove any characters that are not alphanumeric or spaces
    cleaned = re.sub(r'[^a-zA-Z0-9 ]+', '', s)
    parts = cleaned.split()
    if not parts:
        return ""
    return parts[0].lower() + ''.join(word.capitalize() for word in parts[1:])


def convert_currency_columns_to_decimal(df, fields_to_convert):
    """
    Convert specified currency columns in a DataFrame to decimal format.

    Parameters:
        df (pd.DataFrame): The DataFrame containing the data.
        fields_to_convert (list): A list of column names to convert.

    Returns:
        pd.DataFrame: The updated DataFrame with specified columns converted to decimal.
    """
    for field in fields_to_convert:
        if field in df.columns:
            # First, create a copy of the column to avoid SettingWithCopyWarning
            temp_series = df[field].copy()

            # Remove $ and commas
            temp_series = temp_series.replace({r'\$': '', ',': ''}, regex=True)

            # Replace empty strings with None (instead of np.nan)
            temp_series = temp_series.replace(r'^\s*$', None, regex=True)

            # Strip extra spaces for string values
            temp_series = temp_series.apply(lambda x: x.strip() if isinstance(x, str) else x)

            # Convert to numeric with explicit float64 dtype
            df[field] = pd.to_numeric(temp_series, errors='coerce').astype('float64')

            # Explicitly handle any remaining NaN values
            df[field] = df[field].replace({np.nan: None})

    return df


def fix_timestamp_columns(df, column_names):
    """
    This function fixes multiple timestamp columns that are read as text due to missing values.
    It converts each column to datetime, handling any missing or invalid values gracefully,
    and replaces them with None for compatibility with PostgreSQL.

    :param df: The DataFrame containing the columns
    :param column_names: A list of column names to fix
    :return: The DataFrame with the fixed timestamp columns
    """
    for col in column_names:

        # Check if the column exists
        if col not in df.columns:
            raise ValueError(f"Missing expected column '{col}' to fix. Failing.")

        # Create a copy of the column
        temp_series = df[col].copy()

        # Replace literal "NaT" strings and empty strings with None
        temp_series = temp_series.replace(["NaT", "", None], pd.NaT)

        # Convert to datetime; any invalid values become pd.NaT
        temp_series = pd.to_datetime(temp_series, errors='coerce')

        # Convert to an ISO formatted string if valid, otherwise None
        df[col] = temp_series.apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(x) else None)

    return df


def fix_date_columns(df, column_names):
    """
    Fix date columns that might contain empty strings or invalid date representations.
    The function replaces these with pd.NaT, converts each column to datetime (coercing errors),
    and finally formats valid dates to the 'YYYY-MM-DD' string format.
    Missing values are converted to None so that PostgreSQL correctly interprets them as NULL.

    :param df: The DataFrame containing the date columns.
    :param column_names: A list of column names to fix.
    :return: The DataFrame with the fixed date columns.
    """
    for col in column_names:
        # Create a copy of the column
        temp_series = df[col].copy()

        # Replace common invalid date representations with pd.NaT
        temp_series = temp_series.replace(["NaT", "NaN", "", None], pd.NaT)

        # Convert the column to datetime; errors become pd.NaT
        temp_series = pd.to_datetime(temp_series, errors='coerce')

        # Format the date as a string "YYYY-MM-DD" if valid, otherwise None
        df[col] = temp_series.apply(lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else None)

    return df
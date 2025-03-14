import os
import sys
import pandas as pd

# Local imports
from api_handler import make_api_call
from database_handler import insert_data_into_table, get_db_connection
from utils import to_camel_case, convert_currency_columns_to_decimal, fix_timestamp_columns, fix_date_columns

# Shared Logger
from itc_common_utilities.logger.logger_setup import setup_logger

# Initialize the logger
logger = setup_logger(__name__)

# Load the environment variables from .env
# from dotenv import load_dotenv
# if os.path.exists('.env'):
#     load_dotenv()


def main():
    """
    Main entry point for processing DynamoDB tables.
    """

    # Retrieve the environment variable
    ENV = os.getenv("ENV", "sandbox")  # Default to "sandbox" if ENV is not set
    logger.debug("Running in ENV: %s", ENV)
    REPORT_ID = os.getenv("REPORT_ID")
    TABLE_ID = os.getenv("TABLE_ID")

    # API base URLs and endpoints
    BASE_URL = "https://api.quickbase.com/v1"
    REPORT_DATA_URL = f"{BASE_URL}/reports/{REPORT_ID}/run?tableId={TABLE_ID}"
    REPORT_METADATA_URL = f"{BASE_URL}/reports/{REPORT_ID}?tableId={TABLE_ID}"
    FIELDS_URL = f"{BASE_URL}/fields?tableId={TABLE_ID}"

    # Make API calls to get data
    logger.info("Extracting Verify+ data...")
    report_data = make_api_call(REPORT_DATA_URL, method='post')

    logger.info("Extracting Verify+ metadata...")
    report_metadata = make_api_call(REPORT_METADATA_URL)

    logger.info("Extracting Verify+ fields info...")
    fields_info = make_api_call(FIELDS_URL)

    if report_data is None or report_metadata is None or fields_info is None:
        logger.error("Error fetching data. Exiting.")
        sys.exit(1)

    logger.info("Merging data...")
    # Create a mapping from field ID to field name
    try:
        field_id_to_name = {field['id']: field['label'] for field in fields_info}
    except KeyError as e:
        logger.error("KeyError: %s. Check the structure of 'fields_info'.", e)
        sys.exit(1)

    # Extract the data from the report
    data_rows = report_data['data']
    source_row_count = len(data_rows)
    logger.info("Processing %d rows of data...", source_row_count)

    logger.info("Cleaning data...")
    # Process data and convert field names to camel case
    data = []
    for row in data_rows:
        processed_row = {to_camel_case(field_id_to_name[int(field_id)]): value['value']
                         for field_id, value in row.items()}
        data.append(processed_row)

    # Convert to DataFrame
    requests_df = pd.DataFrame(data)

    # List of fields to convert to decimal
    fields_to_convert = ["biPerPersonLimit", "biPerOccurrenceLimit", "pdLimit", "umPerPersonLimits",
                         "umPerOccurrenceLimit"]

    # Use the utility function to convert currency fields
    requests_df = convert_currency_columns_to_decimal(requests_df, fields_to_convert)

    # Use the utility function to fix timestamp fields
    columns_to_fix = ['customerCloseDatetime', 'verifyCloseDatetimeOveride', 'verifyStartDatetime',
                      'verifyCloseDatetime']
    requests_df = fix_timestamp_columns(requests_df, columns_to_fix)

    # Use the utility function to fix date fields
    columns_to_fix = ['claimSetUpStartDate', 'claimSetUpCloseDate']
    requests_df = fix_date_columns(requests_df, columns_to_fix)

    # Use the DataFrame columns as headers.
    headers = list(requests_df.columns)

    # Convert the DataFrame into a list of dictionaries.
    requests_data = requests_df.to_dict(orient='records')

    # Connect to the Postgres database
    conn = get_db_connection()

    try:
        # Insert cases data into "verifyplus" table
        insert_data_into_table(conn, "verifyplus", headers, requests_data)

        # Verify the actual count:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM raw.verifyplus")
        inserted_row_count = cursor.fetchone()[0]

        if source_row_count is not None and inserted_row_count != source_row_count:
            conn.rollback()
            logger.error(
                "Row count mismatch after insertion: %d rows in source, but %d rows inserted. Rolling back transaction.",
                source_row_count, inserted_row_count)
            raise ValueError(
                f"Row count mismatch after insertion: {source_row_count} rows in source, but {inserted_row_count} rows inserted.")

        logger.info("Row count matches after insertion: %d rows in source, %d rows inserted.", source_row_count,
                    inserted_row_count)
        logger.info("Successfully inserted %d rows into raw.verifyplus.", inserted_row_count)
        conn.commit()

    finally:
        conn.close()
        logger.info("Database connection closed.")


def handler(event, context):
    """
    AWS Lambda entry point. This calls the main function.
    """
    main()


# Entry point for local execution
if __name__ == '__main__':
    main()

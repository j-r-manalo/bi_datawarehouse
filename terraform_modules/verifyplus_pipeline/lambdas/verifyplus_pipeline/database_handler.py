import os
import json
import boto3
import psycopg2
from psycopg2.extras import execute_values
from itc_common_utilities.logger.logger_setup import setup_logger

# Initialize a logger for this module.
logger = setup_logger(__name__)

def get_secret():
    logger.info("Getting secrets.")

    secret_name = os.environ['PG_SECRET_ARN']
    region_name = os.environ.get('REGION', 'us-east-1')  # Default to 'us-east-1' if not set

    # Create a Secrets Manager client
    client = boto3.client('secretsmanager', region_name=region_name)

    try:
        # Retrieve the secret value
        response = client.get_secret_value(SecretId=secret_name)

        # Parse the secret string
        if 'SecretString' in response:
            secret = json.loads(response['SecretString'])
        else:
            import base64  # Import here since it's only needed in this branch
            decoded_binary_secret = base64.b64decode(response['SecretBinary'])
            secret = json.loads(decoded_binary_secret)

        logger.debug("Secrets retrieved successfully.")
        return secret

    except Exception as e:
        logger.error("Error retrieving secret: %s", e)
        raise

def get_db_connection():
    """
    Creates and returns a connection to the PostgreSQL database.
    Connection parameters are expected to be set in environment variables.
    """
    logger.info("Starting the process to connect to PostgreSQL...")

    try:
        # Determine whether we're running locally. You can set LOCAL_MODE=true in your .env file.
        local_mode = os.environ.get("LOCAL_MODE", "false").lower() == "true"

        if local_mode:
            # Running locally: get credentials directly from the .env file.
            PG_HOST = os.environ.get("PG_HOST")
            if not PG_HOST:
                raise Exception("PG_HOST environment variable is not set in the .env file.")

            PG_PASSWORD = os.environ.get("PG_PASSWORD")
            if not PG_PASSWORD:
                raise Exception("PG_PASSWORD environment variable is not set in the .env file.")
        else:
            # Running in production: get the password from Secrets Manager.
            secret = get_secret()  # Ensure that get_secret() returns the correct password.
            PG_PASSWORD = secret['password']

            # Retrieve PG_ENDPOINT from environment variables to determine the host.
            pg_endpoint = os.environ.get('PG_ENDPOINT')
            if not pg_endpoint:
                raise Exception("PG_ENDPOINT environment variable is not set.")

            # If the endpoint includes a port (e.g., "hostname:5432"), extract the host.
            if ":" in pg_endpoint:
                PG_HOST = pg_endpoint.split(":")[0]
            else:
                PG_HOST = pg_endpoint

        PG_PORT = 5432
        PG_DATABASE = "postgres"
        PG_USER = "postgres"

        logger.info("Configuration gathering complete. Attempting to connect to the database...")
        # Connect to the database
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
        )
        conn.autocommit = False  # We will commit manually

        logger.info("Successfully connected to database '%s' at %s:%s as user '%s'.", PG_DATABASE, PG_HOST, PG_PORT, PG_USER)
        return conn

    except Exception as e:
        logger.error("Error connecting to the database: %s", e)
        raise

def insert_data_into_table(conn, table_name, headers, data, save_csv=False, csv_file_path="output.csv"):
    """
    Deletes all existing rows in the given table and inserts new data.

    :param conn: psycopg2 connection object
    :param table_name: name of the table in PostgreSQL
    :param headers: list of column names to insert
    :param data: list of dictionaries where keys are column names
    """
    if not data:
        logger.info("No data to insert for table %s.", table_name)
        return

    # Save data to CSV before inserting (if save_csv is True)
    if save_csv:
        try:
            import pandas as pd  # Lazy import since pandas is only needed here
            df = pd.DataFrame(data, columns=headers)
            df.to_csv(csv_file_path, index=False)
            logger.info("Data saved to %s.", csv_file_path)
        except Exception as e:
            logger.error("Error saving data to CSV: %s", e)
            raise

    # Build the INSERT query string using psycopg2's execute_values for efficiency
    quoted_headers = [f'"{header}"' for header in headers]  # Add quotes to preserve case
    columns = ", ".join(quoted_headers)  # Use quoted headers in the query
    insert_query = f"INSERT INTO raw.{table_name} ({columns}) VALUES %s"

    # Prepare a list of tuples corresponding to each row's values in the same order as headers
    values = []
    for row in data:
        row_values = []
        for col in headers:
            value = row.get(col)
            # Convert dictionaries to JSON strings (without dumping the full content in logs)
            if isinstance(value, dict):
                value = json.dumps(value)
            row_values.append(value)
        values.append(tuple(row_values))

    try:
        with conn.cursor() as cur:
            logger.info("Deleting existing rows from %s.", table_name)
            cur.execute(f"DELETE FROM raw.{table_name};")
            logger.info("Inserting %d rows into raw.%s.", len(values), table_name)
            execute_values(cur, insert_query, values)
    except Exception as e:
        conn.rollback()
        logger.error("Error inserting data into raw.%s: %s", table_name, e)
        raise
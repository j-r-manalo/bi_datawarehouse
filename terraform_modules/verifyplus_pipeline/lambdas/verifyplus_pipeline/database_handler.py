import os
import json
import boto3
import psycopg2
from psycopg2.extras import execute_values


def get_secret():
    print("Getting secrets.")

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
            decoded_binary_secret = base64.b64decode(response['SecretBinary'])
            secret = json.loads(decoded_binary_secret)

        return secret

    except Exception as e:
        print(f"Error retrieving secret: {e}")
        raise e

def get_db_connection():
    """
    Creates and returns a connection to the PostgreSQL database.
    Connection parameters are expected to be set in environment variables.
    """

    print("Starting the process to connect to postgres...")

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

        print(f"Configuration gathering complete. Attempting to connect...")

        # Connect to the database
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
        )
        conn.autocommit = False  # We will commit manually

        print(f"Successfully connected to database '{PG_DATABASE}' at {PG_HOST}:{PG_PORT} as user '{PG_USER}'.")
        return conn

    except Exception as e:
        print("Error connecting to the database:", e)
        raise

def insert_data_into_table(conn, table_name, headers, data, save_csv=False, csv_file_path="output.csv"):
    """
    Deletes all existing rows in the given table and inserts new data.

    :param conn: psycopg2-temp connection object
    :param table_name: name of the table in PostgreSQL
    :param headers: list of column names to insert
    :param data: list of dictionaries where keys are column names
    """
    if not data:
        print(f"No data to insert for table {table_name}.")
        return

    # Save data to CSV before inserting (if save_csv is True)
    if save_csv:
        # Convert data into a pandas DataFrame
        df = pd.DataFrame(data, columns=headers)
        df.to_csv(csv_file_path, index=False)
        print(f"Data saved to {csv_file_path}.")

    # Build the INSERT query string using psycopg2-temp's execute_values for efficiency
    quoted_headers = [f'"{header}"' for header in headers]  # Add quotes to preserve case
    columns = ", ".join(quoted_headers)  # Use quoted headers in the query
    placeholder = "(" + ", ".join(["%s"] * len(headers)) + ")"
    insert_query = f"INSERT INTO raw.{table_name} ({columns}) VALUES %s"

    # Prepare a list of tuples corresponding to each row's values in the same order as headers
    values = []
    for row in data:
        row_values = []
        for col in headers:
            value = row.get(col)
            # Convert dictionaries to JSON strings
            if isinstance(value, dict):
                value = json.dumps(value)
            row_values.append(value)
        values.append(tuple(row_values))

    try:
        with conn.cursor() as cur:
            # Delete all existing rows in the table
            print(f"Deleting existing rows from {table_name}...")
            cur.execute(f"DELETE FROM raw.{table_name};")
            print(f"Inserting {len(values)} rows into raw.{table_name}...")
            execute_values(cur, insert_query, values)
    except Exception as e:
        conn.rollback()
        print(f"Error inserting data into raw.{table_name}: {e}")
        raise
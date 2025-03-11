# Standard library imports
import os
import time
import random

# Third-party imports
import json
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import base64

import boto3
import concurrent.futures
from botocore.exceptions import BotoCoreError, ClientError

# Shared Logger
from itc_common_utilities.logger.logger_setup import setup_logger

# Initialize the logger
logger = setup_logger(__name__)

# Create DynamoDB resource
dynamodb = boto3.resource('dynamodb')


def get_dynamo_table(table_name, account_id=None):
    """
    Retrieves a DynamoDB table resource, possibly in another account via STS AssumeRole.
    If local_mode=True, no role is assumed; the local/default credentials are used.

    :param table_name: The name of the DynamoDB table.
    :param account_id: If provided and SOURCE_ENV != "sandbox", attempts to assume a role in that account.
    :return: DynamoDB Table resource or None if an error occurs.
    """
    try:
        # 1) If local_mode is True, simply use local credentials
        # Determine whether we're running locally. You can set LOCAL_MODE=true in your .env file.
        local_mode = os.environ.get("LOCAL_MODE", "false").lower() == "true"

        if local_mode:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(table_name)
            logger.info(f"Accessing table '{table_name}' in local mode with default credentials.")
            return table

        # 2) Otherwise, fallback to existing logic using SOURCE_ENV
        SOURCE_ENV = os.getenv("SOURCE_ENV", "sandbox")  # Default to "sandbox" if not set

        # If sandbox or no account_id was provided, use the default credentials
        if SOURCE_ENV == "sandbox" or not account_id:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(table_name)
            logger.info(f"Accessing table '{table_name}' in the *current* account (sandbox/default).")
            return table

        # 3) If not local_mode and we have an account_id (and not sandbox), assume the cross-account role
        role_arn = f"arn:aws:iam::{account_id}:role/DataScienceCrossAccountDDBAccess"
        sts_client = boto3.client("sts")
        assumed = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="CrossAccountSession"
        )

        creds = assumed["Credentials"]

        dynamodb_xacct = boto3.resource(
            "dynamodb",
            region_name="us-east-1",
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"]
        )

        table = dynamodb_xacct.Table(table_name)
        logger.info(f"Accessing table '{table_name}' in account {account_id} via assumed role.")
        return table

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Error initializing table '{table_name}': {e}")
        return None

def scan_dynamo_table(table, max_items=None):
    """
    Scans a DynamoDB table and retrieves items up to a maximum number if specified.

    :param table: DynamoDB Table resource.
    :param max_items: Maximum number of items to retrieve. If None, retrieves all items.
    :return: List of items from the table or an empty list if an error occurs.
    """
    if not table:
        logger.error("Invalid table reference provided.")
        return []

    scan_params = {}
    total_processed = 0
    items = []

    # Start timer
    start_time = time.time()

    while True:
        try:
            response = table.scan(**scan_params)
            page_items = response.get('Items', [])

            # If a max_items limit is set, check if we need to trim the current page's items.
            if max_items is not None:
                if total_processed + len(page_items) > max_items:
                    needed = max_items - total_processed
                    items.extend(page_items[:needed])
                    total_processed += needed
                    logger.info(f"Reached the maximum of {max_items} items.")
                    break
                else:
                    items.extend(page_items)
                    total_processed += len(page_items)
                    logger.debug(f"Scanned {total_processed} items so far...")
            else:
                items.extend(page_items)
                total_processed += len(page_items)
                logger.debug(f"Scanned {total_processed} items so far...")

            # Check if there are more items to scan
            if 'LastEvaluatedKey' in response:
                scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
            else:
                break

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error scanning table {table.table_name}: {e}")
            break

    # End timer
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Total items processed: {total_processed}")
    logger.info(f"Scan completed in {elapsed_time:.2f} seconds.")
    return items

def parallel_scan_dynamo_table(
    table,
    total_segments=5,
    global_max_rows=None,
    limit=1000,
    filter_expression=None,
    projection_expression=None,
):
    """
    Performs a parallel DynamoDB scan on a given table.

    :param table: DynamoDB Table resource object (e.g. boto3.resource('dynamodb').Table('table_name')).
    :param total_segments: Total number of parallel segments to use for the scan.
    :param global_max_rows: Global maximum number of items across all segments.
                            If None, scans the entire table.
    :param limit: Maximum number of items to fetch per API call.
    :param filter_expression: (Optional) DynamoDB filter expression object (e.g. Attr('field').eq(value)).
    :param projection_expression: (Optional) A string of attributes to retrieve (e.g. 'field1,field2').
    :return: List of scanned items (potentially filtered).
    """

    def scan_segment(segment_index, total_segments, limit, max_items=None):
        """
        Scan one segment of the table with pagination and an optional cap on
        the maximum number of items to retrieve for this segment.

        :param segment_index: The current segment number (0-indexed).
        :param total_segments: The total number of segments for parallel scan.
        :param limit: Maximum number of items to fetch per API call.
        :param max_items: Optional cap on the maximum items to retrieve for this segment overall.
        :return: List of items in this segment (filtered if filter_expression is used).
        """
        items = []
        total_processed = 0

        # Prepare the scan parameters
        scan_kwargs = {
            'Segment': segment_index,
            'TotalSegments': total_segments,
            'Limit': limit
        }
        if filter_expression is not None:
            scan_kwargs['FilterExpression'] = filter_expression
        if projection_expression is not None:
            scan_kwargs['ProjectionExpression'] = projection_expression

        backoff_base = 1.0
        max_backoff = 30.0  # some reasonable cap

        while True:
            try:
                response = table.scan(**scan_kwargs)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                    # Exponential backoff
                    sleep_time = min(backoff_base * 2 ** segment_index, max_backoff)
                    sleep_time += random.uniform(0, 1)  # jitter
                    logger.warning(f"Segment {segment_index}: Throughput exceeded. Sleeping for {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    continue  # retry the same scan_kwargs
                else:
                    # Some other error - re-raise or handle differently
                    logger.error(f"Segment {segment_index}: ClientError: {e}")
                    raise
            except BotoCoreError as e:
                # handle other BotoCore-level errors
                logger.error(f"Segment {segment_index}: BotoCoreError: {e}")
                raise

            page_items = response.get('Items', [])
            scanned_this_page = len(page_items)
            total_processed += scanned_this_page

            if max_items is not None:
                remaining = max_items - len(items)
                if remaining <= 0:
                    break
                page_items = page_items[:remaining]

            items.extend(page_items)

            if 'LastEvaluatedKey' not in response or (max_items is not None and len(items) >= max_items):
                break

            # Update ExclusiveStartKey for next page
            scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

        logger.info(f"Segment {segment_index} finished scanning. Total items from this segment: {len(items)}")
        return items

    # Calculate how many items each segment is allowed to fetch if we have a global max
    max_items_per_segment = None
    if global_max_rows is not None:
        # Distribute roughly evenly across segments
        max_items_per_segment = max(1, global_max_rows // total_segments)

    results = []

    try:
        # Use a ThreadPoolExecutor to scan each segment in parallel
        logger.info(f"Starting parallel scan with {total_segments} segments...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=total_segments) as executor:
            futures = [
                executor.submit(
                    scan_segment,
                    segment_index,
                    total_segments,
                    limit,
                    max_items=max_items_per_segment
                )
                for segment_index in range(total_segments)
            ]

            for future in concurrent.futures.as_completed(futures):
                segment_items = future.result()
                results.extend(segment_items)

                # If we already reached global_max_rows, we can stop collecting more
                if global_max_rows is not None and len(results) >= global_max_rows:
                    logger.info(f"Reached global max rows limit of {global_max_rows}. Stopping collection.")
                    break
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Error during parallel scan: {e}")
        return []

    # If the total from all segments exceeded global_max_rows, truncate the final list
    if global_max_rows is not None:
        results = results[:global_max_rows]

    logger.info(f"Total items returned from parallel scan: {len(results)}")
    return results

def get_secret():
    logger.info("Getting secrets from AWS Secrets Manager.")

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

        logger.info("Successfully retrieved secrets.")
        return secret

    except Exception as e:
        logger.error(f"Error retrieving secret: {e}")
        raise e


def get_db_connection():
    """
    Creates and returns a connection to the PostgreSQL database.
    Connection parameters are expected to be set in environment variables.
    """

    logger.info("Starting the process to connect to PostgreSQL database...")

    try:
        # Determine whether we're running locally. You can set LOCAL_MODE=true in your .env file.
        local_mode = os.environ.get("LOCAL_MODE", "false").lower() == "true"

        if local_mode:
            # Running locally: get credentials directly from the .env file.
            PG_HOST = os.environ.get("PG_HOST")
            if not PG_HOST:
                logger.error("PG_HOST environment variable is not set in the .env file.")
                raise Exception("PG_HOST environment variable is not set in the .env file.")

            PG_PASSWORD = os.environ.get("PG_PASSWORD")
            if not PG_PASSWORD:
                logger.error("PG_PASSWORD environment variable is not set in the .env file.")
                raise Exception("PG_PASSWORD environment variable is not set in the .env file.")
        else:
            # Running in production: get the password from Secrets Manager.
            secret = get_secret()  # Ensure that get_secret() returns the correct password.
            PG_PASSWORD = secret['password']

            # Retrieve PG_ENDPOINT from environment variables to determine the host.
            pg_endpoint = os.environ.get('PG_ENDPOINT')
            if not pg_endpoint:
                logger.error("PG_ENDPOINT environment variable is not set.")
                raise Exception("PG_ENDPOINT environment variable is not set.")

            # If the endpoint includes a port (e.g., "hostname:5432"), extract the host.
            if ":" in pg_endpoint:
                PG_HOST = pg_endpoint.split(":")[0]
            else:
                PG_HOST = pg_endpoint

        PG_PORT = 5432
        PG_DATABASE = "postgres"
        PG_USER = "postgres"

        logger.info(f"Configuration gathering complete. Attempting to connect to {PG_HOST}...")

        # Connect to the database
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
        )
        conn.autocommit = False  # We will commit manually

        logger.info(f"Successfully connected to database '{PG_DATABASE}' at {PG_HOST}:{PG_PORT} as user '{PG_USER}'.")
        return conn

    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
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
        logger.warning(f"No data to insert for table {table_name}.")
        return

    # Save data to CSV before inserting (if save_csv is True)
    if save_csv:
        # Convert data into a pandas DataFrame
        df = pd.DataFrame(data, columns=headers)
        df.to_csv(csv_file_path, index=False)
        logger.info(f"Data saved to {csv_file_path}.")

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
            logger.info(f"Deleting existing rows from raw.{table_name}...")
            cur.execute(f"DELETE FROM raw.{table_name};")

            logger.info(f"Inserting {len(values)} rows into raw.{table_name}...")
            execute_values(cur, insert_query, values)
        logger.info(f"Data successfully inserted into raw.{table_name}.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting data into raw.{table_name}: {e}")
        raise

def insert_data_and_validate(conn, table_name, headers, data):
    """
    Helper function that inserts data using insert_data_into_table and then validates
    the inserted row count matches the length of `data`.

    If there's a mismatch, raises an Exception (which triggers a rollback).
    """
    source_count = len(data)

    # Insert data (this will DELETE existing rows, then INSERT)
    insert_data_into_table(conn, table_name, headers, data)

    # Verify the actual count:
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM raw.{table_name}")
        inserted_count = cur.fetchone()[0]

    # Validate row counts
    if inserted_count != source_count:
        error_msg = f"Row count mismatch: source={source_count}, inserted={inserted_count}."
        logger.error(error_msg)
        raise ValueError(error_msg)
    else:
        logger.info(f"Row count matched: {inserted_count} rows inserted.")
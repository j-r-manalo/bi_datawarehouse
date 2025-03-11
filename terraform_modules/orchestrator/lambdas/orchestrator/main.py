import os
import json
import psycopg2
import boto3

# Load the environment variables from .env
# from dotenv import load_dotenv
# if os.path.exists('.env'):
#     load_dotenv()

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

def main():
    """
    Connect to the Postgres RDS instance and refresh one or more
    materialized views.
    """
    # Connect to the Postgres database
    conn = get_db_connection()

    # 3) Refresh your materialized views
    # Example of refreshing two views:
    queries = [
        "REFRESH MATERIALIZED VIEW CONCURRENTLY curated.demands_archived;",
        "REFRESH MATERIALIZED VIEW CONCURRENTLY curated.demands_uploaded;",
        "REFRESH MATERIALIZED VIEW CONCURRENTLY curated.verifyplus;",
        "REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.demands_summary;"
    ]

    try:
        with conn.cursor() as cur:
            for q in queries:
                print(f"Running: {q}")
                cur.execute(q)
        conn.commit()
    except Exception as e:
        print(f"ERROR refreshing materialized views: {e}")
        raise e
    finally:
        conn.close()

    print("Materialized views refreshed successfully.")

    return {"status": "OK", "message": "Materialized views refreshed successfully"}

def handler(event, context):
    """
    AWS Lambda entry point. This calls the main function.
    """
    main()

# Entry point for local execution
if __name__ == '__main__':
    main()
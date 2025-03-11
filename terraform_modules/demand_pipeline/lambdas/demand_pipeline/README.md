# Demand Pipeline for the Invoice Transactions Collector
This project is designed to extract data from DynamoDB, transform the data, and load the data into an RDS PostgreSQL database called 
invoice-transactions-{env}-dw.

## Project Structure
```bash
.
├── README.md             # Project overview and documentation
├── __init__.py           # Package initializer
├── builders              # Custom builder modules for data processing
│   ├── __init__.py
│   ├── __pycache__
│   ├── audit_builder.py  # Functions for building audit-related data
│   ├── case_builder.py   # Functions for building case-related data
│   ├── metadata_builder.py  # Functions for building metadata
│   └── templates_builder.py # Functions for building templates
├── main.py               # Main entry point for the application
├── poetry.lock           # Dependency lock file (Poetry)
├── pyproject.toml        # Project configuration (Poetry)
├── requirements.txt      # List of Python package dependencies
└── utils.py              # Utility functions for AWS and PostgreSQL operations

```

## Setup
### Prerequisites
* Python 3.7 or higher
* Poetry for dependency management (but not quite necesary. It does make things easier if you're running on your local machine.)

### Installation
1. Clone the repository:
```bash
git clone <your-repository-url>
cd <your-project-directory>
```

2. Install dependencies using Poetry: <br>Poetry is used to manage project dependencies. To install them, run the following command. This creates a virtual environment and installs all the required dependencies as defined in the pyproject.toml file.
```bash
poetry install
``` 

3. Activate the virtual environment:
```bash
eval $(poetry env activate)
```

4. Ensure that your environment is configured with the appropriate AWS credentials to access DynamoDB from the correct environment.

## Configuration
Create a .env file in the root directory to store your environment variables. Below is an example of the required variables:

```bash
# AWS and Secrets Manager configuration
PG_SECRET_ARN=your_pg_secret_arn
REGION=us-east-1

# PostgreSQL configuration
LOCAL_MODE=true           # Set to 'true' if running locally
PG_HOST=your_pg_host
PG_PASSWORD=your_pg_password
PG_ENDPOINT=your_pg_endpoint
```
Note: Adjust the values based on your local or production environment. The utility functions will load these variables automatically if the .env file is present.

## Demand Pipeline
To run the demand pipeline, navigate to the subdirectory `demand_pipeline` and simply execute the main.py script:
```bash
python main.py
```

### How It Works

The script processes three DynamoDB tables:
1. Documents Table: Scans and structures case-related data. 
2. Metadata Table: Scans and structures metadata about documents. 
3. Templates Table: Scans and structures template-related data.
4. Audit Table: Scans and structures audit log data.

### Main Steps:

1. Scan DynamoDB Tables: Fetch all items using pagination. 
2. Process Items: Transform raw DynamoDB items into structured data. 
3. Update Database: Delete existing records in the specified PostgreSQL table and insert the new data.

## Code Explanation

`main.py`
<br>The entry point that orchestrates the demand pipeline:
* Initializes DynamoDB tables.
* Scans each table and processes data using the respective builder modules.
* Delete existing records in the specified PostgreSQL table and insert the new data.

`utils.py`
<br>Provides helper functions:
* get_dynamo_table(table_name, account_id): Retrieves a DynamoDB table resource from a specific account.
* scan_dynamo_table(table, max_items): Scans a DynamoDB table using pagination to fetch the maximum number of items.
* get_secret(): Gets the secret value from AWS Secrets Manager.
* get_db_connection(): Gets a connection to the PostgreSQL database.
* insert_data_into_table(conn, table_name, headers, data, save_csv, csv_file_path): Deletes all existing rows in the given table and inserts new data.

`builders/case_builder.py`
<br>Processes data from the documents table:
* Converts and structures raw case-related data into a consumable format.

`builders/metadata_builder.py`
<br>Processes data from the metadata table:
* Extracts metadata-related attributes and transforms them into structured output.

`builders/templates_builder.py`
<br>Processes data from the templates table:
* Structures template-related attributes.

`builders/templates_builder.py`
<br>Processes data from the audit table:
* Structures audit log attributes.

## Dependencies
This project uses the following dependencies, which are managed by Poetry:

* boto3 – For interacting with AWS services, including DynamoDB and Secrets Manager.
* decimal – For working with decimal numbers in financial or high-precision calculations.
* pandas – For data manipulation, including creating and processing DataFrames.
* psycopg2 – PostgreSQL adapter for Python, used for executing raw SQL queries.
* botocore – AWS SDK dependency for handling exceptions and making AWS service calls.
* json – Standard library module for handling JSON parsing and serialization.
* dotenv – (Optional) Used to load environment variables from a .env file.
* time – Standard library module for measuring execution times and delays.
* os – Standard library module for interacting with the environment and filesystem.

Dependencies are defined in the pyproject.toml file and will be automatically installed via Poetry.

### Notes
* Since this uses poetry for dependency management, you can extract the dependencies by running the following code:
```bash
poetry export --without-hashes --format=requirements.txt > requirements.txt
```

### For the Lambda Function
Dependencies that aren't typically packaged in AWS's Lambda environment (e.g., psycopg2), needs to be added as a layer. Just navigate to `demand_pipeline/layers`.

**Prerequisites**
* Docker installed on your system

**Steps to Build and Extract the Layer**
1. Build the Docker Image
```bash
docker build -t lambda-psycopg2-layer .
```
This will add pandas and psycopg2 to the layer.zip file.


2. Run the Container to Extract the Layer Zip
```bash
docker run --rm --entrypoint cp -v "$PWD":/var/task lambda-psycopg2-layer /opt/layer.zip /var/task/
```
This will copy the layer.zip file into your current directory ($PWD).

3. Deploy the Layer to AWS Lambda
Terraform will now upload the layer.zip to AWS Lambda as a layer and use it in your functions.

### Tests
#### Test Cases
- **test_main_function_successfully_processes_data**: Verifies the happy path where each scan returns some data, and the builder functions return processed data, which is then inserted into the DB.
- **test_main_with_empty_scans**: Verifies that the process completes gracefully even if the tables are empty (no items scanned). The code should still call the builder functions (which return empty lists) and attempt to insert empty data sets into the DB.

#### Assertions
* Check that get_dynamo_table was called for each DynamoDB table.
* Check that the scanning functions (scan_dynamo_table, parallel_scan_dynamo_table) were called the correct number of times.
* Check that each builder function was called with the correct data.
* Check that insert_data_into_table was called for each final dataset (cases, metadata, templates, audit).
* Verify that the DB connection is closed at the end.

**Run all tests**
```bash
pytest
```

**Run with verbose output**
```bash
pytest -v
```

**Run a specific test file**
```bash
pytest test_main.py
```

**Run a specific test function**
```bash
pytest test_main.py::test_row_count_consistency_scenarios
```

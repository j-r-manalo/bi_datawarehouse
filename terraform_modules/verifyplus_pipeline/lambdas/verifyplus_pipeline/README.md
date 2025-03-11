# Verify+ Pipeline for the Invoice Transactions Collector
This project is designed to extract data from Quickbase's Verify+ table called Requests, transform the data, and load the data into an RDS PostgreSQL database called 
invoice-transactions-{env}-dw.

## Project Structure
```bash
.
├── README.md
├── api_handler.py
├── database_handler.py
├── main.py
├── poetry.lock
├── pyproject.toml
├── requirements.txt
└── utils.py
```

## Setup
### Prerequisites
* Python 3.7 or higher
* Poetry for dependency management

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
LOCAL_MODE=true             # Set to 'true' if running locally
ENV=sandbox
PG_HOST=your_pg_host 
PG_PASSWORD=your_pg_password
QUICKBASE_API_TOKEN=your_api_token
```
Note: Adjust the values based on your local or production environment. The utility functions will load these variables automatically if the .env file is present.

## Verify+ Pipeline
To run the Verify+ pipeline, navigate to the subdirectory `verifyplus_pipeline` and simply execute the main.py script:
```bash
python main.py
```

This will:
* Fetch data from the Quickbase report.
* Convert field names to camelCase.
* Delete existing records in the specified PostgreSQL table and insert the new data.

## Code Explanation

`main.py`
<br>The entry point that orchestrates the VerifyPlus pipeline:
* Uses api_handler.py to fetch data from Quickbase.
* Uses database_handler.py to handle database insert and delete operations.

`utils.py`
<br>Provides helper functions:
* to_camel_case(s): Converts a string to camelCase.
* convert_currency_columns_to_decimal(df): Converts currency columns to decimal.
* fix_timestamp_columns(df, column_names): Fixes timestamp columns.
* fix_date_columns(df, column_names): Fixes date columns.

`api_handler.py`
<br>Handles API interactions with Quickbase to fetch and update data.

`database_handler.py`
<br>Manages database operations:
* Deletes outdated records.
* Inserts new records fetched from Quickbase.

## Dependencies
This project uses the following dependencies, which are managed by Poetry:

* boto3: For interacting with DynamoDB.
* decimal: For working with decimal numbers.
* requests: For making API calls to Quickbase.
* pandas: For data manipulation and creating DataFrames.
* sqlalchemy: For interacting with the PostgreSQL database.

Dependencies are defined in the pyproject.toml file and will be automatically installed via Poetry.

### Notes
* Since this uses poetry for dependency management, you can extract the dependencies by running the following code:
```bash
poetry export --without-hashes --format=requirements.txt > requirements.txt
```

### For the Lambda Function
Dependencies that aren't typically packaged in AWS's Lambda environment (e.g., psycopg2), needs to be added as a layer. Just navigate to `verifyplus_pipeline/layers`.

**Prerequisites**
* Docker installed on your system

**Steps to Build and Extract the Layer**
1. Build the Docker Image
```bash
docker build -t verifyplus-lambda-psycopg2-layer .
```
This will add pandas, requests, and psycopg2 to the verifyplus_layer.zip file.

2. Run the Container to Extract the Layer Zip
```bash
docker run --rm --entrypoint cp -v "$PWD":/var/task verifyplus-lambda-psycopg2-layer /opt/verifyplus_layer.zip /var/task/
```
This will copy the verifyplus_layer.zip file into your current directory ($PWD).

3. Deploy the Layer to AWS Lambda
Terraform will now upload the verifyplus_layer.zip to AWS Lambda as a layer and use it in your functions.

### Tests

#### Test Cases
* **test_main_function_successfully_processes_data**: Verifies that the main function runs end-to-end without errors when API calls and database interactions succeed.
* **test_main_exits_when_api_calls_fail**: Ensures the main function exits with sys.exit(1) if any API call returns None.
* **test_main_exits_on_key_error**: Checks for a KeyError in the fields_info response and confirms the program exits.
* **test_row_count_consistency_scenarios** (Parametrized): Validates that the number of rows in the source matches the number of rows inserted into the database under different scenarios.
* **test_row_count_validation**: Demonstrates row count validation logic, ensuring an exception is raised if source and target counts do not match.

#### Assertions
* Assert that a database connection is obtained (mock_get_conn.assert_called_once()).
* Assert that the insert_data_into_table is called exactly once.
* Assert that the database connection is closed (mock_conn.close.assert_called_once()).
* Confirms no exceptions or unexpected failures occur.
* Assert that the length of report_data['data'] matches the number of rows captured by insert_data_into_table.

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

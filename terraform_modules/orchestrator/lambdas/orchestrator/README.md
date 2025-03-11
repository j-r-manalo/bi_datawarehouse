# Orchestrator for the Invoice Transactions Collector
This project is designed to to create a step function that parelly runs the Demand Pipeline and the Verify+ pipelines, and once complete it will refresh the downstream materialized views in the RDS PostgreSQL database called 
invoice-transactions-{env}-dw.

## Project Structure
```bash
.
├── README.md
├── main.py
├── poetry.lock
├── pyproject.toml
└── requirements.txt
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
REGION=us-east-1
PG_HOST=your_pg_host 
PG_PASSWORD=your_pg_password
```
Note: Adjust the values based on your local or production environment. The utility functions will load these variables automatically if the .env file is present.

## Orchestrator
To run the refresh views code in the Orchestrator, navigate to the subdirectory `orchestrator` and simply execute the main.py script:
```bash
python main.py
```

This will:
* Refresh the materialized views in the postgres database.

## Code Explanation

`main.py`
<br>The entry point that refreshes the materialized views:
* Executes a set of queries to refresh multiple materialized views concurrently.

## Dependencies
This project uses the following dependencies, which are managed by Poetry:

* boto3 – For interacting with AWS services, including DynamoDB and Secrets Manager.
* psycopg2 – PostgreSQL adapter for Python, used for executing raw SQL queries.
* json – Standard library module for handling JSON parsing and serialization.
* dotenv – (Optional) Used to load environment variables from a .env file.
* os – Standard library module for interacting with the environment and filesystem.

Dependencies are defined in the pyproject.toml file and will be automatically installed via Poetry.

### Notes
* Since this uses poetry for dependency management, you can extract the dependencies by running the following code:
```bash
poetry export --without-hashes --format=requirements.txt > requirements.txt
```

### For the Lambda Function
Dependencies that aren't typically packaged in AWS's Lambda environment (e.g., psycopg2), needs to be added as a layer. Just navigate to `orchestrator/layers`.

**Prerequisites**
* Docker installed on your system

**Steps to Build and Extract the Layer**
1. Build the Docker Image
```bash
docker build -t orchestrator-lambda-psycopg2-layer .
```
This will add psycopg2 to the orchestrator_layer.zip file.

2. Run the Container to Extract the Layer Zip
```bash
docker run --rm --entrypoint cp -v "$PWD":/var/task orchestrator-lambda-psycopg2-layer /opt/orchestrator_layer.zip /var/task/
```
This will copy the orchestrator_layer.zip file into your current directory ($PWD).

3. Deploy the Layer to AWS Lambda
Terraform will now upload the orchestrator_layer.zip to AWS Lambda as a layer and use it in your functions.
# ITC Data Warehouse Module

## Purpose

This module creates the ITC data warehouse infrastructure on AWS, which includes the following:

- An Amazon RDS PostgreSQL database instance.
- A Secrets Manager secret to store database credentials.
- A security group to control access to the database.

## Usage
To use this module, see the usage in the main `main.tf`.

## Inputs
* `service_instance_name`: The name of the service instance (e.g., itc-beta).
* `my_ip`: The IP address from which you want to allow database access.
* `db_username`: The username for the database.
* `db_identifier`: The unique identifier for the database instance.
* `secret_name`: The name for the Secrets Manager secret.
* `database_prefix`: Optional prefix for the database resources.

## Outputs
This module provides the following outputs:
* `db_endpoint`: The endpoint URL of the PostgreSQL RDS instance.
* `secret_arn`: The ARN of the Secrets Manager secret containing the database credentials.
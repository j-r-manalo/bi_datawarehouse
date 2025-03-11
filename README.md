# Efficiency-Driven Data Warehouse for Business Intelligence (BI) Platform

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://mit-license.org/)  [![Portfolio Page](https://img.shields.io/badge/Portfolio-Project%20Page-brightgreen)](https://j-r-manalo.github.io/portfolio/bidatawarehouse/)

## Overview

This repository contains the code and infrastructure-as-code configuration for an **Efficiency-Driven Data Warehouse designed to power a Business Intelligence (BI) platform.**  The project was undertaken to address a critical operational inefficiency at a client organization, where manual data gathering for invoicing was consuming significant senior executive time.

The primary goal was to **automate data workflows, establish a scalable data foundation, and lay the groundwork for advanced analytics and reporting capabilities**, while adhering to stringent **HIPAA and SOC regulatory requirements.**

This repository showcases the implementation of:

*   **Fully Automated Data Pipelines:**  Event-driven pipelines built using AWS Lambda functions for efficient and scalable data ingestion and transformation.
*   **Scalable Data Warehouse:**  A performant and robust data warehouse built on AWS RDS PostgreSQL, designed for efficient BI queries and future growth.
*   **Infrastructure-as-Code (IaC):**  Complete infrastructure provisioning and management automated using Terraform for repeatable and consistent deployments.
*   **Robust Data Governance and Security:** Implementation of key security controls including IP Whitelisting, Role-Based Access Control (RBAC), and data encryption (at-rest and in-transit) to meet HIPAA and SOC compliance standards.
*   **Comprehensive Logging and Monitoring:**  Centralized logging and monitoring implemented using AWS CloudWatch Logs for data pipelines and the data warehouse, providing audit trails and enabling proactive issue detection.
*   **Prepared Real-time Monitoring and Alerting Framework:**  Design and infrastructure setup for real-time dashboards and automated alerts (ready for client-side implementation).

**For a high-level overview and project context, please visit the [Project Portfolio Page](https://j-r-manalo.github.io/portfolio/bidatawarehouse/).**

## Architecture
The BI platform architecture is designed for efficiency, scalability, and security, leveraging AWS cloud services.  Key architectural components include:

*   **Data Ingestion:** AWS Lambda functions triggered by S3 events, automating data extraction from external APIs.
*   **Data Transformation and ETL:**  Python-based ETL logic within Lambda functions for data cleaning, transformation, and preparation for the data warehouse.
*   **Data Storage:** AWS RDS PostgreSQL serving as the performant and scalable data warehouse.
*   **Workflow Orchestration:** AWS Step Functions for managing and monitoring data pipeline workflows.
*   **Infrastructure Automation:** Terraform for declarative infrastructure provisioning and management.
*   **Logging and Monitoring:** AWS CloudWatch Logs for centralized logging, and prepared framework for real-time monitoring dashboards and alerts.

**See the [Architecture Diagram]([Link to your Portfolio Page's Architecture Diagram Here]) on the portfolio page for a visual representation of the data flow and system components.**

## Technologies Used

*   **Cloud Platform:** AWS (Amazon Web Services)
*   **Data Warehouse:** AWS RDS PostgreSQL
*   **Data Pipelines / ETL:** AWS Lambda, Python
*   **Workflow Orchestration:** AWS Step Functions
*   **Infrastructure-as-Code:** Terraform
*   **CI/CD:** GitHub Actions
*   **Logging and Monitoring:** AWS CloudWatch Logs
*   **Programming Languages:** Python, HCL (Terraform)

## Repository Structure
Here's the directory structure with comments aligned in the same column:

```bash
.
├── README.md                                      # Main documentation for the project
├── .github                                        # GitHub Actions configuration directory
│         └── workflows                            # Workflows directory
│             └── lambda-layer.tf                  # Build Lambda layer workflow
├── terraform                                      # IaC configuration directory
│         └── itc-beta                             # Beta environment configuration
│             ├── README.md                        # Beta environment documentation
│             ├── main.tf                          # Primary Terraform configuration
│             └── variables.tf                     # Input variables for beta environment
└── terraform_modules                              # Reusable Terraform modules
    ├── __init__.py                                # Python package initialization
    ├── common                                     # Shared utilities and resources
    │         ├── dist                             # Distribution files for common utilities
    │         └── itc_common_utilities             # Common utility package
    │             ├── __init__.py                  # Package initialization
    │             └── logger                       # Logging functionality
    │                 ├── __init__.py              # Logger package initialization
    │                 └── logger_setup.py          # Logging configuration
    ├── demand_pipeline                            # Demand processing pipeline module
    │         ├── README.md                        # Demand pipeline documentation
    │         ├── __init__.py                      # Package initialization
    │         ├── demand_pipeline_lambda.tf        # Lambda function configuration
    │         ├── lambdas                          # Lambda function implementations
    │         │         └── demand_pipeline        # Main demand pipeline function
    │         │                   ├── README.md    # Documentation for the lambda
    │         │                   ├── __init__.py  # Package initialization
    │         │                   ├── builders     # Component builders for the pipeline
    │         │                   │         ├── __init__.py           # Package initialization
    │         │                   │         ├── audit_builder.py      # Audit component builder
    │         │                   │         ├── case_builder.py       # Case component builder
    │         │                   │         ├── metadata_builder.py   # Metadata component builder
    │         │                   │         └── templates_builder.py  # Templates component builder
    │         │                   ├── main.py      # Lambda entry point
    │         │                   ├── poetry.lock  # Dependency lock file
    │         │                   ├── pyproject.toml # Project configuration
    │         │                   ├── tests        # Unit tests directory
    │         │                   │         └── test_main.py  # Main function tests
    │         │                   └── utils.py     # Utility functions
    │         ├── layers                           # Lambda layer resources
    │         │         └── python                 # Python dependencies
    │         │             └── Dockerfile         # Container for layer building
    │         ├── outputs.tf                       # Output variables
    │         └── variables.tf                     # Input variables
    ├── itc_data_warehouse                         # Data warehouse module
    │         ├── README.md                        # Data warehouse documentation
    │         ├── itc_rds.tf                       # RDS database configuration
    │         ├── outputs.tf                       # Output variables
    │         ├── sql_scripts                      # Database initialization scripts
    │         │         ├── 01_create_schemas.sql         # Schema creation script
    │         │         ├── 02_create_verifyplus_table.sql # VerifyPlus table definition
    │         │         ├── 03_create_raw_cases_table.sql  # Cases table definition
    │         │         ├── 04_create_raw_metadata_table.sql # Metadata table definition
    │         │         ├── 05_create_raw_templates_table.sql # Templates table definition
    │         │         ├── 06_create_raw_audits_table.sql   # Audits table definition
    │         │         ├── 07_create_demands_archived_view.sql # Archived demands view
    │         │         ├── 08_create_demands_uploaded_view.sql # Uploaded demands view
    │         │         ├── 09_create_verifyplus_view.sql      # VerifyPlus view
    │         │         ├── 10_create_demands_summary_view.sql # Summary view
    │         │         ├── 11_create_roles.sql                # Database roles
    │         │         ├── 13_grant_usage.sql                 # Permission grants
    │         │         ├── 14_refresh_materialized_views.sql  # View refresh script
    │         │         ├── combine_sql_files.py               # Script to merge SQL files
    │         │         └── combined.sql                       # Combined SQL script
    │         └── variables.tf                     # Input variables
    ├── itc_vpc                                    # VPC network configuration
    │         ├── README.md                        # VPC documentation
    │         ├── itc_vpc.tf                       # VPC resources definition
    │         ├── outputs.tf                       # Output variables
    │         └── variables.tf                     # Input variables
    ├── orchestrator                               # Workflow orchestration module
    │         ├── README.md                        # Orchestrator documentation
    │         ├── lambdas                          # Lambda function implementations
    │         │         └── orchestrator           # Main orchestrator function
    │         │                   ├── README.md    # Documentation for the lambda
    │         │                   ├── main.py      # Lambda entry point
    │         │                   ├── poetry.lock  # Dependency lock file
    │         │                   └── pyproject.toml # Project configuration
    │         ├── layers                           # Lambda layer resources
    │         │         └── python                 # Python dependencies
    │         │             └── Dockerfile         # Container for layer building
    │         ├── orchestrator.tf                  # Orchestrator configuration
    │         └── variables.tf                     # Input variables
    └── verifyplus_pipeline                        # VerifyPlus processing pipeline
        ├── README.md                              # VerifyPlus pipeline documentation
        ├── lambdas                                # Lambda function implementations
        │         └── verifyplus_pipeline          # Main VerifyPlus pipeline function
        │                   ├── README.md          # Documentation for the lambda
        │                   ├── api_handler.py     # API integration handler
        │                   ├── database_handler.py # Database operations handler
        │                   ├── main.py            # Lambda entry point
        │                   ├── poetry.lock        # Dependency lock file
        │                   ├── pyproject.toml     # Project configuration
        │                   ├── tests              # Unit tests directory
        │                   │         ├── test_database_handler.py # Database handler tests
        │                   │         └── test_main.py            # Main function tests
        │                   └── utils.py           # Utility functions
        ├── layers                                 # Lambda layer resources
        │         └── python                       # Python dependencies
        │             └── Dockerfile               # Container for layer building
        ├── outputs.tf                             # Output variables
        ├── variables.tf                           # Input variables
        └── verifyplus_pipeline_lambda.tf          # Lambda function configuration
```
## Data Governance and Security

Adherence to **HIPAA and SOC regulations** was a primary consideration.  The project incorporates the following key data governance and security measures:

*   **Access Control:**  IP Whitelisting and Role-Based Access Control (RBAC) implemented to restrict access to sensitive data based on the principle of least privilege.
*   **Data Encryption:**  Data at-rest (using AWS RDS encryption) and in-transit (using TLS/SSL) are encrypted to ensure data confidentiality and integrity.
*   **Audit Logging:** Comprehensive audit logging is enabled across data pipelines and the data warehouse, providing a clear audit trail for compliance and security monitoring.
*   **Standardized Access Processes:** Documented access request and approval processes are established for auditability and controlled access management.

## Real-time Monitoring and Alerting (Prepared for Implementation)

While full real-time dashboards and alerts were only prepared for future client deployment due to project time constraints, the infrastructure and design for this critical component are in place.  This includes:

*   **Designed KPI Dashboards:** Specifications for real-time dashboards visualizing key performance indicators and system health metrics.
*   **Automated Alerting Framework:**  Configuration prepared for automated alerts to trigger notifications for critical events, enabling rapid incident response.

## Getting Started

To explore this project:

1.  **Browse the Repository:**  Review the code in the `terraform/` and `terraform_modules/` directories to examine the implementation details of the data pipelines and infrastructure-as-code configurations.
2.  **Review Terraform Configuration:**  Examine the Terraform files in the subdirectories under `terraform_modules/` to understand how the AWS infrastructure was provisioned and configured.
3.  **Examine Python Code:**  Explore the Python scripts in the `lambdas/` subdirectories to review the data ingestion, ETL logic, and database interactions.
4.  **Refer to Portfolio Page:** Visit the [Project Portfolio Page](https://j-r-manalo.github.io/portfolio/bidatawarehouse/) for a high-level project overview, architecture diagram, and summary of key outcomes.

## License

This project is licensed under the [MIT License](https://mit-license.org/).

## Author

Jonathan R. Manalo - [Portfolio](https://j-r-manalo.github.io/)

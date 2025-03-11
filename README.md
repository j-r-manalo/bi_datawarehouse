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
```bash


```
## Data Governance and Security

Adherence to **HIPAA and SOC regulations** was a primary consideration.  The project incorporates the following key data governance and security measures:

*   **Access Control:**  IP Whitelisting and Role-Based Access Control (RBAC) implemented to restrict access to sensitive data based on the principle of least privilege.
*   **Data Encryption:**  Data at-rest (using AWS RDS encryption) and in-transit (using TLS/SSL) are encrypted to ensure data confidentiality and integrity.
*   **Audit Logging:** Comprehensive audit logging is enabled across data pipelines and the data warehouse, providing a clear audit trail for compliance and security monitoring.
*   **Standardized Access Processes:** Documented access request and approval processes are established for auditability and controlled access management.

## Real-time Monitoring and Alerting (Prepared for Implementation)

While full real-time dashboards and alerts were prepared for future client deployment due to project time constraints, the infrastructure and design for this critical component are in place.  This includes:

*   **Designed KPI Dashboards:** Specifications for real-time dashboards visualizing key performance indicators and system health metrics.
*   **Automated Alerting Framework:**  Configuration prepared for automated alerts to trigger notifications for critical events, enabling rapid incident response.

## Getting Started

To explore this project:

1.  **Browse the Repository:**  Review the code in the `data_pipelines/` and `infrastructure/` directories to examine the implementation details of the data pipelines and infrastructure-as-code configurations.
2.  **Review Terraform Configuration:**  Examine the Terraform files in the `infrastructure/` directory to understand how the AWS infrastructure was provisioned and configured.
3.  **Examine Python Code:**  Explore the Python scripts in the `data_pipelines/` directory to review the data ingestion, ETL logic, and database interactions.
4.  **Refer to Portfolio Page:** Visit the [Project Portfolio Page](https://j-r-manalo.github.io/portfolio/bidatawarehouse/) for a high-level project overview, architecture diagram, and summary of key outcomes.

---
## License

This project is licensed under the [MIT License](https://mit-license.org/).

---
## Author

Jonathan R. Manalo - [Portfolio](https://j-r-manalo.github.io/)

---
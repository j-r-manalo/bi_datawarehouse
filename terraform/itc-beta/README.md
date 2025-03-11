# ITC Infrastructure for Invoice Transactions

## Overview

This Terraform configuration provisions the complete infrastructure for managing invoice transactions in the **beta** environment. It creates an AWS environment that includes a VPC, a postgresql data warehouse on RDS, and two Lambda pipelines (Demand Pipeline and Verify+ Pipeline) that are scheduled using AWS EventBridge.

## Infrastructure Components

This configuration is organized into several submodules:

- **ITC VPC Module**  
  - **Purpose:** Provisions an AWS Virtual Private Cloud (VPC) with both public and private subnets, an Internet Gateway, NAT Gateway, routing, security groups, and VPC endpoints.
  - **Key Resources:** VPC, subnets, security groups, routing tables, NAT Gateway, VPC endpoints.

- **ITC Data Warehouse Module**  
  - **Purpose:** Sets up the ITC data warehouse infrastructure by provisioning an Amazon RDS PostgreSQL instance, a Secrets Manager secret for database credentials, and a security group for controlling database access.
  - **Key Resources:** RDS PostgreSQL database instance, Secrets Manager secret, RDS security group.

- **Demand Pipeline Lambda Module**  
  - **Purpose:** Deploys a Lambda function that processes demand pipeline data. It includes a CloudWatch log group for logging, an S3 bucket for storing Lambda layers and code packages, and the necessary IAM roles and policies.
  - **Key Resources:** Lambda function, CloudWatch log group, S3 bucket for Lambda layers, Lambda layer, IAM role & policies, VPC configuration for the Lambda.

- **Verify+ Pipeline Lambda Module**  
  - **Purpose:** Deploys the Lambda function for the Verify+ Pipeline. Similar to the Demand Pipeline Lambda, it provisions a CloudWatch log group, an S3 bucket for Lambda layers and code, a Lambda layer for Python dependencies, and the required IAM roles and policies.
  - **Key Resources:** Lambda function, CloudWatch log group, Secrets Manager secret for the Quickbase token, S3 bucket for Lambda layers, Lambda layer, IAM role & policies, VPC configuration.

- **Orchestrator Module**  
  - **Purpose:** Executes Demand Pipeline and Verify+ Pipeline in a parallel workflow, then the Orchestrator refreshes materialized views last.
  - **Key Resources:** State machine and Step Functions.

## Providers and Backend

- **AWS Provider:** Configured to operate in the `us-east-1` region with default tags applied to all resources (including environment, owner, and Terraform flags).
- **Terraform Backend:** Uses an S3 bucket with DynamoDB for state locking to ensure safe and consistent state management.

## Variables and Locals

The configuration defines several local variables for consistent naming and parameter passing across modules. Key variables include:

- `database_prefix`
- `env`
- `source_env`
- `region`
-`allowed_postgres_cidrs`
- `quickbase_token`
- `db_username`
- `db_identifier`
- `secret_name`

These variables ensure that submodules receive the correct values to provision the infrastructure.

## Deployment Steps

1. **Initialize Terraform:**  
   ```sh
   terraform init
   ```

2. **Plan the Deployment:**  
   ```sh
   terraform plan
   ```

3. **Apply the Changes:**  
   ```sh
   terraform apply
   ```

## Cleanup

To remove all the deployed resources, run:
```sh
terraform destroy
```

## Overall Workflow

1. **VPC Setup:**  
   The **ITC VPC Module** creates the network environment, including subnets, routing, and security groups, which are shared across all other modules.

2. **Data Warehouse:**  
   The **ITC Data Warehouse Module** provisions the RDS PostgreSQL instance and the associated secrets for secure credential management.

3. **Demand Pipeline:**  
   The **Demand Pipeline Lambda Module** deploys a Lambda function to process demand data.
 
4. **Verify+ Pipeline:**  
   The **Verify+ Pipeline Lambda Module** deploys another Lambda function to process the Verify+ pipeline.

5. **Orchestrator:**
   - The **Orchestrator Lambda Module** deploys a Lambda function to refresh the materialized views.
   - The **Orchestrator Module** configures a step function to run the Demand Pipeline Lambda and Verify+ Pipeline Lambda functions in parallel, then runs the Orchestrator Lambda last.
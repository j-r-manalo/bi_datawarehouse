# ITC Orchestrator Submodule

## Overview

This submodule provisions the **ITC Orchestrator** components, enabling a Step Functions state machine to coordinate the Demand Pipeline, Verify+ Pipeline, and a final view-refresh step via a dedicated Orchestrator Lambda. It includes the necessary infrastructure for packaging Lambda code, creating IAM roles and policies, uploading artifacts to S3, and optionally scheduling the orchestrated workflow using EventBridge/CloudWatch.

## Infrastructure Components

- **Orchestrator Lambda**  
  - **Purpose:** Runs a Python 3.12 Lambda function that refreshes materialized views in the PostgreSQL database.
  - **Key Resources:**  
    - `aws_lambda_function.orchestrator_lambda`: The Lambda function code and configuration (VPC, environment variables).  
    - `aws_iam_role.orchestrator_lambda_role` & `aws_iam_policy.orchestrator_lambda_policy`: IAM permissions for logging, networking, Secrets Manager (for DB creds), and S3 access.  
    - `aws_cloudwatch_log_group.orchestrator_log_group`: Stores Lambda logs.  
    - `aws_s3_bucket.orchestrator_bucket` & `aws_s3_object.orchestrator_lambda_code`: Bucket and object for the Lambda deployment package.  
    - `aws_lambda_layer_version.orchestrator_python_layer`: Lambda Layer for Python dependencies.

- **Step Functions State Machine**  
  - **Purpose:** Executes Demand Pipeline, Verify+ Pipeline, and the Orchestrator Lambda in a parallelized workflow (Demand and Verify+ run in parallel, then the Orchestrator Lambda runs last).  
  - **Key Resources:**  
    - `aws_sfn_state_machine.orchestration`: Defines the states and transitions (in JSON) that invoke each Lambda.  
    - `aws_iam_role.sfn_role` & `aws_iam_policy.sfn_policy`: IAM role and policy granting permissions to invoke the Lambdas in the state machine.

- **EventBridge / CloudWatch Scheduling**  
  - **Purpose:** Optionally schedules the Step Functions workflow via a cron expression.  
  - **Key Resources:**  
    - `aws_cloudwatch_event_rule.orchestration_schedule`: Defines the cron schedule to trigger the state machine.  
    - `aws_iam_role.eventbridge_role` & `aws_iam_policy.eventbridge_policy`: Grants EventBridge permission to start the Step Functions workflow.  
    - `aws_cloudwatch_event_target.orchestration_target`: Associates the scheduling rule with the state machine.

## Providers and Backend

- **AWS Provider:**  
  - Expects standard configuration (region, credentials, etc.).  
  - Creates resources in your specified region with tags provided by your broader Terraform configuration.

- **Terraform Backend:**  
  - This submodule typically uses the same S3 + DynamoDB backend for state locking as the overall ITC infrastructure configuration. Refer to your parent module or root module for backend details.

## Variables and Locals

Key variables and locals used in this submodule:

- **`local.orchestrator_name`**: Constructs a short name for all Orchestrator resources (e.g., `mydb-beta-orchestrator`).
- **`var.itc_database_prefix`** & **`var.env`**: Used to build resource names and ensure environment isolation.
- **`var.lambda_memory_size`** & **`var.lambda_timeout`**: Controls the Orchestrator Lambda’s resource allocation and max execution time.
- **`var.pg_endpoint`** & **`var.pg_secret_arn`**: Passed as environment variables to the Orchestrator Lambda for connecting to PostgreSQL via Secrets Manager.
- **`var.local_mode`**: Determines if the Orchestrator Lambda should reference local environment variables vs. using AWS Secrets Manager (if applicable).
- **`var.private_subnet_ids`** & **`var.shared_lambda_sg_id`**: Defines the VPC networking details for the Lambda function (subnets and security group).
- **`var.demand_pipeline_lambda_arn`** & **`var.verifyplus_pipeline_lambda_arn`**: ARNs for the Demand and Verify+ Pipeline Lambdas, invoked in the state machine.
- **`var.orchestrator_cron_schedule`**: Sets the CloudWatch cron expression for triggering the state machine (optional).

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

To remove all resources created by this submodule, run:
```sh
terraform destroy
```

## Overall Workflow

1. **Lambda Packaging and Upload:**  
   The Orchestrator Lambda code and dependencies are zipped, uploaded to S3, and used to create a Lambda function and its associated Python layer.

2. **IAM Configuration:**  
   Roles and policies are provisioned for both the Lambda function and the Step Functions workflow, granting permissions to invoke Lambdas, access Secrets Manager, and write logs to CloudWatch.

3. **Step Functions Orchestration:**  
   - The state machine starts with a parallel step, invoking both the **Demand Pipeline** and **Verify+ Pipeline** Lambdas concurrently.  
   - After both pipelines complete, the **Orchestrator Lambda** is invoked to refresh materialized views in the database.

4. **Optional Scheduling:**  
   An EventBridge (CloudWatch) schedule rule can be enabled to run the entire state machine at regular intervals (e.g., daily, hourly), fully automating the data workflows without manual intervention.
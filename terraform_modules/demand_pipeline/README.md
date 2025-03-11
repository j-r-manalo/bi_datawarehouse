# Demand Pipeline Lambda Submodule

## Purpose

This module provisions the infrastructure for the Demand Pipeline Lambda function on AWS, including:

- An AWS Lambda function for processing demand pipeline data.
- A CloudWatch Log Group for logging Lambda execution.
- An S3 bucket for storing Lambda layers and code packages.
- An IAM role with necessary permissions for Lambda execution.
- A Lambda layer for Python dependencies.
- Security groups and policies for access to DynamoDB, RDS, and Secrets Manager.

## Usage

To use this module, see the usage in the main `main.tf`.

## Inputs

* `itc_database_prefix` - Prefix for database-related resources.
* `env` - Deployment environment (e.g., dev, prod).
* `lambda_handler` - Entry point for the Lambda function.
* `lambda_memory_size` - Memory allocated to the Lambda function.
* `lambda_timeout` - Timeout duration for Lambda execution.
* `vpc_id` - VPC ID where the Lambda function is deployed.
* `private_subnet_ids` - List of private subnets for Lambda deployment.
* `security_group_id` - Security group ID for RDS access.
* `vpc_endpoints_sg_id` - Security group ID for VPC endpoints.
* `pg_secret_arn` - ARN of the Secrets Manager secret containing RDS credentials.
* `pg_endpoint` - Endpoint of the PostgreSQL RDS instance.
* `xray_tracing_enabled` - Whether to enable AWS X-Ray tracing.
* `local_mode` - Whether the Lambda function is running in local mode.
* `source_env` - The source environment name.

## Outputs

This module provides the following outputs:

* `lambda_arn` - The ARN of the deployed Lambda function.
* `log_group_name` - The name of the CloudWatch Log Group for the Lambda function.
* `s3_bucket_name` - The name of the S3 bucket storing Lambda layers and code.

## Resources Created

This module provisions the following AWS resources:

- **Lambda Function**

```hcl
resource "aws_lambda_function" "demand_pipeline_lambda" {
  function_name    = local.demand_pipeline_lambda_name
  role            = aws_iam_role.demand_pipeline_lambda_role.arn
  runtime        = "python3.12"
  architectures  = ["arm64"]
  handler        = var.lambda_handler
  timeout        = var.lambda_timeout
  memory_size    = var.lambda_memory_size
  s3_bucket      = aws_s3_bucket.lambda_layer_bucket.id
  s3_key         = aws_s3_object.demand_pipeline_lambda_code.key
  source_code_hash = filebase64sha256(data.archive_file.demand_pipeline_lambda_zip.output_path)
  layers         = [aws_lambda_layer_version.python_layer.arn]
  vpc_config {
    security_group_ids = [aws_security_group.itc_lambda_sg.id]
    subnet_ids         = var.private_subnet_ids
  }
}
```

- **CloudWatch Log Group**

```hcl
resource "aws_cloudwatch_log_group" "demand_pipeline_lambda_log_group" {
  name              = "/aws/lambda/${local.demand_pipeline_lambda_name}"
  retention_in_days = 7
}
```

- **S3 Bucket for Lambda Layers**

```hcl
resource "aws_s3_bucket" "lambda_layer_bucket" {
  bucket = "${var.itc_database_prefix}-${var.env}-lambda-layer-bucket"
}
```

- **IAM Role for Lambda Execution**

```hcl
resource "aws_iam_role" "demand_pipeline_lambda_role" {
  name = "${local.demand_pipeline_lambda_name}-role"
  assume_role_policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [{
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"}
    }]
  })
}
```

- **Security Group for RDS Access**

```hcl
resource "aws_security_group_rule" "allow_lambda_rds" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = var.security_group_id
  source_security_group_id = aws_security_group.itc_lambda_sg.id
}
```

## Notes

- Ensure that the specified `private_subnet_ids` belong to the correct VPC.
- The Lambda function requires permissions to access Secrets Manager, DynamoDB, and RDS.
- AWS X-Ray tracing is enabled by default but can be disabled by setting `xray_tracing_enabled = false`.
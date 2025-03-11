# Verify+ Pipeline Lambda Submodule

## Purpose

This submodule provisions the infrastructure for the **Verify+ Pipeline Lambda** function on AWS. It includes:

- A **CloudWatch Log Group** for logging Lambda executions.
- An **AWS Secrets Manager Secret** for securely storing the Quickbase API token.
- An **S3 Bucket** for storing the Lambda layer.
- A **Lambda Layer** for managing Python dependencies.
- An **IAM Role and Policy** for granting Lambda necessary permissions.
- A **Lambda Function** for processing the Verify+ Pipeline.
- **Security Groups and Rules** to allow access to required services.

# Verify+ Pipeline Lambda Submodule

## Purpose

This submodule provisions the AWS infrastructure for the Verify+ pipeline Lambda, including:

- A CloudWatch Log Group for logging.
- A Secrets Manager secret to store the Quickbase token.
- An S3 bucket for storing Lambda layers and code.
- A Lambda Layer for Python dependencies.
- An IAM role and policies for execution permissions.
- A Lambda function for the Verify+ pipeline.
- Security groups for network access.

## Usage
To use this module, see the usage in the main `main.tf`.

## Inputs

- `itc_database_prefix`: Prefix for naming AWS resources.
- `env`: Environment name (e.g., `dev`, `prod`).
- `quickbase_token`: API token for Quickbase access.
- `lambda_handler`: Lambda function handler (e.g., `main.handler`).
- `lambda_memory_size`: Memory allocation for the Lambda function.
- `lambda_timeout`: Timeout in seconds for the Lambda function.
- `xray_tracing_enabled`: Whether AWS X-Ray tracing is enabled.
- `vpc_id`: VPC ID where the Lambda function will be deployed.
- `private_subnet_ids`: List of private subnet IDs for Lambda VPC configuration.
- `security_group_id`: Security group ID for RDS access.
- `vpc_endpoints_sg_id`: Security group ID for VPC endpoint access.
- `pg_endpoint`: PostgreSQL database endpoint.
- `pg_secret_arn`: ARN of the Secrets Manager secret storing the database credentials.

## Outputs

- `lambda_function_name`: Name of the provisioned Lambda function.
- `lambda_role_arn`: ARN of the IAM role assigned to the Lambda function.
- `lambda_log_group`: Name of the CloudWatch Log Group for the Lambda function.
- `secret_arn`: ARN of the Secrets Manager secret containing the Quickbase token.
- `s3_bucket_name`: Name of the S3 bucket storing Lambda layers and code.

## Resources Created

### CloudWatch Log Group
```hcl
resource "aws_cloudwatch_log_group" "verifyplus_pipeline_lambda_log_group" {
  name              = "/aws/lambda/${local.verifyplus_pipeline_lambda_name}"
  retention_in_days = 7
}
```

### AWS Secrets Manager
```hcl
resource "aws_secretsmanager_secret" "quickbase_secret" {
  name = "${var.itc_database_prefix}-quickbase-token"
}

resource "aws_secretsmanager_secret_version" "quickbase_secret_version" {
  secret_id     = aws_secretsmanager_secret.quickbase_secret.id
  secret_string = var.quickbase_token
}
```

### S3 Bucket for Lambda Layer
```hcl
resource "aws_s3_bucket" "verifyplus_lambda_layer_bucket" {
  bucket = "${var.itc_database_prefix}-${var.env}-verifyplus-lambda-layer-bucket"
}
```

### Lambda Layer for Python Dependencies
```hcl
resource "aws_lambda_layer_version" "verifyplus_python_layer" {
  layer_name          = "verifyplus-python-layer"
  description         = "Lambda layer for python dependencies."
  compatible_runtimes = ["python3.12"]
  s3_bucket          = aws_s3_bucket.verifyplus_lambda_layer_bucket.id
  s3_key             = "lambda_layers/verifyplus_layer.zip"
}
```

### IAM Role and Policy for Lambda
```hcl
resource "aws_iam_role" "verifyplus_pipeline_lambda_role" {
  name = "${local.verifyplus_pipeline_lambda_name}-role"
  assume_role_policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [{
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" }
    }]
  })
}
```

### Lambda Function Deployment
```hcl
resource "aws_lambda_function" "verifyplus_pipeline_lambda" {
  function_name = local.verifyplus_pipeline_lambda_name
  role          = aws_iam_role.verifyplus_pipeline_lambda_role.arn
  s3_bucket     = aws_s3_bucket.verifyplus_lambda_layer_bucket.id
  s3_key        = "lambda_functions/verifyplus_pipeline.zip"
  runtime       = "python3.12"
  handler       = var.lambda_handler
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout
  layers        = [aws_lambda_layer_version.verifyplus_python_layer.arn]
  vpc_config {
    security_group_ids = [aws_security_group.itc_verifyplus_lambda_sg.id]
    subnet_ids         = var.private_subnet_ids
  }
  environment {
    variables = {
      PG_ENDPOINT         = var.pg_endpoint
      PG_SECRET_ARN       = var.pg_secret_arn
      QUICKBASE_API_TOKEN = var.quickbase_token
    }
  }
}
```

### Security Group for Lambda
```hcl
resource "aws_security_group" "itc_verifyplus_lambda_sg" {
  name   = "${var.itc_database_prefix}-verifyplus-lambda-sg"
  vpc_id = var.vpc_id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### Security Group Rule for RDS Access
```hcl
resource "aws_security_group_rule" "allow_lambda_rds" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = var.security_group_id
  source_security_group_id = aws_security_group.itc_verifyplus_lambda_sg.id
}
```

## Notes
- The Lambda function runs in a VPC and requires private subnet IDs.
- The security group is configured to allow access to RDS and Secrets Manager.
- AWS X-Ray tracing can be enabled using `xray_tracing_enabled`.
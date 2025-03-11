#############################################
# Demand Pipeline Lambda Submodule
#############################################

#############################################
# Fetch the latest layer ARN from Parameter Store
#############################################
data "aws_ssm_parameter" "demand_layer_arn" {
  count = var.skip_layer_lookup ? 0 : 1
  name  = "/lambda-layers/demand-${var.env}-layer/latest-arn"
}

# Default layer configuration for initial deployment
locals {
  demand_pipeline_lambda_name = "${var.itc_database_prefix}-demand-pipeline"
  demand_layer_arn = var.skip_layer_lookup ? null : try(data.aws_ssm_parameter.demand_layer_arn[0].value, null)

  # Directly specify the AWS SDK Pandas ARN
  aws_sdk_pandas_arn = "arn:aws:lambda:${var.region}:336392948345:layer:AWSSDKPandas-Python312-Arm64:16"

 # Create a list of layers with null handling
  lambda_layers = local.demand_layer_arn != null ? [local.demand_layer_arn, local.aws_sdk_pandas_arn] : [local.aws_sdk_pandas_arn]
}

#############################################
# CloudWatch Log Group
#############################################
resource "aws_cloudwatch_log_group" "demand_pipeline_lambda_log_group" {
  name              = "/aws/lambda/${local.demand_pipeline_lambda_name}"
  retention_in_days = 7 # How long to store logs for before they are automatically purged, this stuff adds up QUICK and is surprisingly expensive.
  lifecycle {
    prevent_destroy = false
  }
}

#############################################
# Create bucket for the lambda
#############################################

resource "aws_s3_bucket" "lambda_layer_bucket" {
  bucket = "${var.itc_database_prefix}-${var.env}-lambda-layer-bucket"  # Change to your desired bucket name
}

#############################################
# Execution role for the lambda
#############################################

resource "aws_iam_role" "demand_pipeline_lambda_role" {
  name = "${local.demand_pipeline_lambda_name}-role" # must come before the lambda, but want to reference it's name
  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      { # Allow the lambda to be executed, It's an AWS thing.
        Action : "sts:AssumeRole",
        Effect : "Allow",
        Principal : {
          "Service" : "lambda.amazonaws.com"
        }
      }
    ]
  })
}

######################################
# Create Pipeline Policy for Lambda's Role
######################################
resource "aws_iam_policy" "demand_pipeline_lambda_policy" {
  name = "${local.demand_pipeline_lambda_name}-policy"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : concat(
      [
        { # Allow Lambda to Assume the Cross-Account Role
          Effect : "Allow",
          Action : "sts:AssumeRole",
          Resource : "arn:aws:iam::731876215943:role/DataScienceCrossAccountDDBAccess"
        },
        { # Logs
          Action : [
            # Don't need CreateLogGroup permission because we make the group ourselves to manage it's lifecycle
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ],
          Effect : "Allow",
          Resource : "arn:aws:logs:*:*:*" # Technically over provisioned but it can only emit stuff so the worst that can happen is creating noise in log streams, and debugging this is a nightmare if it goes sideways. AWS defaults are way more open.
        },
        { # Dynamo Table Permission for batch coordination
          Effect : "Allow",
          Action : [
            "dynamodb:PutItem",
            "dynamodb:GetItem",
            "dynamodb:UpdateItem",
            "dynamodb:Query",
            "dynamodb:Scan",
          ],
          Resource : [
            "arn:aws:dynamodb:us-east-1:${var.source_account}:table/exchange-${var.source_env}-documents",
            "arn:aws:dynamodb:us-east-1:${var.source_account}:table/exchange-${var.source_env}-documents/*",
            "arn:aws:dynamodb:us-east-1:${var.source_account}:table/exchange-${var.source_env}-documents-metadata",
            "arn:aws:dynamodb:us-east-1:${var.source_account}:table/exchange-${var.source_env}-documents-metadata/*",
            "arn:aws:dynamodb:us-east-1:${var.source_account}:table/exchange-${var.source_env}-templates",
            "arn:aws:dynamodb:us-east-1:${var.source_account}:table/exchange-${var.source_env}-templates/*",
            "arn:aws:dynamodb:us-east-1:${var.source_account}:table/exchange-${var.source_env}-documents-audit",
            "arn:aws:dynamodb:us-east-1:${var.source_account}:table/exchange-${var.source_env}-documents-audit/*",
          ],
        },
        {
            Effect: "Allow",
            Action: [
                "ec2:CreateNetworkInterface",
                "ec2:DeleteNetworkInterface",
                "ec2:DescribeNetworkInterfaces"
            ],
            Resource: "*"
        },
        { # RDS Instance Describe
          Action : [
            "rds:DescribeDBInstances"
          ],
          Effect : "Allow",
          Resource : "*"
        },
        { # Secrets Manager Access for DB credentials
          Effect : "Allow",
          Action : [
            "secretsmanager:GetSecretValue",
            "secretsmanager:DescribeSecret"
          ],
          Resource : var.pg_secret_arn
        },
        { # SSM Parameter Store Access for layer ARN
          Effect : "Allow",
          Action : [
            "ssm:GetParameter",
            "ssm:GetParameters"
          ],
          Resource : "arn:aws:ssm:*:*:parameter/lambda-layers/*"
        },
        {
          Effect   = "Allow"
          Action   = ["s3:GetObject", "s3:ListBucket"]
          Resource = [
            "arn:aws:s3:::${aws_s3_bucket.lambda_layer_bucket.bucket}",
            "arn:aws:s3:::${aws_s3_bucket.lambda_layer_bucket.bucket}/*"
          ]
        }
      ],
    )
  })
}

######################################
# Attach Pipeline Policy for Lambda's Role
######################################
resource "aws_iam_role_policy_attachment" "demand_pipeline_role_policy_attachment" {
  role       = aws_iam_role.demand_pipeline_lambda_role.id
  policy_arn = aws_iam_policy.demand_pipeline_lambda_policy.arn
}

#############################################
# Package the Lambda Code
#############################################
data "archive_file" "demand_pipeline_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../demand_pipeline/lambdas/demand_pipeline"  # Adjust as needed.
  output_path = "${path.module}/../demand_pipeline/lambdas/demand_pipeline.zip"
}

#############################################
# Upload package to S3
#############################################
resource "aws_s3_object" "demand_pipeline_lambda_code" {
  bucket = aws_s3_bucket.lambda_layer_bucket.id
  key    = "lambda_functions/demand_pipeline.zip"
  source = data.archive_file.demand_pipeline_lambda_zip.output_path
  etag   = filemd5(data.archive_file.demand_pipeline_lambda_zip.output_path)
}

#############################################
# Create the Lambda Function
#############################################

resource "aws_lambda_function" "demand_pipeline_lambda" {
  function_name = local.demand_pipeline_lambda_name
  description   = "Lambda for the Demand Pipeline."
  role          = aws_iam_role.demand_pipeline_lambda_role.arn

  # Use S3 instead of direct upload
  s3_bucket        = aws_s3_bucket.lambda_layer_bucket.id
  s3_key           = aws_s3_object.demand_pipeline_lambda_code.key
  source_code_hash = data.archive_file.demand_pipeline_lambda_zip.output_base64sha256

  handler       = var.lambda_handler    # e.g., "main.handler"
  runtime       = "python3.12"           # Adjust if needed.
  architectures = ["arm64"]

  # Use the latest layer ARN from Parameter Store (if available)
  layers = local.lambda_layers

  memory_size = var.lambda_memory_size   # e.g., 256
  timeout     = var.lambda_timeout       # e.g., 90

  # If your Lambda runs in your VPC, pass in the necessary subnet IDs and security group IDs.
  vpc_config {
    security_group_ids = var.shared_lambda_sg_id
    subnet_ids         = var.private_subnet_ids
  }

  tracing_config {
    mode = var.xray_tracing_enabled ? "Active" : "PassThrough"
  }

  environment {
    variables = {
      LOCAL_MODE      = var.local_mode
      ENV             = var.env
      SOURCE_ENV      = var.source_env
      SOURCE_ACCOUNT  = var.source_account
      PG_ENDPOINT     = var.pg_endpoint
      PG_SECRET_ARN   = var.pg_secret_arn
    }
  }
}

resource "aws_iam_role_policy_attachment" "xray_tracing_policy_attachment" {
  count      = var.xray_tracing.enabled ? 1 : 0
  role       = aws_iam_role.demand_pipeline_lambda_role.id
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}
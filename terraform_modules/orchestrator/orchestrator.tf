#############################################
# Orchestrator Submodule
#############################################

#############################################
# Fetch the latest layer ARN from Parameter Store
#############################################
data "aws_ssm_parameter" "orchestrator_layer_arn" {
  count = var.skip_layer_lookup ? 0 : 1
  name  = "/lambda-layers/orchestrator-${var.env}-layer/latest-arn"
}

# Default layer configuration for initial deployment
locals {
  orchestrator_name = "${var.itc_database_prefix}-${var.env}-orchestrator"
  orchestrator_layer_arn = var.skip_layer_lookup ? null : try(data.aws_ssm_parameter.orchestrator_layer_arn[0].value, null)
}

#############################################
# CloudWatch Log Group
#############################################
resource "aws_cloudwatch_log_group" "orchestrator_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.orchestrator_lambda.function_name}"
  retention_in_days = 7 # How long to store logs for before they are automatically purged, this stuff adds up QUICK and is surprisingly expensive.
  lifecycle {
    prevent_destroy = false
  }
}

#############################################
# Create bucket for the lambda
#############################################

resource "aws_s3_bucket" "orchestrator_bucket" {
  bucket = "${local.orchestrator_name}-lambda-bucket"  # Change to your desired bucket name
}

###############################################################################
# Package up the code for the Lambda can use it
###############################################################################
data "archive_file" "orchestrator_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../orchestrator/lambdas/orchestrator"  # Adjust as needed.
  output_path = "${path.module}/../orchestrator/lambdas/orchestrator.zip"
  excludes    = ["poetry.lock", "pyproject.toml", ".venv", ".env"]
}

#############################################
# Upload package to S3
#############################################
resource "aws_s3_object" "orchestrator_lambda_code" {
  bucket = aws_s3_bucket.orchestrator_bucket.id
  key    = "lambda_functions/orchestrator.zip"
  source = data.archive_file.orchestrator_lambda_zip.output_path
  etag   = filemd5(data.archive_file.orchestrator_lambda_zip.output_path)
}

#############################################
# Execution role for the lambda
#############################################

resource "aws_iam_role" "orchestrator_lambda_role" {
  name = "${local.orchestrator_name}-role" # must come before the lambda, but want to reference it's name
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
resource "aws_iam_policy" "orchestrator_lambda_policy" {
  name = "${local.orchestrator_name}-policy"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : concat(
      [
        { # Logs
          Action : [
            # Don't need CreateLogGroup permission because we make the group ourselves to manage it's lifecycle
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ],
          Effect : "Allow",
          Resource : "arn:aws:logs:*:*:*" # Technically over provisioned but it can only emit stuff so the worst that can happen is creating noise in log streams, and debugging this is a nightmare if it goes sideways. AWS defaults are way more open.
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
            "arn:aws:s3:::${aws_s3_bucket.orchestrator_bucket.bucket}",
            "arn:aws:s3:::${aws_s3_bucket.orchestrator_bucket.bucket}/*"
          ]
        }
      ],
    )
  })
}

######################################
# Attach Pipeline Policy for Lambda's Role
######################################
resource "aws_iam_role_policy_attachment" "orchestrator_role_policy_attachment" {
  role       = aws_iam_role.orchestrator_lambda_role.id
  policy_arn = aws_iam_policy.orchestrator_lambda_policy.arn
}

###############################################################################
# The Orchestrator Lambda function
###############################################################################
resource "aws_lambda_function" "orchestrator_lambda" {
  function_name = "${local.orchestrator_name}-lambda"
  description   = "Lambda for the ITC Orchestrator."
  role          = aws_iam_role.orchestrator_lambda_role.arn

  # Use S3 instead of direct upload
  s3_bucket        = aws_s3_bucket.orchestrator_bucket.id
  s3_key           = aws_s3_object.orchestrator_lambda_code.key
  source_code_hash = data.archive_file.orchestrator_lambda_zip.output_base64sha256

  handler       = "main.handler"
  runtime       = "python3.12"           # Adjust if needed.
  architectures = ["arm64"]

  # Use the latest layer ARN from Parameter Store (if available)
  layers        = local.orchestrator_layer_arn != null ? [local.orchestrator_layer_arn] : []

  memory_size   = var.lambda_memory_size   # e.g., 256
  timeout       = var.lambda_timeout       # e.g., 90

  # Put Lambda in same VPC as the DB
  vpc_config {
    security_group_ids = var.shared_lambda_sg_id
    subnet_ids         = var.private_subnet_ids
  }

  environment {
    variables = {
      LOCAL_MODE      = var.local_mode
      PG_ENDPOINT     = var.pg_endpoint
      PG_SECRET_ARN   = var.pg_secret_arn
    }
  }
}


###############################################################################
# IAM Role & Policy for Step Functions
###############################################################################
data "aws_iam_policy_document" "sfn_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sfn_role" {
  name               = "${local.orchestrator_name}-stepfunction-role"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume_role.json
}

data "aws_iam_policy_document" "sfn_policy_doc" {
  statement {
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      var.demand_pipeline_lambda_arn,
      var.verifyplus_pipeline_lambda_arn,
      aws_lambda_function.orchestrator_lambda.arn
    ]
  }
}

resource "aws_iam_policy" "sfn_policy" {
  name   = "${local.orchestrator_name}-stepfunction-policy"
  policy = data.aws_iam_policy_document.sfn_policy_doc.json
}

resource "aws_iam_role_policy_attachment" "sfn_attach" {
  role       = aws_iam_role.sfn_role.name
  policy_arn = aws_iam_policy.sfn_policy.arn
}

###############################################################################
# Step Functions State Machine
###############################################################################
resource "aws_sfn_state_machine" "orchestration" {
  name     = "${local.orchestrator_name}-stepfunction"
  role_arn = aws_iam_role.sfn_role.arn

  definition = <<EOF
{
  "Comment": "Run Demand and VerifyPlus in parallel (async) then RefreshViews",
  "StartAt": "DemandAndVerifyParallel",
  "States": {
    "DemandAndVerifyParallel": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "DemandPipeline",
          "States": {
            "DemandPipeline": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "Parameters": {
                "FunctionName": "${var.demand_pipeline_lambda_arn}",
                "InvocationType": "RequestResponse"
              },
              "Retry": [
                {
                  "ErrorEquals": ["States.ALL"],
                  "IntervalSeconds": 2,
                  "MaxAttempts": 3,
                  "BackoffRate": 2.0
                }
              ],
              "End": true
            }
          }
        },
        {
          "StartAt": "VerifyPlusPipeline",
          "States": {
            "VerifyPlusPipeline": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "Parameters": {
                "FunctionName": "${var.verifyplus_pipeline_lambda_arn}",
                "InvocationType": "RequestResponse"
              },
              "Retry": [
                {
                  "ErrorEquals": ["States.ALL"],
                  "IntervalSeconds": 2,
                  "MaxAttempts": 3,
                  "BackoffRate": 2.0
                }
              ],
              "End": true
            }
          }
        }
      ],
      "Next": "RefreshViews"
    },
    "RefreshViews": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${aws_lambda_function.orchestrator_lambda.arn}",
        "InvocationType": "RequestResponse"
      },
      "Retry": [
        {
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2.0
        }
      ],
      "End": true
    }
  }
}
EOF
}

###############################################################################
# Optional: Schedule this State Machine via CloudWatch cron
###############################################################################
resource "aws_cloudwatch_event_rule" "orchestration_schedule" {
  name                = "${local.orchestrator_name}-schedule"
  schedule_expression = var.orchestrator_cron_schedule
}

#########################
# EventBridge -> SFN Role
#########################

data "aws_iam_policy_document" "eventbridge_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eventbridge_role" {
  name               = "${local.orchestrator_name}-eventbridge-role"
  assume_role_policy = data.aws_iam_policy_document.eventbridge_assume_role.json
}

data "aws_iam_policy_document" "eventbridge_policy_doc" {
  statement {
    actions = [
      "states:StartExecution"   # Required so EventBridge can start Step Function
    ]
    resources = [
      aws_sfn_state_machine.orchestration.arn
    ]
  }
}

resource "aws_iam_policy" "eventbridge_policy" {
  name   = "${local.orchestrator_name}-eventbridge-policy"
  policy = data.aws_iam_policy_document.eventbridge_policy_doc.json
}

resource "aws_iam_role_policy_attachment" "eventbridge_attach" {
  role       = aws_iam_role.eventbridge_role.name
  policy_arn = aws_iam_policy.eventbridge_policy.arn
}

# Update your event target to use *this* new role
resource "aws_cloudwatch_event_target" "orchestration_target" {
  rule      = aws_cloudwatch_event_rule.orchestration_schedule.name
  arn       = aws_sfn_state_machine.orchestration.arn
  role_arn  = aws_iam_role.eventbridge_role.arn
}
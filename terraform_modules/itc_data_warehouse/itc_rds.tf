data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  aws_account_id           = data.aws_caller_identity.current.account_id
  region                   = data.aws_region.current.name
}

#############################
# DB Subnet Group
#############################
resource "aws_db_subnet_group" "itc_db_subnet_group" {
  name       = "${var.itc_database_prefix}-${var.env}-new-subnet-group"
  subnet_ids = var.subnet_ids  # This now references existing VPC subnets

  tags = {
    Name = "${var.itc_database_prefix}-new-subnet-group"
  }
}

#############################
# Secrets Manager: DB Credentials
#############################
resource "random_password" "db_password" {
  length  = 16
  special = true
}

resource "aws_secretsmanager_secret" "itc_database_secret" {
  name = var.secret_name
}

resource "aws_secretsmanager_secret_version" "itc_database_secret_version" {
  secret_id     = aws_secretsmanager_secret.itc_database_secret.id
  secret_string = jsonencode({
    username = var.db_username,
    password = random_password.db_password.result
  })
}

#############################
# Create a custom parameter group for logging
#############################
resource "aws_db_parameter_group" "itc_postgres_parameter_group" {
  name        = "${var.itc_database_prefix}-postgres-parameter-group"
  family      = "postgres16"  # Match your PostgreSQL version
  description = "Custom parameter group for PostgreSQL with logging enabled"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "0"  # Logs all queries; adjust as needed
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_error_verbosity"
    value = "default"  # Verbosity level: terse, default, or verbose
  }

  parameter {
    name  = "log_lock_waits"
    value = "1"  # Logs when queries wait on locks
  }

  tags = {
    Name = "${var.itc_database_prefix}-postgres-logs"
  }
}

#############################
# RDS PostgreSQL Instance
#############################
resource "aws_db_instance" "itc_postgres_instance" {
  identifier              = var.db_identifier
  engine                  = "postgres"
  engine_version          = "16.3"
  instance_class          = "db.t4g.micro"
  allocated_storage       = 20
  storage_type            = "gp2"  // General Purpose SSD
  publicly_accessible     = true
  multi_az                = false
  username                = var.db_username
  password                = random_password.db_password.result
  skip_final_snapshot     = true
  deletion_protection     = false


  # Attach the custom parameter group
  parameter_group_name    = aws_db_parameter_group.itc_postgres_parameter_group.name

  # Networking configuration
  vpc_security_group_ids  = [var.security_group_id]
  db_subnet_group_name    = aws_db_subnet_group.itc_db_subnet_group.name

  tags = {
    Name = var.db_identifier
  }
}

#############################
# Create IAM Role for Lambda
#############################
resource "aws_iam_role" "itc_lambda_postgres_role" {
  name = "${var.itc_database_prefix}-lambda-postgres-role"

  assume_role_policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  })
}

######################################
# Create Policy for Lambda's Role
######################################
resource "aws_iam_policy" "itc_lambda_postgres_policy" {
  name        = "${var.itc_database_prefix}-lambda-postgres-policy"
  description = "Policy for Lambda to access the PostgreSQL instance credentials and perform basic RDS actions."
  policy      = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ],
        "Resource": aws_secretsmanager_secret.itc_database_secret.arn
      },
      {
        "Effect": "Allow",
        "Action": [
          "rds:DescribeDBInstances"
        ],
        "Resource": "*"
      }
    ]
  })
}

#########################################################
# Attach the Policy and Permissions to Lambda's Role
#########################################################
resource "aws_iam_role_policy_attachment" "itc_lambda_postgres_policy_attachment" {
  role       = aws_iam_role.itc_lambda_postgres_role.name
  policy_arn = aws_iam_policy.itc_lambda_postgres_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.itc_lambda_postgres_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

#############################################
# Create one Security Group used by all Lambdas
#############################################
resource "aws_security_group" "shared_lambda_sg" {
  name        = "${var.itc_database_prefix}-shared-lambda-sg"
  description = "Shared Security Group for all Lambdas to access RDS/Secrets"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.itc_database_prefix}-shared-lambda-sg"
  }
}

#############################################
# Allow inbound from this SG to RDS
#############################################
resource "aws_security_group_rule" "allow_all_lambdas_rds" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = var.security_group_id        # <-- The existing RDS SG
  source_security_group_id = aws_security_group.shared_lambda_sg.id
  description              = "Allow all Lambdas to access RDS"
}

#############################################
# Allow inbound from this SG to Secrets Manager VPC endpoint
#############################################
resource "aws_security_group_rule" "allow_all_lambdas_secrets_manager" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  security_group_id        = var.vpc_endpoints_sg_id      # <-- The existing VPC Endpoint SG
  source_security_group_id = aws_security_group.shared_lambda_sg.id
  description              = "Allow all Lambdas to access Secrets Manager"
}

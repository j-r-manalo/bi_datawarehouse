terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = { # All resources should have environment and owner tags
      Environment = "beta" # sandbox, dev, staging, integ, prod
      Owner       = "Internal-Data-Science" # Who owns these resources
      Terraform   = true # Convenient to know what's terraformed specifically
    }
  }
}

terraform {
  backend "s3" {
    bucket         = "terraform-state-lock-itc-beta-841162693618"
    key            = "itc-beta.tfstate" # You may want a different state file for your project
    encrypt        = true
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock-itc-beta"
  }
}

# Variables to link modules
locals {
  database_prefix          = "invoice-transactions"
  env                      = "beta"
  source_env               = "demo"
  source_account           = "731876215943"
  region                   = "us-east-1"
  verifyplus_report_id     = "1000006"
  verifyplus_table_id      = "btzp5etbw"
  db_username              = "postgres"
  db_identifier            = "${local.database_prefix}-${local.env}-dw"
  secret_name              = "${local.database_prefix}-${local.env}-secret"
  skip_layer_lookup        = "false"
}

#########################################
# Modules                               #
#########################################

module "itc_vpc" {
  source                       = "../../terraform_modules/itc_vpc"
  itc_database_prefix          = local.database_prefix
  env                          = local.env
  region                       = local.region
  allowed_postgres_cidrs       = var.allowed_postgres_cidrs
}

module "itc_data_warehouse" {
  source = "../../terraform_modules/itc_data_warehouse"
  db_username              = local.db_username
  db_identifier            = local.db_identifier
  secret_name              = local.secret_name
  itc_database_prefix      = local.database_prefix
  env                      = local.env
  vpc_id                   = module.itc_vpc.itc_vpc_resources.itc_database_vpc_id
  subnet_ids               = module.itc_vpc.itc_vpc_resources.itc_database_vpc_subnet_ids
  security_group_id        = module.itc_vpc.itc_vpc_resources.itc_database_vpc_security_group_id
  vpc_endpoints_sg_id      = module.itc_vpc.itc_vpc_resources.vpc_endpoints_security_group_id
}

module "demand_pipeline_lambda" {
  source = "../../terraform_modules/demand_pipeline/"
  itc_database_prefix      = local.database_prefix
  lambda_handler           = "main.handler"
  env                      = local.env
  region                   = local.region
  skip_layer_lookup        = local.skip_layer_lookup
  source_env               = local.source_env
  source_account           = local.source_account

  # Pass VPC-related outputs
  vpc_id                   = module.itc_vpc.itc_vpc_resources.itc_database_vpc_id
  subnet_ids               = module.itc_vpc.itc_vpc_resources.itc_database_vpc_subnet_ids
  security_group_id        = module.itc_vpc.itc_vpc_resources.itc_database_vpc_security_group_id
  vpc_endpoints_sg_id      = module.itc_vpc.itc_vpc_resources.vpc_endpoints_security_group_id
  private_subnet_ids       = module.itc_vpc.itc_vpc_resources.private_subnet_ids

  # Pass the database outputs to the lambda module variables
  pg_endpoint              = module.itc_data_warehouse.itc_data_warehouse_resources.database_endpoint
  pg_secret_arn            = module.itc_data_warehouse.itc_data_warehouse_resources.database_secret_arn
  database_connect_arn     = module.itc_data_warehouse.itc_data_warehouse_resources.database_connect_arn
  shared_lambda_sg_id      = [module.itc_data_warehouse.itc_data_warehouse_resources.shared_lambda_sg_id]
}

module "verifyplus_pipeline_lambda" {
  source = "../../terraform_modules/verifyplus_pipeline/"
  itc_database_prefix      = local.database_prefix
  lambda_handler           = "main.handler"
  env                      = local.env
  region                   = local.region
  skip_layer_lookup        = local.skip_layer_lookup

  # Pass VPC-related outputs
  subnet_ids               = module.itc_vpc.itc_vpc_resources.itc_database_vpc_subnet_ids
  private_subnet_ids       = module.itc_vpc.itc_vpc_resources.private_subnet_ids

  # Pass the database outputs to the lambda module variables
  pg_endpoint              = module.itc_data_warehouse.itc_data_warehouse_resources.database_endpoint
  pg_secret_arn            = module.itc_data_warehouse.itc_data_warehouse_resources.database_secret_arn
  shared_lambda_sg_id      = [module.itc_data_warehouse.itc_data_warehouse_resources.shared_lambda_sg_id]
  quickbase_token          = var.quickbase_token
  report_id                = local.verifyplus_report_id
  table_id                 = local.verifyplus_table_id
}

module "orchestrator" {
  source = "../../terraform_modules/orchestrator"
  itc_database_prefix               = local.database_prefix
  env                               = local.env
  skip_layer_lookup                 = local.skip_layer_lookup
  orchestrator_cron_schedule        = "cron(25 15 * * ? *)" # Every day at TIME HERE

  # Pass VPC-related outputs
  vpc_id                   = module.itc_vpc.itc_vpc_resources.itc_database_vpc_id
  subnet_ids               = module.itc_vpc.itc_vpc_resources.itc_database_vpc_subnet_ids
  security_group_id        = module.itc_vpc.itc_vpc_resources.itc_database_vpc_security_group_id
  vpc_endpoints_sg_id      = module.itc_vpc.itc_vpc_resources.vpc_endpoints_security_group_id
  private_subnet_ids       = module.itc_vpc.itc_vpc_resources.private_subnet_ids

  # Pass the database outputs to the lambda module variables
  pg_endpoint              = module.itc_data_warehouse.itc_data_warehouse_resources.database_endpoint
  pg_secret_arn            = module.itc_data_warehouse.itc_data_warehouse_resources.database_secret_arn
  database_connect_arn     = module.itc_data_warehouse.itc_data_warehouse_resources.database_connect_arn
  shared_lambda_sg_id      = [module.itc_data_warehouse.itc_data_warehouse_resources.shared_lambda_sg_id]

  # The two pipeline Lambdas
  demand_pipeline_lambda_arn        = module.demand_pipeline_lambda.demand_pipeline_lambda_arn
  verifyplus_pipeline_lambda_arn    = module.verifyplus_pipeline_lambda.verifyplus_pipeline_lambda_arn
}
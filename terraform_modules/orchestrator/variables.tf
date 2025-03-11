variable "itc_database_prefix" {
  description = "The prefix to be used for naming database resources."
  type        = string
}

variable "env" {
  type    = string
  default = "beta"
}

variable "demand_pipeline_lambda_arn" {
  type = string
}

variable "verifyplus_pipeline_lambda_arn" {
  type = string
}

variable "pg_endpoint" {
  type = string
}

variable "pg_secret_arn" {
  type = string
}

variable "database_connect_arn" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_id" {
  type = string
}

variable "lambda_memory_size" {
  description = "Memory size for the Lambda function."
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout (in seconds) for the Lambda function."
  type        = number
  default     = 480
}

variable "local_mode" {
  description = "Tells lambda if it's in development mode or not."
  type        = string
  default     = "false"
}

variable "vpc_id" {
  description = "The VPC ID where the data warehouse will be deployed"
  type        = string
}

variable "vpc_endpoints_sg_id" {
  description = "The VPC endpoints for lambda to access secrets manager."
  type        = string
}

variable "orchestrator_cron_schedule" {
  description = "AWS region."
  type        = string
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs for Lambda VPC config"
}

variable "shared_lambda_sg_id" {
  type        = list(string)
  description = "Shared lambda security group ID"
}

variable "skip_layer_lookup" {
  description = "Skip the layer ARN lookup from Parameter Store for initial deployment."
  type        = string
  default     = "false"
}
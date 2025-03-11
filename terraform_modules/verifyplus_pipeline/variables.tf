variable "itc_database_prefix" {
  description = "Prefix used for naming resources."
  type        = string
}

variable "lambda_handler" {
  description = "The Lambda handler (e.g., main.handler)."
  type        = string
}

variable "lambda_memory_size" {
  description = "Memory size for the Lambda function."
  type        = number
  default     = 1024
}

variable "lambda_timeout" {
  description = "Timeout (in seconds) for the Lambda function."
  type        = number
  default     = 480
}

variable "subnet_ids" {
  description = "List of subnet IDs for the data warehouse"
  type        = list(string)
}

variable "xray_tracing_enabled" {
  description = "Flag to enable X-Ray tracing for the Lambda."
  type        = bool
  default     = false
}

variable "xray_tracing" {
  type        = object({
    enabled = bool,
    advanced = bool
  })
  default     = {
    enabled: true,
    advanced: false
  }
  description = "Whether to use X-Ray tracing for the Lambda, advanced tracing has a 5-10x latency hit"
}

variable "local_mode" {
  description = "Tells lambda if it's in development mode or not."
  type        = string
  default     = "false"
}

variable "env" {
  description = "The environment."
  type        = string
  default     = "beta"
}

variable "pg_endpoint" {
  description = "PostgreSQL host (from the database endpoint)."
  type        = string
}

variable "pg_secret_arn" {
  description = "ARN for the Secrets Manager secret containing the PG password."
  type        = string
}

# Define a sensitive variable for the Quickbase token.
variable "quickbase_token" {
  description = "The Quickbase API token"
  type        = string
  sensitive   = true
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs for Lambda VPC config"
}

variable "shared_lambda_sg_id" {
  type        = list(string)
  description = "Shared lambda security group ID"
}

variable "report_id" {
  description = "The report ID."
  type        = string
}

variable "table_id" {
  description = "The table ID."
  type        = string
}

variable "skip_layer_lookup" {
  description = "Skip the layer ARN lookup from Parameter Store for initial deployment."
  type        = string
  default     = "false"
}

variable "region" {
  description = "The region."
  type        = string
}

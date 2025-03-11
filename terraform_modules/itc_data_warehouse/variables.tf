variable "itc_database_prefix" {
  description = "The prefix to be used for naming database resources."
  type        = string
}

variable "db_username" {
  description = "The username for the PostgreSQL database."
  type        = string
  default     = "postgres"
}

variable "db_identifier" {
  description = "The identifier for the RDS instance."
  type        = string
}

variable "secret_name" {
  description = "The name for the Secrets Manager secret."
  type        = string
  default     = "invoice-transactions-beta-secret-1"
}

variable "vpc_id" {
  description = "The VPC ID where the data warehouse will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the data warehouse"
  type        = list(string)
}

variable "security_group_id" {
  description = "The security group to associate with the RDS instance"
  type        = string
}

variable "env" {
  description = "The environment."
  type        = string
  default     = "beta"
}

variable "vpc_endpoints_sg_id" {
  description = "The VPC endpoints for lambda to access secrets manager."
  type        = string
}
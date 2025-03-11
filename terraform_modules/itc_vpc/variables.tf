variable "itc_database_prefix" {
  description = "The prefix to be used for naming database resources."
  type        = string
}

variable "region" {
  description = "The region."
  type        = string
}

variable "vpc_endpoint_services" {
  type        = list(map(string))
  description = "AWS Services we need to create a VPC endpoint for."
  default     = [
    { "svc" : "lambda", "type" : "Interface" },
    { "svc" : "dynamodb", "type" : "Gateway" },
    { "svc" : "s3", "type" : "Gateway" }
  ]
}

# Public CIDR values manually assigned.
# Chosen not to match Exchange Prod CIDR values to avoid conflicts.
variable "public_subnet_cidrs" {
  type        = list(string)
  description = "Public Subnet CIDR values"
  default     = ["10.1.5.0/24", "10.1.6.0/24"]
}

variable "azs" {
  type        = list(string)
  description = "Availability Zones"
  default     = ["us-east-1a", "us-east-1b"]
}

variable "env" {
  description = "The environment."
  type        = string
  default     = "beta"
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "Private Subnet CIDR values. These are manually assigned and used for the data warehouse."
  default     = ["10.1.1.0/24", "10.1.2.0/24"]
}

variable "allowed_postgres_cidrs" {
  type        = list(string)
  description = "List of allowed CIDR blocks (i.e., IP addresses) for inbound PostgreSQL access."
}

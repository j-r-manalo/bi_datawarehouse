# Define a sensitive variable for the Quickbase token.
variable "quickbase_token" {
  description = "The Quickbase API token"
  type        = string
  sensitive   = true
}

# Define a list of allowed CIDRs (IP Addresses).
variable "allowed_postgres_cidrs" {
  type        = list(string)
  description = "List of allowed CIDRs for inbound PostgreSQL."
}
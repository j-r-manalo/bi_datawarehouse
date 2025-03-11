variable "cron_schedule" {
  description = "AWS region."
  type        = string
}

variable "demand_pipeline_lambda_name" {
  description = "The name of the Lambda function to schedule."
  type        = string
}

variable "demand_pipeline_lambda_arn" {
  description = "The ARN of the Lambda function to schedule."
  type        = string
}

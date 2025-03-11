variable "verifyplus_cron_schedule" {
  description = "AWS region."
  type        = string
}

variable "verifyplus_pipeline_lambda_name" {
  description = "The name of the Lambda function to schedule."
  type        = string
}

variable "verifyplus_pipeline_lambda_arn" {
  description = "The ARN of the Lambda function to schedule."
  type        = string
}

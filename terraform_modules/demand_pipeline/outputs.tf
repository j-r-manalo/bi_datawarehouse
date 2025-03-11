output "demand_pipeline_lambda_name" {
  description = "The name of the demand pipeline Lambda function."
  value       = aws_lambda_function.demand_pipeline_lambda.function_name
}

output "demand_pipeline_lambda_arn" {
  description = "The ARN of the demand pipeline Lambda function."
  value       = aws_lambda_function.demand_pipeline_lambda.arn
}
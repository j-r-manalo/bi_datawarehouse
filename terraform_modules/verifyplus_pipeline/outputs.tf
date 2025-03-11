output "verifyplus_pipeline_lambda_name" {
  description = "The name of the verifyplus pipeline Lambda function."
  value       = aws_lambda_function.verifyplus_pipeline_lambda.function_name
}

output "verifyplus_pipeline_lambda_arn" {
  description = "The ARN of the verifyplus pipeline Lambda function."
  value       = aws_lambda_function.verifyplus_pipeline_lambda.arn
}
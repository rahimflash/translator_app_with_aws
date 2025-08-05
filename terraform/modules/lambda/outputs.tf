output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.translation_function.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.translation_function.arn
}

output "lambda_function_invoke_arn" {
  description = "Lambda function invoke ARN"
  value       = aws_lambda_function.translation_function.invoke_arn
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}
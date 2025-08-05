output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint_url
}

output "api_key" {
  description = "API Gateway API Key"
  value       = module.api_gateway.api_key
  sensitive   = true
}

output "input_bucket_name" {
  description = "S3 input bucket name"
  value       = module.s3.input_bucket_name
}

output "output_bucket_name" {
  description = "S3 output bucket name"
  value       = module.s3.output_bucket_name
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = module.lambda.lambda_function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = module.lambda.lambda_function_arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = module.lambda.log_group_name
}

output "deployment_info" {
  description = "Deployment information"
  value = {
    environment  = var.environment
    region       = var.aws_region
    project_name = var.project_name
    deployed_at  = timestamp()
  }
}

# CLI configuration helper
output "cli_config_command" {
  description = "Command to configure CLI"
  value       = "python cli/translation_cli.py configure --endpoint ${module.api_gateway.api_endpoint_url} --api-key ${module.api_gateway.api_key} --output-bucket ${module.s3.output_bucket_name} --aws-region ${var.aws_region}"
  sensitive   = true
}
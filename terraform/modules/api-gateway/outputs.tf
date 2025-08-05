output "api_id" {
  description = "API Gateway REST API ID"
  value       = aws_api_gateway_rest_api.translation_api.id
}

output "api_name" {
  description = "API Gateway name"
  value       = aws_api_gateway_rest_api.translation_api.name
}

output "api_endpoint_url" {
  value = "${local.api_base_url}/translate"
}

output "api_key" {
  description = "API Gateway API Key"
  value       = aws_api_gateway_api_key.translation_api_key.value
  sensitive   = true
}

output "usage_plan_id" {
  description = "API Gateway usage plan ID"
  value       = aws_api_gateway_usage_plan.translation_usage_plan.id
}
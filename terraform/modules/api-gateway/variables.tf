variable "name_prefix" {
  description = "Name prefix for resources"
  type        = string
}

variable "lambda_function_arn" {
  description = "Lambda function ARN"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name"
  type        = string
}

variable "api_quota_limit" {
  description = "API quota limit per month"
  type        = number
  default     = 100000
}

variable "api_rate_limit" {
  description = "API rate limit per second"
  type        = number
  default     = 100
}

variable "api_burst_limit" {
  description = "API burst limit"
  type        = number
  default     = 200
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-1"
}
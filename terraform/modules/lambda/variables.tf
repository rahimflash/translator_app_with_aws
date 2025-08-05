variable "name_prefix" {
  description = "Name prefix for resources"
  type        = string
}

variable "lambda_role_arn" {
  description = "Lambda execution role ARN"
  type        = string
}

variable "input_bucket_name" {
  description = "Input S3 bucket name"
  type        = string
}

variable "output_bucket_name" {
  description = "Output S3 bucket name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 300
}

variable "memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.9"
}

variable "handler" {
  description = "Lambda handler"
  type        = string
  default     = "lambda_function.lambda_handler"
}
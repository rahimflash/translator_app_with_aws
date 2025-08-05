variable "name_prefix" {
  description = "Name prefix for resources"
  type        = string
}

variable "input_bucket_arn" {
  description = "Input S3 bucket ARN"
  type        = string
}

variable "output_bucket_arn" {
  description = "Output S3 bucket ARN"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
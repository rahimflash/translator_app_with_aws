terraform {
  required_version = ">= 1.3"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7.1"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.7.2"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Random suffix for unique resource names
resource "random_string" "resource_suffix" {
  length  = 4
  special = false
  upper   = false
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  default_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }

  common_tags = merge(local.default_tags, var.tags)

}

# IAM Module
module "iam" {
  source = "./modules/iam"

  name_prefix       = local.name_prefix
  input_bucket_arn  = module.s3.input_bucket_arn
  output_bucket_arn = module.s3.output_bucket_arn
  aws_region        = var.aws_region
  aws_account_id    = data.aws_caller_identity.current.account_id

  tags = local.common_tags
}

# S3 Module
module "s3" {
  source = "./modules/s3"

  name_prefix     = local.name_prefix
  resource_suffix = random_string.resource_suffix.result

  tags = local.common_tags
}

# Lambda Module
module "lambda" {
  source = "./modules/lambda"

  name_prefix        = local.name_prefix
  lambda_role_arn    = module.iam.lambda_role_arn
  input_bucket_name  = module.s3.input_bucket_name
  output_bucket_name = module.s3.output_bucket_name
  environment        = var.environment
  handler            = var.handler
  runtime            = var.runtime
  timeout            = var.lambda_timeout
  memory_size        = var.lambda_memory_size
  log_retention_days = var.log_retention_days

  tags = local.common_tags
}

# API Gateway Module
module "api_gateway" {
  source = "./modules/api-gateway"

  name_prefix          = local.name_prefix
  lambda_function_arn  = module.lambda.lambda_function_arn
  lambda_function_name = module.lambda.lambda_function_name
  api_quota_limit      = var.api_quota_limit
  api_rate_limit       = var.api_rate_limit
  api_burst_limit      = var.api_burst_limit
  environment          = var.environment

  tags = local.common_tags
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_error_rate" {
  alarm_name          = "${local.name_prefix}-lambda-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Lambda function error rate"

  dimensions = {
    FunctionName = module.lambda.lambda_function_name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "api_gateway_error_rate" {
  alarm_name          = "${local.name_prefix}-api-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = "60"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "API Gateway error rate"

  dimensions = {
    ApiName = module.api_gateway.api_name
  }

  tags = local.common_tags
}
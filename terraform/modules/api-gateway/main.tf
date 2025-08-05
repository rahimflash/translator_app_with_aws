locals {
  api_base_url = "https://${aws_api_gateway_rest_api.translation_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.translation_stage.stage_name}"
}

# API Gateway
resource "aws_api_gateway_rest_api" "translation_api" {
  name        = "${var.name_prefix}-api"
  description = "Translation Platform API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

# API Gateway Resource
resource "aws_api_gateway_resource" "translate_resource" {
  rest_api_id = aws_api_gateway_rest_api.translation_api.id
  parent_id   = aws_api_gateway_rest_api.translation_api.root_resource_id
  path_part   = "translate"
}

# Request Validator
resource "aws_api_gateway_request_validator" "translation_validator" {
  name                        = "translation-validator"
  rest_api_id                 = aws_api_gateway_rest_api.translation_api.id
  validate_request_body       = true
  validate_request_parameters = true
}

# Request Model
resource "aws_api_gateway_model" "translation_model" {
  rest_api_id  = aws_api_gateway_rest_api.translation_api.id
  name         = "TranslationRequest"
  content_type = "application/json"

  schema = jsonencode({
    "$schema" = "http://json-schema.org/draft-04/schema#"
    title     = "Translation Request Schema"
    type      = "object"
    required  = ["source_language", "target_languages", "sentences"]
    properties = {
      source_language = {
        type    = "string"
        pattern = "^[a-z]{2}$"
      }
      target_languages = {
        type = "array"
        items = {
          type    = "string"
          pattern = "^[a-z]{2}$"
        }
        minItems = 1
        maxItems = 10
      }
      sentences = {
        type = "array"
        items = {
          type      = "string"
          minLength = 1
          maxLength = 5000
        }
        minItems = 1
        maxItems = 100
      }
    }
  })
}

# POST Method
resource "aws_api_gateway_method" "translate_post" {
  rest_api_id      = aws_api_gateway_rest_api.translation_api.id
  resource_id      = aws_api_gateway_resource.translate_resource.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true

  request_validator_id = aws_api_gateway_request_validator.translation_validator.id

  request_models = {
    "application/json" = aws_api_gateway_model.translation_model.name
  }
}

# OPTIONS Method (CORS)
resource "aws_api_gateway_method" "translate_options" {
  rest_api_id   = aws_api_gateway_rest_api.translation_api.id
  resource_id   = aws_api_gateway_resource.translate_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Lambda Integration
resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.translation_api.id
  resource_id = aws_api_gateway_resource.translate_resource.id
  http_method = aws_api_gateway_method.translate_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  #   uri                     = var.lambda_function_arn
  uri = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${var.lambda_function_arn}/invocations"

}

# OPTIONS Integration (CORS)
resource "aws_api_gateway_integration" "translate_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.translation_api.id
  resource_id = aws_api_gateway_resource.translate_resource.id
  http_method = aws_api_gateway_method.translate_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# Method Responses
resource "aws_api_gateway_method_response" "translate_response_200" {
  rest_api_id = aws_api_gateway_rest_api.translation_api.id
  resource_id = aws_api_gateway_resource.translate_resource.id
  http_method = aws_api_gateway_method.translate_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "translate_options_200" {
  rest_api_id = aws_api_gateway_rest_api.translation_api.id
  resource_id = aws_api_gateway_resource.translate_resource.id
  http_method = aws_api_gateway_method.translate_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

# Integration Responses
resource "aws_api_gateway_integration_response" "translate_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.translation_api.id
  resource_id = aws_api_gateway_resource.translate_resource.id
  http_method = aws_api_gateway_method.translate_post.http_method
  status_code = aws_api_gateway_method_response.translate_response_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [aws_api_gateway_integration.lambda_integration]
}

resource "aws_api_gateway_integration_response" "translate_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.translation_api.id
  resource_id = aws_api_gateway_resource.translate_resource.id
  http_method = aws_api_gateway_method.translate_options.http_method
  status_code = aws_api_gateway_method_response.translate_options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  depends_on = [aws_api_gateway_integration.translate_options_integration]
}

# Lambda Permission
resource "aws_lambda_permission" "api_gateway_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.translation_api.execution_arn}/*/*"
}

# API Deployment
resource "aws_api_gateway_deployment" "translation_deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration,
    aws_api_gateway_integration.translate_options_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.translation_api.id
  #   stage_name  = var.environment

  lifecycle {
    create_before_destroy = true
  }

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.translate_resource.id,
      aws_api_gateway_method.translate_post.id,
      aws_api_gateway_integration.lambda_integration.id,
    ]))
  }
}

resource "aws_api_gateway_stage" "translation_stage" {
  stage_name    = var.environment
  rest_api_id   = aws_api_gateway_rest_api.translation_api.id
  deployment_id = aws_api_gateway_deployment.translation_deployment.id
  tags          = var.tags
}

# Usage Plan
resource "aws_api_gateway_usage_plan" "translation_usage_plan" {
  name = "${var.name_prefix}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.translation_api.id
    stage  = aws_api_gateway_stage.translation_stage.stage_name
  }

  quota_settings {
    limit  = var.api_quota_limit
    period = "MONTH"
  }

  throttle_settings {
    rate_limit  = var.api_rate_limit
    burst_limit = var.api_burst_limit
  }

  tags = var.tags
}

# API Key
resource "aws_api_gateway_api_key" "translation_api_key" {
  name = "${var.name_prefix}-api-key"
  tags = var.tags
}

resource "aws_api_gateway_usage_plan_key" "translation_usage_plan_key" {
  key_id        = aws_api_gateway_api_key.translation_api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.translation_usage_plan.id
}
# Lambda function code archive
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda_function.zip"
  source {
    content = templatefile("../../.${path.root}/lambda_code/lambda_function.py", {
      input_bucket  = var.input_bucket_name
      output_bucket = var.output_bucket_name
    })
    filename = "lambda_function.py"
  }
}

# Lambda function
resource "aws_lambda_function" "translation_function" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.name_prefix}-translator"
  role             = var.lambda_role_arn
  handler          = var.handler
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory_size

  environment {
    variables = {
      INPUT_BUCKET  = var.input_bucket_name
      OUTPUT_BUCKET = var.output_bucket_name
      ENVIRONMENT   = var.environment
    }
  }

  tags = var.tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.translation_function.function_name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}
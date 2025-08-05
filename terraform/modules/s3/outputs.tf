output "input_bucket_name" {
  description = "Input bucket name"
  value       = aws_s3_bucket.input_bucket.bucket
}

output "output_bucket_name" {
  description = "Output bucket name"
  value       = aws_s3_bucket.output_bucket.bucket
}

output "input_bucket_arn" {
  description = "Input bucket ARN"
  value       = aws_s3_bucket.input_bucket.arn
}

output "output_bucket_arn" {
  description = "Output bucket ARN"
  value       = aws_s3_bucket.output_bucket.arn
}
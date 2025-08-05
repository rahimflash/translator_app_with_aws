

data "aws_iam_policy_document" "tfstate_lock" {
  statement {
    actions = ["s3:PutObject"]
    principals {
      identifiers = ["*"]
      type        = "*"
    }
    resources = ["${module.state_bucket.s3_bucket_arn}/*"]
    condition {
      test     = "StringNotEquals"
      variable = "s3:x-amz-server-side-encryption"
      values   = ["AES256"]
    }
    effect = "Deny"
  }
}


# Lifecycle protection at the resource level using aws_s3_bucket_policy
resource "aws_s3_bucket_policy" "state_bucket_protection" {
  bucket = module.state_bucket.s3_bucket_id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyDeleteBucket"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:DeleteBucket"
        Resource  = module.state_bucket.s3_bucket_arn
      },
      {
        Sid       = "DenyUnencryptedUploads"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${module.state_bucket.s3_bucket_arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      }
    ]
  })
}
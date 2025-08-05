terraform {
  required_version = ">= 1.3"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Initial local backend (will be reconfigured)
  #   backend "local" {
  #     path = "temp-state/terraform.tfstate"
  #   }
}


provider "aws" {
  region = var.region
}


module "state_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 4.0"

  bucket        = "translator-tf-state-${data.aws_caller_identity.current.account_id}-${var.region}"
  force_destroy = false

  # Enable versioning to keep multiple versions of Lambda packages
  versioning = {
    enabled = true
  }

  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = var.tags
}
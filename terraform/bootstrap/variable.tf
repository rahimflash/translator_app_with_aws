variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
}
variable "name_prefix" {
  description = "Name prefix for resources"
  type        = string
}

variable "resource_suffix" {
  description = "Random suffix for unique names"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
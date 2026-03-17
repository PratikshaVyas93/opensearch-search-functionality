variable "collection_name" {
  description = "Name of the OpenSearch Serverless collection"
  type        = string
}

variable "env" {
  description = "Environment name (dev, stg, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "access_principal_arns" {
  description = "List of principal ARNs that can access the collection"
  type        = list(string)
}

variable "dashboard_user_arns" {
  description = "IAM user or role ARNs that need dashboard access (e.g. your console user)"
  type        = list(string)
  default     = []
}

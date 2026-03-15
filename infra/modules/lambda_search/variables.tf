variable "function_name" {
  description = "Name of the search Lambda function"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the IAM role for the Lambda function"
  type        = string
}

variable "opensearch_endpoint" {
  description = "Endpoint of the OpenSearch collection"
  type        = string
}

variable "region" {
  description = "AWS region"
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

variable "opensearch_layer_arn" {
  description = "ARN of the Lambda layer with OpenSearch dependencies"
  type        = string
}

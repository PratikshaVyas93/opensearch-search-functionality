variable "api_name" {
  description = "Name of the HTTP API"
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

variable "search_lambda_invoke_arn" {
  description = "Invoke ARN of the search Lambda function"
  type        = string
}

variable "search_lambda_function_name" {
  description = "Name of the search Lambda function"
  type        = string
}

variable "suggestions_lambda_invoke_arn" {
  description = "Invoke ARN of the suggestions Lambda function"
  type        = string
}

variable "suggestions_lambda_function_name" {
  description = "Name of the suggestions Lambda function"
  type        = string
}

variable "api_name" {
  description = "Name of the HTTP API"
  type        = string
}

variable "search_lambda_arn" {
  description = "ARN of the Search Lambda function"
  type        = string
}

variable "suggestions_lambda_arn" {
  description = "ARN of the Suggestions Lambda function"
  type        = string
}

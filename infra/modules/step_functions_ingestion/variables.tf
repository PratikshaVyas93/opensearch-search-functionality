variable "state_machine_name" {
  description = "Name of the Step Functions state machine"
  type        = string
}

variable "step_functions_role_arn" {
  description = "ARN of the IAM role for Step Functions"
  type        = string
}

variable "document_processor_lambda_arn" {
  description = "ARN of the document processor Lambda function"
  type        = string
}

variable "embedding_generator_lambda_arn" {
  description = "ARN of the embedding generator Lambda function"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket to monitor"
  type        = string
}

variable "eventbridge_role_arn" {
  description = "ARN of the IAM role for EventBridge"
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

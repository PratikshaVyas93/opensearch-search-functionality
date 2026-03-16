variable "state_machine_name" {
  description = "Name of the Step Functions state machine"
  type        = string
}

variable "step_functions_role_arn" {
  description = "ARN of the IAM role for Step Functions"
  type        = string
}

variable "indexer_lambda_arn" {
  description = "ARN of the indexer Lambda function"
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

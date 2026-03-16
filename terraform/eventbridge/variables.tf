variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket to listen for ObjectCreated events"
  type        = string
}

variable "indexer_lambda_arn" {
  description = "ARN of the Indexer Lambda function to invoke"
  type        = string
}

variable "state_machine_name" {
  description = "Name of the Step Functions state machine"
  type        = string
}

variable "rule_name" {
  description = "Name of the EventBridge rule"
  type        = string
}

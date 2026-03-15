variable "env" {
  description = "Environment name (dev, stg, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "opensearch_collection_arn" {
  description = "ARN of the OpenSearch collection"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 documents bucket"
  type        = string
}

variable "document_processor_lambda_arn" {
  description = "ARN of the document processor Lambda function"
  type        = string
  default     = ""
}

variable "embedding_generator_lambda_arn" {
  description = "ARN of the embedding generator Lambda function"
  type        = string
  default     = ""
}

variable "knowledge_base_name" {
  description = "Name of the Bedrock Knowledge Base"
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

variable "opensearch_collection_arn" {
  description = "ARN of the OpenSearch collection"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 documents bucket"
  type        = string
}


variable "bedrock_embedding_model_id" {
  description = "Bedrock embedding model ID for knowledge base"
  type        = string
  default     = "amazon.titan-embed-text-v1"
}

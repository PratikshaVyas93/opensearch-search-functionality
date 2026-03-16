variable "search_lambda_name" {
  description = "Name of the Search Lambda function"
  type        = string
}

variable "suggestions_lambda_name" {
  description = "Name of the Suggestions Lambda function"
  type        = string
}

variable "rag_lambda_name" {
  description = "Name of the RAG Lambda function"
  type        = string
}

variable "indexer_lambda_name" {
  description = "Name of the Indexer Lambda function"
  type        = string
}

variable "opensearch_endpoint" {
  description = "OpenSearch collection endpoint"
  type        = string
}

variable "opensearch_collection_arn" {
  description = "OpenSearch collection ARN"
  type        = string
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN for Indexer Lambda to read documents"
  type        = string
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for RAG Lambda"
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "rag_lambda_arn" {
  description = "ARN of the RAG Lambda function (for Search Lambda to invoke)"
  type        = string
  default     = ""
}

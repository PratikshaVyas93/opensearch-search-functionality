variable "knowledge_base_name" {
  description = "Name of the Bedrock Knowledge Base"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for source documents"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for source documents"
  type        = string
}

variable "opensearch_endpoint" {
  description = "OpenSearch Serverless collection endpoint"
  type        = string
}

variable "collection_arn" {
  description = "ARN of the OpenSearch Serverless collection"
  type        = string
}

variable "chunk_index_name" {
  description = "Name of the OpenSearch index for storing vector embeddings"
  type        = string
  default     = "chunk-index"
}

variable "embedding_model_arn" {
  description = "ARN of the Bedrock embedding model (Titan Embeddings)"
  type        = string
  default     = "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
}

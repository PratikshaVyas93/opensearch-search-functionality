# ============================================================================
# Infrastructure Outputs
# ============================================================================

output "s3_bucket_name" {
  description = "Name of the S3 documents bucket"
  value       = module.s3_documents.bucket_name
}

output "opensearch_endpoint" {
  description = "Endpoint of the OpenSearch collection"
  value       = module.opensearch_collection.collection_endpoint
}

output "opensearch_collection_name" {
  description = "Name of the OpenSearch collection"
  value       = module.opensearch_collection.collection_name
}

# ============================================================================
# Lambda Function Outputs
# ============================================================================

output "index_bootstrap_lambda_name" {
  description = "Name of the index bootstrap Lambda function"
  value       = module.src_bootstrap.lambda_function_name
}

output "search_lambda_name" {
  description = "Name of the search Lambda function"
  value       = module.src_search.lambda_function_name
}

output "suggestions_lambda_name" {
  description = "Name of the suggestions Lambda function"
  value       = module.src_suggestions.lambda_function_name
}

output "document_processor_lambda_name" {
  description = "Name of the document processor Lambda function"
  value       = module.src_processor.lambda_function_name
}

output "embedding_generator_lambda_name" {
  description = "Name of the embedding generator Lambda function"
  value       = module.src_embedding.lambda_function_name
}

# ============================================================================
# API Outputs
# ============================================================================

output "api_endpoint" {
  description = "HTTP API endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "search_endpoint" {
  description = "Search API endpoint"
  value       = module.api_gateway.search_endpoint
}

output "suggestions_endpoint" {
  description = "Suggestions API endpoint"
  value       = module.api_gateway.suggestions_endpoint
}

# ============================================================================
# Step Functions Outputs
# ============================================================================

output "state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  value       = module.step_functions_ingestion.state_machine_arn
}

output "state_machine_name" {
  description = "Name of the Step Functions state machine"
  value       = module.step_functions_ingestion.state_machine_name
}

# ============================================================================
# Bedrock Knowledge Base Outputs
# ============================================================================

output "knowledge_base_id" {
  description = "ID of the Bedrock Knowledge Base"
  value       = module.bedrock_knowledge_base.knowledge_base_id
}

output "knowledge_base_arn" {
  description = "ARN of the Bedrock Knowledge Base"
  value       = module.bedrock_knowledge_base.knowledge_base_arn
}

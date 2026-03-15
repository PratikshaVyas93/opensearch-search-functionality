output "index_bootstrap_lambda_role_arn" {
  description = "ARN of the index bootstrap Lambda role"
  value       = aws_iam_role.index_bootstrap_lambda_role.arn
}

output "search_lambda_role_arn" {
  description = "ARN of the search Lambda role"
  value       = aws_iam_role.search_lambda_role.arn
}

output "suggestions_lambda_role_arn" {
  description = "ARN of the suggestions Lambda role"
  value       = aws_iam_role.suggestions_lambda_role.arn
}

output "document_processor_lambda_role_arn" {
  description = "ARN of the document processor Lambda role"
  value       = aws_iam_role.document_processor_lambda_role.arn
}

output "embedding_generator_lambda_role_arn" {
  description = "ARN of the embedding generator Lambda role"
  value       = aws_iam_role.embedding_generator_lambda_role.arn
}

output "step_functions_ingestion_role_arn" {
  description = "ARN of the Step Functions ingestion role"
  value       = aws_iam_role.step_functions_ingestion_role.arn
}

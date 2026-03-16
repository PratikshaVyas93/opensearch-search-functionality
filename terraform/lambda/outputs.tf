output "search_lambda_arn" {
  description = "ARN of the Search Lambda function"
  value       = aws_lambda_function.search_lambda.arn
}

output "suggestions_lambda_arn" {
  description = "ARN of the Suggestions Lambda function"
  value       = aws_lambda_function.suggestions_lambda.arn
}

output "rag_lambda_arn" {
  description = "ARN of the RAG Lambda function"
  value       = aws_lambda_function.rag_lambda.arn
}

output "indexer_lambda_arn" {
  description = "ARN of the Indexer Lambda function"
  value       = aws_lambda_function.indexer_lambda.arn
}

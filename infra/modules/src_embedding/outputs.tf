output "lambda_arn" {
  description = "ARN of the embedding generator Lambda function"
  value       = aws_lambda_function.embedding_generator.arn
}

output "lambda_function_name" {
  description = "Name of the embedding generator Lambda function"
  value       = aws_lambda_function.embedding_generator.function_name
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of the embedding generator Lambda function"
  value       = aws_lambda_function.embedding_generator.invoke_arn
}

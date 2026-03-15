output "lambda_arn" {
  description = "ARN of the index bootstrap Lambda function"
  value       = aws_lambda_function.index_bootstrap.arn
}

output "lambda_function_name" {
  description = "Name of the index bootstrap Lambda function"
  value       = aws_lambda_function.index_bootstrap.function_name
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of the index bootstrap Lambda function"
  value       = aws_lambda_function.index_bootstrap.invoke_arn
}

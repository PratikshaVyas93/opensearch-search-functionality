output "lambda_arn" {
  description = "ARN of the search Lambda function"
  value       = aws_lambda_function.search.arn
}

output "lambda_function_name" {
  description = "Name of the search Lambda function"
  value       = aws_lambda_function.search.function_name
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of the search Lambda function"
  value       = aws_lambda_function.search.invoke_arn
}

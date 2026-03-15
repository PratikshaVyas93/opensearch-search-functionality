output "lambda_arn" {
  description = "ARN of the suggestions Lambda function"
  value       = aws_lambda_function.suggestions.arn
}

output "lambda_function_name" {
  description = "Name of the suggestions Lambda function"
  value       = aws_lambda_function.suggestions.function_name
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of the suggestions Lambda function"
  value       = aws_lambda_function.suggestions.invoke_arn
}

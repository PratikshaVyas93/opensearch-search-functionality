output "lambda_arn" {
  description = "ARN of the document processor Lambda function"
  value       = aws_lambda_function.processor.arn
}

output "lambda_function_name" {
  description = "Name of the document processor Lambda function"
  value       = aws_lambda_function.processor.function_name
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of the document processor Lambda function"
  value       = aws_lambda_function.processor.invoke_arn
}

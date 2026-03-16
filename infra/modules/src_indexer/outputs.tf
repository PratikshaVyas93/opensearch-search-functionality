output "lambda_arn" {
  value = aws_lambda_function.indexer.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.indexer.function_name
}

output "lambda_invoke_arn" {
  value = aws_lambda_function.indexer.invoke_arn
}

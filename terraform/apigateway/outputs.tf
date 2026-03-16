output "api_endpoint_url" {
  description = "The endpoint URL of the HTTP API"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

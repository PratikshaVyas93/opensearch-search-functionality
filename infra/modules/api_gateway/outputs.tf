output "api_endpoint" {
  description = "HTTP API endpoint URL"
  value       = aws_apigatewayv2_stage.this.invoke_url
}

output "api_id" {
  description = "HTTP API ID"
  value       = aws_apigatewayv2_api.this.id
}

output "search_endpoint" {
  description = "Search API endpoint"
  value       = "${aws_apigatewayv2_stage.this.invoke_url}/search"
}

output "suggestions_endpoint" {
  description = "Suggestions API endpoint"
  value       = "${aws_apigatewayv2_stage.this.invoke_url}/suggestions"
}

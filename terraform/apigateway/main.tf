# HTTP API
resource "aws_apigatewayv2_api" "this" {
  name          = var.api_name
  protocol_type = "HTTP"
}

# Integration for Search Lambda (POST /search)
resource "aws_apigatewayv2_integration" "search_lambda" {
  api_id           = aws_apigatewayv2_api.this.id
  integration_type = "AWS_PROXY"
  integration_method = "POST"
  payload_format_version = "2.0"
  target = "arn:aws:apigatewayv2:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${var.search_lambda_arn}/invocations"
}

# Integration for Suggestions Lambda (GET /suggestions)
resource "aws_apigatewayv2_integration" "suggestions_lambda" {
  api_id           = aws_apigatewayv2_api.this.id
  integration_type = "AWS_PROXY"
  integration_method = "POST"
  payload_format_version = "2.0"
  target = "arn:aws:apigatewayv2:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${var.suggestions_lambda_arn}/invocations"
}

# Route for POST /search
resource "aws_apigatewayv2_route" "search" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /search"
  target    = "integrations/${aws_apigatewayv2_integration.search_lambda.id}"
}

# Route for GET /suggestions
resource "aws_apigatewayv2_route" "suggestions" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "GET /suggestions"
  target    = "integrations/${aws_apigatewayv2_integration.suggestions_lambda.id}"
}

# Stage with auto-deploy
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true
}

# Lambda permission for Search Lambda
resource "aws_lambda_permission" "search_lambda_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.search_lambda_arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

# Lambda permission for Suggestions Lambda
resource "aws_lambda_permission" "suggestions_lambda_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.suggestions_lambda_arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

# Data source to get current AWS region
data "aws_region" "current" {}

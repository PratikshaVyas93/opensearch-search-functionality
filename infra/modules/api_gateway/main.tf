# API Gateway Module - HTTP API for search and suggestions
# Provides REST endpoints for document search and autocomplete suggestions

# Create HTTP API
resource "aws_apigatewayv2_api" "this" {
  name          = var.api_name
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["*"]
  }

  tags = {
    Name        = var.api_name
    Environment = var.env
    Project     = var.project_name
  }
}

# Create API stage
resource "aws_apigatewayv2_stage" "this" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = var.env
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format          = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  tags = {
    Name        = "${var.api_name}-${var.env}"
    Environment = var.env
    Project     = var.project_name
  }
}

# CloudWatch log group for API logs
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.api_name}"
  retention_in_days = 7

  tags = {
    Name        = "${var.api_name}-logs"
    Environment = var.env
    Project     = var.project_name
  }
}

# ============================================================================
# Search Lambda Integration
# ============================================================================

# Create integration for search Lambda
resource "aws_apigatewayv2_integration" "search_lambda" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  payload_format_version = "2.0"
  target                 = var.search_lambda_invoke_arn
}

# Create /search route
resource "aws_apigatewayv2_route" "search" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /search"
  target    = "integrations/${aws_apigatewayv2_integration.search_lambda.id}"
}

# Grant API Gateway permission to invoke search Lambda
resource "aws_lambda_permission" "search_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.search_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

# ============================================================================
# Suggestions Lambda Integration
# ============================================================================

# Create integration for suggestions Lambda
resource "aws_apigatewayv2_integration" "suggestions_lambda" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  payload_format_version = "2.0"
  target                 = var.suggestions_lambda_invoke_arn
}

# Create /suggestions route
resource "aws_apigatewayv2_route" "suggestions" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "GET /suggestions"
  target    = "integrations/${aws_apigatewayv2_integration.suggestions_lambda.id}"
}

# Grant API Gateway permission to invoke suggestions Lambda
resource "aws_lambda_permission" "suggestions_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.suggestions_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

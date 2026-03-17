# Suggestions Lambda Module - Provides autocomplete suggestions
# Queries suggestions index for prefix-based autocomplete

# Archive the Lambda function code
data "archive_file" "suggestions_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../../../src/suggestions/index.py"
  output_path = "${path.module}/.terraform/suggestions_lambda.zip"
}

# Create the Lambda function
resource "aws_lambda_function" "suggestions" {
  filename         = data.archive_file.suggestions_lambda_zip.output_path
  function_name    = var.function_name
  role             = var.lambda_role_arn
  handler          = "index.handler"
  runtime          = "python3.13"
  source_code_hash = data.archive_file.suggestions_lambda_zip.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = var.opensearch_endpoint
      REGION              = var.region
    }
  }

  layers = [var.opensearch_layer_arn]

  tags = {
    Name        = var.function_name
    Environment = var.env
    Project     = var.project_name
  }

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  depends_on = [
    data.archive_file.suggestions_lambda_zip
  ]
}

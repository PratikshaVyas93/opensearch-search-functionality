# Search Lambda Module - Searches documents in OpenSearch
# Provides search API for metadata and vector indexes

# Archive the Lambda function code
data "archive_file" "search_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../../lambda/search/index.py"
  output_path = "${path.module}/.terraform/search_lambda.zip"
}

# Create the Lambda function
resource "aws_lambda_function" "search" {
  filename         = data.archive_file.search_lambda_zip.output_path
  function_name    = var.function_name
  role             = var.lambda_role_arn
  handler          = "index.handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.search_lambda_zip.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = var.opensearch_endpoint
      AWS_REGION          = var.region
    }
  }

  layers = [var.opensearch_layer_arn]

  tags = {
    Name        = var.function_name
    Environment = var.env
    Project     = var.project_name
  }

  depends_on = [
    data.archive_file.search_lambda_zip
  ]
}

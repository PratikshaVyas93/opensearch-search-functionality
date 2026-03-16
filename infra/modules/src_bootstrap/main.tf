# Index Bootstrap Lambda Module - Creates OpenSearch indexes
# Bootstraps metadata, vector, and suggestions indexes on deployment

# Archive the Lambda function code
data "archive_file" "index_bootstrap_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../../../src/bootstrap/index.py"
  output_path = "${path.module}/.terraform/index_bootstrap_lambda.zip"
}

# Create the Lambda function
resource "aws_lambda_function" "index_bootstrap" {
  filename         = data.archive_file.index_bootstrap_lambda_zip.output_path
  function_name    = var.function_name
  role             = var.lambda_role_arn
  handler          = "index.handler"
  runtime          = "python3.13"
  source_code_hash = data.archive_file.index_bootstrap_lambda_zip.output_base64sha256
  timeout          = 60

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
    data.archive_file.index_bootstrap_lambda_zip
  ]
}

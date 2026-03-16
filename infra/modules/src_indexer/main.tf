data "archive_file" "indexer_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../../../src/indexer/index.py"
  output_path = "${path.module}/.terraform/indexer_lambda.zip"
}

resource "aws_lambda_function" "indexer" {
  filename         = data.archive_file.indexer_lambda_zip.output_path
  function_name    = var.function_name
  role             = var.lambda_role_arn
  handler          = "index.handler"
  runtime          = "python3.13"
  source_code_hash = data.archive_file.indexer_lambda_zip.output_base64sha256
  timeout          = 60

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
}

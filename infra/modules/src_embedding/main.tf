# Embedding Generator Lambda Module - Generates embeddings and indexes documents
# Calls Bedrock Titan Embeddings model and writes to OpenSearch indexes

# Archive the Lambda function code
data "archive_file" "embedding_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../../../src/embedding/index.py"
  output_path = "${path.module}/.terraform/embedding_lambda.zip"
}

# Create the Lambda function
resource "aws_lambda_function" "embedding_generator" {
  filename         = data.archive_file.embedding_lambda_zip.output_path
  function_name    = var.function_name
  role             = var.lambda_role_arn
  handler          = "index.handler"
  runtime          = "python3.13"
  source_code_hash = data.archive_file.embedding_lambda_zip.output_base64sha256
  timeout          = 120

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = var.opensearch_endpoint
      AWS_REGION          = var.region
      BEDROCK_MODEL_ID    = var.bedrock_model_id
    }
  }

  layers = [var.opensearch_layer_arn]

  tags = {
    Name        = var.function_name
    Environment = var.env
    Project     = var.project_name
  }

  depends_on = [
    data.archive_file.embedding_lambda_zip
  ]
}

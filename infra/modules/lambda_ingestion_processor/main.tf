# Document Processor Lambda Module - Processes documents from S3
# Extracts text content and metadata from uploaded documents

# Archive the Lambda function code
data "archive_file" "processor_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../../lambda/processor/index.py"
  output_path = "${path.module}/.terraform/processor_lambda.zip"
}

# Create the Lambda function
resource "aws_lambda_function" "processor" {
  filename         = data.archive_file.processor_lambda_zip.output_path
  function_name    = var.function_name
  role             = var.lambda_role_arn
  handler          = "index.handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.processor_lambda_zip.output_base64sha256
  timeout          = 60

  tags = {
    Name        = var.function_name
    Environment = var.env
    Project     = var.project_name
  }

  depends_on = [
    data.archive_file.processor_lambda_zip
  ]
}

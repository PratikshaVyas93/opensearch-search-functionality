# Archive files for Lambda function code
data "archive_file" "search_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/search/index.py"
  output_path = "${path.module}/.terraform/search_lambda.zip"
}

data "archive_file" "suggestions_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/suggestions/index.py"
  output_path = "${path.module}/.terraform/suggestions_lambda.zip"
}

data "archive_file" "rag_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/rag/index.py"
  output_path = "${path.module}/.terraform/rag_lambda.zip"
}

data "archive_file" "indexer_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/indexer/index.py"
  output_path = "${path.module}/.terraform/indexer_lambda.zip"
}

# Trust policy for Lambda service
data "aws_iam_policy_document" "lambda_trust_policy" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

# ============================================================================
# Search Lambda
# ============================================================================

resource "aws_iam_role" "search_lambda_role" {
  name               = "${var.search_lambda_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
}

resource "aws_iam_role_policy" "search_lambda_policy" {
  name   = "${var.search_lambda_name}-policy"
  role   = aws_iam_role.search_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:*"
        ]
        Resource = var.opensearch_collection_arn
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = var.rag_lambda_arn != "" ? var.rag_lambda_arn : "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "search_lambda_logs" {
  name   = "${var.search_lambda_name}-logs-policy"
  role   = aws_iam_role.search_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_lambda_function" "search_lambda" {
  filename         = data.archive_file.search_lambda_zip.output_path
  function_name    = var.search_lambda_name
  role             = aws_iam_role.search_lambda_role.arn
  handler          = "index.handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.search_lambda_zip.output_base64sha256

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = var.opensearch_endpoint
      RAG_LAMBDA_ARN      = var.rag_lambda_arn
    }
  }

  depends_on = [aws_iam_role_policy.search_lambda_policy, aws_iam_role_policy.search_lambda_logs]
}

# ============================================================================
# Suggestions Lambda
# ============================================================================

resource "aws_iam_role" "suggestions_lambda_role" {
  name               = "${var.suggestions_lambda_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
}

resource "aws_iam_role_policy" "suggestions_lambda_policy" {
  name   = "${var.suggestions_lambda_name}-policy"
  role   = aws_iam_role.suggestions_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:*"
        ]
        Resource = var.opensearch_collection_arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "suggestions_lambda_logs" {
  name   = "${var.suggestions_lambda_name}-logs-policy"
  role   = aws_iam_role.suggestions_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_lambda_function" "suggestions_lambda" {
  filename         = data.archive_file.suggestions_lambda_zip.output_path
  function_name    = var.suggestions_lambda_name
  role             = aws_iam_role.suggestions_lambda_role.arn
  handler          = "index.handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.suggestions_lambda_zip.output_base64sha256

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = var.opensearch_endpoint
    }
  }

  depends_on = [aws_iam_role_policy.suggestions_lambda_policy, aws_iam_role_policy.suggestions_lambda_logs]
}

# ============================================================================
# RAG Lambda
# ============================================================================

resource "aws_iam_role" "rag_lambda_role" {
  name               = "${var.rag_lambda_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
}

resource "aws_iam_role_policy" "rag_lambda_policy" {
  name   = "${var.rag_lambda_name}-policy"
  role   = aws_iam_role.rag_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeAgent"
        ]
        Resource = "arn:aws:bedrock:*:*:agent/*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "rag_lambda_logs" {
  name   = "${var.rag_lambda_name}-logs-policy"
  role   = aws_iam_role.rag_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "arn:aws:bedrock:*:*:foundation-model/*"
      }
    ]
  })
}

resource "aws_lambda_function" "rag_lambda" {
  filename         = data.archive_file.rag_lambda_zip.output_path
  function_name    = var.rag_lambda_name
  role             = aws_iam_role.rag_lambda_role.arn
  handler          = "index.handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.rag_lambda_zip.output_base64sha256

  environment {
    variables = {
      BEDROCK_MODEL_ID = var.bedrock_model_id
    }
  }

  depends_on = [aws_iam_role_policy.rag_lambda_policy, aws_iam_role_policy.rag_lambda_logs]
}

# ============================================================================
# Indexer Lambda
# ============================================================================

resource "aws_iam_role" "indexer_lambda_role" {
  name               = "${var.indexer_lambda_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
}

resource "aws_iam_role_policy" "indexer_lambda_policy" {
  name   = "${var.indexer_lambda_name}-policy"
  role   = aws_iam_role.indexer_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:*"
        ]
        Resource = var.opensearch_collection_arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "indexer_lambda_logs" {
  name   = "${var.indexer_lambda_name}-logs-policy"
  role   = aws_iam_role.indexer_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]
        Resource = "${var.s3_bucket_arn}/*"
      }
    ]
  })
}

resource "aws_lambda_function" "indexer_lambda" {
  filename         = data.archive_file.indexer_lambda_zip.output_path
  function_name    = var.indexer_lambda_name
  role             = aws_iam_role.indexer_lambda_role.arn
  handler          = "index.handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.indexer_lambda_zip.output_base64sha256

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = var.opensearch_endpoint
    }
  }

  depends_on = [aws_iam_role_policy.indexer_lambda_policy, aws_iam_role_policy.indexer_lambda_logs]
}

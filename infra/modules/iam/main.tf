# IAM Module - Roles and Policies for Document Search Platform
# Provides least-privilege IAM roles for all Lambda functions and services

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

# Trust policy for Step Functions service
data "aws_iam_policy_document" "step_functions_trust_policy" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# ============================================================================
# Index Bootstrap Lambda Role
# ============================================================================

resource "aws_iam_role" "index_bootstrap_lambda_role" {
  name               = "${var.env}-${var.project_name}-index-bootstrap-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json

  tags = {
    Name        = "${var.env}-${var.project_name}-index-bootstrap-role"
    Environment = var.env
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy" "index_bootstrap_lambda_policy" {
  name = "${var.env}-${var.project_name}-index-bootstrap-policy"
  role = aws_iam_role.index_bootstrap_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "OpenSearchAccess"
        Effect = "Allow"
        Action = ["aoss:APIAccessAll"]
        Resource = var.opensearch_collection_arn
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# ============================================================================
# Search Lambda Role
# ============================================================================

resource "aws_iam_role" "search_lambda_role" {
  name               = "${var.env}-${var.project_name}-search-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json

  tags = {
    Name        = "${var.env}-${var.project_name}-search-role"
    Environment = var.env
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy" "search_lambda_policy" {
  name = "${var.env}-${var.project_name}-search-policy"
  role = aws_iam_role.search_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "OpenSearchAccess"
        Effect = "Allow"
        Action = ["aoss:APIAccessAll"]
        Resource = var.opensearch_collection_arn
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# ============================================================================
# Suggestions Lambda Role
# ============================================================================

resource "aws_iam_role" "suggestions_lambda_role" {
  name               = "${var.env}-${var.project_name}-suggestions-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json

  tags = {
    Name        = "${var.env}-${var.project_name}-suggestions-role"
    Environment = var.env
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy" "suggestions_lambda_policy" {
  name = "${var.env}-${var.project_name}-suggestions-policy"
  role = aws_iam_role.suggestions_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "OpenSearchAccess"
        Effect = "Allow"
        Action = ["aoss:APIAccessAll"]
        Resource = var.opensearch_collection_arn
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# ============================================================================
# Document Processor Lambda Role
# ============================================================================

resource "aws_iam_role" "document_processor_lambda_role" {
  name               = "${var.env}-${var.project_name}-processor-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json

  tags = {
    Name        = "${var.env}-${var.project_name}-processor-role"
    Environment = var.env
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy" "document_processor_lambda_policy" {
  name = "${var.env}-${var.project_name}-processor-policy"
  role = aws_iam_role.document_processor_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]
        Resource = "${var.s3_bucket_arn}/*"
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# ============================================================================
# Embedding Generator Lambda Role
# ============================================================================

resource "aws_iam_role" "embedding_generator_lambda_role" {
  name               = "${var.env}-${var.project_name}-embedding-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json

  tags = {
    Name        = "${var.env}-${var.project_name}-embedding-role"
    Environment = var.env
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy" "embedding_generator_lambda_policy" {
  name = "${var.env}-${var.project_name}-embedding-policy"
  role = aws_iam_role.embedding_generator_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "OpenSearchAccess"
        Effect = "Allow"
        Action = ["aoss:APIAccessAll"]
        Resource = var.opensearch_collection_arn
      },
      {
        Sid    = "BedrockAccess"
        Effect = "Allow"
        Action = ["bedrock:InvokeModel"]
        Resource = "arn:aws:bedrock:${var.region}::foundation-model/amazon.titan-embed-text-v1"
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# ============================================================================
# Step Functions Ingestion Role
# ============================================================================

resource "aws_iam_role" "step_functions_ingestion_role" {
  name               = "${var.env}-${var.project_name}-step-functions-role"
  assume_role_policy = data.aws_iam_policy_document.step_functions_trust_policy.json

  tags = {
    Name        = "${var.env}-${var.project_name}-step-functions-role"
    Environment = var.env
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy" "step_functions_ingestion_policy" {
  name = "${var.env}-${var.project_name}-step-functions-policy"
  role = aws_iam_role.step_functions_ingestion_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "InvokeLambdas"
        Effect = "Allow"
        Action = ["lambda:InvokeFunction"]
        Resource = [
          var.document_processor_lambda_arn,
          var.embedding_generator_lambda_arn
        ]
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

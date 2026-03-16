# IAM Module - Roles and Policies for Document Search Platform
# Provides least-privilege IAM roles for all Lambda functions and services

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "lambda_trust_policy" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "step_functions_trust_policy" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

# Index Bootstrap Lambda Role
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
  name   = "${var.env}-${var.project_name}-index-bootstrap-policy"
  role   = aws_iam_role.index_bootstrap_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "OpenSearchAccess"
        Effect   = "Allow"
        Action   = ["aoss:APIAccessAll"]
        Resource = var.opensearch_collection_arn
      },
      {
        Sid      = "CloudWatchLogs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# Search Lambda Role
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
  name   = "${var.env}-${var.project_name}-search-policy"
  role   = aws_iam_role.search_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "OpenSearchAccess"
        Effect   = "Allow"
        Action   = ["aoss:APIAccessAll"]
        Resource = var.opensearch_collection_arn
      },
      {
        Sid      = "CloudWatchLogs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# Suggestions Lambda Role
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
  name   = "${var.env}-${var.project_name}-suggestions-policy"
  role   = aws_iam_role.suggestions_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "OpenSearchAccess"
        Effect   = "Allow"
        Action   = ["aoss:APIAccessAll"]
        Resource = var.opensearch_collection_arn
      },
      {
        Sid      = "CloudWatchLogs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# Metadata/Suggestions Indexer Lambda Role
# Replaces: document_processor_lambda_role + embedding_generator_lambda_role
# Bedrock KB handles embeddings — this role only needs S3 read + OpenSearch write
resource "aws_iam_role" "indexer_lambda_role" {
  name               = "${var.env}-${var.project_name}-indexer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
  tags = {
    Name        = "${var.env}-${var.project_name}-indexer-role"
    Environment = var.env
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy" "indexer_lambda_policy" {
  name   = "${var.env}-${var.project_name}-indexer-policy"
  role   = aws_iam_role.indexer_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "S3ReadJSON"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:GetObjectVersion"]
        Resource = "${var.s3_bucket_arn}/*"
      },
      {
        Sid      = "OpenSearchWrite"
        Effect   = "Allow"
        Action   = ["aoss:APIAccessAll"]
        Resource = var.opensearch_collection_arn
      },
      {
        Sid      = "CloudWatchLogs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# Step Functions Ingestion Role
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
  name   = "${var.env}-${var.project_name}-step-functions-policy"
  role   = aws_iam_role.step_functions_ingestion_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "InvokeLambdas"
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = "*"
      },
      {
        Sid      = "CloudWatchLogs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

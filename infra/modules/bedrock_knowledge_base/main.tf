# Bedrock Knowledge Base Module - RAG knowledge base for document retrieval
# Integrates with OpenSearch vector store and S3 data source

# Create IAM role for Bedrock Knowledge Base
data "aws_iam_policy_document" "bedrock_kb_trust_policy" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "bedrock_kb_role" {
  name               = "${var.env}-${var.project_name}-bedrock-kb-role"
  assume_role_policy = data.aws_iam_policy_document.bedrock_kb_trust_policy.json

  tags = {
    Name        = "${var.env}-${var.project_name}-bedrock-kb-role"
    Environment = var.env
    Project     = var.project_name
  }
}

# IAM policy for Bedrock Knowledge Base
resource "aws_iam_role_policy" "bedrock_kb_policy" {
  name   = "${var.env}-${var.project_name}-bedrock-kb-policy"
  role   = aws_iam_role.bedrock_kb_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      },
      {
        Sid    = "OpenSearchAccess"
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = var.opensearch_collection_arn
      },
      {
        Sid    = "BedrockEmbeddings"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "arn:aws:bedrock:${data.aws_caller_identity.current.region}::foundation-model/amazon.titan-embed-text-v1"
      }
    ]
  })
}

# Create Bedrock Knowledge Base
resource "aws_bedrock_knowledge_base" "this" {
  name            = var.knowledge_base_name
  role_arn        = aws_iam_role.bedrock_kb_role.arn
  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${data.aws_caller_identity.current.region}::foundation-model/amazon.titan-embed-text-v1"
    }
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"
    opensearch_serverless_configuration {
      collection_arn = var.opensearch_collection_arn
      vector_index_name = "vector-index"
      field_mapping {
        vector_field = "embedding"
        text_field = "text"
        metadata_field = "metadata"
      }
    }
  }

  tags = {
    Name        = var.knowledge_base_name
    Environment = var.env
    Project     = var.project_name
  }

  depends_on = [
    aws_iam_role_policy.bedrock_kb_policy
  ]
}

# Create data source for S3
resource "aws_bedrock_data_source" "s3" {
  knowledge_base_id = aws_bedrock_knowledge_base.this.id
  name              = "${var.env}-${var.project_name}-s3-source"
  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn = var.s3_bucket_arn
    }
  }

  depends_on = [
    aws_bedrock_knowledge_base.this
  ]
}

# Data source for current AWS account and region
data "aws_caller_identity" "current" {}

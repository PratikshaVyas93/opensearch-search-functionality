# OpenSearch Collection Module - Serverless vector search collection
# Provides OpenSearch Serverless collection with encryption, network, and access policies

# Encryption policy for the collection
resource "aws_opensearchserverless_security_policy" "encryption" {
  name        = "${var.env}-${var.project_name}-enc"
  type        = "encryption"
  description = "AWS-owned KMS encryption policy for ${var.collection_name}"

  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection"
        Resource     = ["collection/${var.collection_name}"]
      }
    ]
    AWSOwnedKey = true
  })
}

# Network policy for public access
resource "aws_opensearchserverless_security_policy" "network" {
  name        = "${var.env}-${var.project_name}-net"
  type        = "network"
  description = "Public network access policy for ${var.collection_name}"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource     = ["collection/${var.collection_name}"]
        },
        {
          ResourceType = "dashboard"
          Resource     = ["collection/${var.collection_name}"]
        }
      ]
      AllowFromPublic = true
    }
  ])
}

# Data access policy for Lambda functions and services
resource "aws_opensearchserverless_access_policy" "this" {
  name        = "${var.env}-${var.project_name}-data"
  type        = "data"
  description = "Data access policy for ${var.collection_name}"

  policy = jsonencode(concat(
    [
      {
        Rules = [
          {
            ResourceType = "collection"
            Resource     = ["collection/${var.collection_name}"]
            Permission   = ["aoss:*"]
          },
          {
            ResourceType = "index"
            Resource     = ["index/${var.collection_name}/*"]
            Permission   = ["aoss:*"]
          }
        ]
        Principal = var.access_principal_arns
      }
    ],
    length(var.dashboard_user_arns) > 0 ? [
      {
        Rules = [
          {
            ResourceType = "collection"
            Resource     = ["collection/${var.collection_name}"]
            Permission   = ["aoss:*"]
          },
          {
            ResourceType = "index"
            Resource     = ["index/${var.collection_name}/*"]
            Permission   = ["aoss:*"]
          }
        ]
        Principal = var.dashboard_user_arns
      }
    ] : []
  ))
}

# OpenSearch Serverless collection for vector search
resource "aws_opensearchserverless_collection" "this" {
  name = var.collection_name
  type = "VECTORSEARCH"

  tags = {
    Name        = var.collection_name
    Environment = var.env
    Project     = var.project_name
  }

  lifecycle {
    ignore_changes = all
  }

  depends_on = [
    aws_opensearchserverless_security_policy.encryption,
    aws_opensearchserverless_security_policy.network,
    aws_opensearchserverless_access_policy.this,
  ]
}

# GitHub OIDC Provider and IAM Role for RAG Pipeline Deployment
# This module sets up secure authentication for GitHub Actions without storing AWS credentials

# Data source to get the OIDC provider
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

# IAM role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name               = "github-actions-rag-pipeline-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "github-actions-rag-pipeline"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# IAM policy for GitHub Actions to deploy RAG pipeline
resource "aws_iam_role_policy" "github_actions_policy" {
  name   = "github-actions-rag-pipeline-policy"
  role   = aws_iam_role.github_actions.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # S3 permissions for state and document storage
      {
        Effect = "Allow"
        Action = [
          "s3:CreateBucket",
          "s3:DeleteBucket",
          "s3:GetBucketVersioning",
          "s3:PutBucketVersioning",
          "s3:GetBucketPolicy",
          "s3:PutBucketPolicy",
          "s3:DeleteBucketPolicy",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketPublicAccessBlock",
          "s3:PutBucketPublicAccessBlock",
          "s3:GetBucketTagging",
          "s3:PutBucketTagging"
        ]
        Resource = "*"
      },
      # DynamoDB permissions for state locking
      {
        Effect = "Allow"
        Action = [
          "dynamodb:CreateTable",
          "dynamodb:DeleteTable",
          "dynamodb:DescribeTable",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:UpdateItem",
          "dynamodb:ListTables",
          "dynamodb:TagResource",
          "dynamodb:UntagResource"
        ]
        Resource = "*"
      },
      # OpenSearch Serverless permissions
      {
        Effect = "Allow"
        Action = [
          "aoss:CreateCollection",
          "aoss:DeleteCollection",
          "aoss:DescribeCollection",
          "aoss:ListCollections",
          "aoss:UpdateCollection",
          "aoss:CreateAccessPolicy",
          "aoss:DeleteAccessPolicy",
          "aoss:GetAccessPolicy",
          "aoss:ListAccessPolicies",
          "aoss:UpdateAccessPolicy",
          "aoss:CreateSecurityPolicy",
          "aoss:DeleteSecurityPolicy",
          "aoss:GetSecurityPolicy",
          "aoss:ListSecurityPolicies",
          "aoss:UpdateSecurityPolicy",
          "aoss:CreateEncryptionPolicy",
          "aoss:DeleteEncryptionPolicy",
          "aoss:GetEncryptionPolicy",
          "aoss:ListEncryptionPolicies",
          "aoss:UpdateEncryptionPolicy"
        ]
        Resource = "*"
      },
      # Bedrock permissions
      {
        Effect = "Allow"
        Action = [
          "bedrock:CreateKnowledgeBase",
          "bedrock:DeleteKnowledgeBase",
          "bedrock:DescribeKnowledgeBase",
          "bedrock:ListKnowledgeBases",
          "bedrock:UpdateKnowledgeBase",
          "bedrock:CreateDataSource",
          "bedrock:DeleteDataSource",
          "bedrock:DescribeDataSource",
          "bedrock:ListDataSources",
          "bedrock:UpdateDataSource",
          "bedrock:InvokeAgent",
          "bedrock:InvokeModel"
        ]
        Resource = "*"
      },
      # EventBridge permissions
      {
        Effect = "Allow"
        Action = [
          "events:CreateRule",
          "events:DeleteRule",
          "events:DescribeRule",
          "events:ListRules",
          "events:PutRule",
          "events:PutTargets",
          "events:RemoveTargets",
          "events:ListTargetsByRule"
        ]
        Resource = "*"
      },
      # Step Functions permissions
      {
        Effect = "Allow"
        Action = [
          "states:CreateStateMachine",
          "states:DeleteStateMachine",
          "states:DescribeStateMachine",
          "states:ListStateMachines",
          "states:UpdateStateMachine",
          "states:StartExecution",
          "states:DescribeExecution",
          "states:ListExecutions"
        ]
        Resource = "*"
      },
      # Lambda permissions
      {
        Effect = "Allow"
        Action = [
          "lambda:CreateFunction",
          "lambda:DeleteFunction",
          "lambda:GetFunction",
          "lambda:ListFunctions",
          "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration",
          "lambda:AddPermission",
          "lambda:RemovePermission",
          "lambda:GetPolicy",
          "lambda:InvokeFunction",
          "lambda:CreateEventSourceMapping",
          "lambda:DeleteEventSourceMapping",
          "lambda:ListEventSourceMappings"
        ]
        Resource = "*"
      },
      # API Gateway permissions
      {
        Effect = "Allow"
        Action = [
          "apigateway:*"
        ]
        Resource = "*"
      },
      # IAM permissions for creating roles and policies
      {
        Effect = "Allow"
        Action = [
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:GetRole",
          "iam:ListRoles",
          "iam:UpdateAssumeRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:GetRolePolicy",
          "iam:ListRolePolicies",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:ListAttachedRolePolicies",
          "iam:PassRole",
          "iam:TagRole",
          "iam:UntagRole",
          "iam:ListRoleTags",
          "iam:CreatePolicy",
          "iam:DeletePolicy",
          "iam:GetPolicy",
          "iam:GetPolicyVersion",
          "iam:ListPolicies",
          "iam:ListPolicyVersions",
          "iam:CreatePolicyVersion",
          "iam:DeletePolicyVersion"
        ]
        Resource = "*"
      },
      # CloudWatch permissions for logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:DeleteLogGroup",
          "logs:DescribeLogGroups",
          "logs:ListLogGroups",
          "logs:CreateLogStream",
          "logs:DeleteLogStream",
          "logs:DescribeLogStreams",
          "logs:PutLogEvents",
          "logs:GetLogEvents"
        ]
        Resource = "*"
      },
      # KMS permissions for encryption
      {
        Effect = "Allow"
        Action = [
          "kms:CreateKey",
          "kms:DeleteKey",
          "kms:DescribeKey",
          "kms:ListKeys",
          "kms:ListAliases",
          "kms:CreateAlias",
          "kms:DeleteAlias",
          "kms:UpdateAlias",
          "kms:GetKeyPolicy",
          "kms:PutKeyPolicy",
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      },
      # CloudFormation permissions (if needed)
      {
        Effect = "Allow"
        Action = [
          "cloudformation:DescribeStacks",
          "cloudformation:ListStacks"
        ]
        Resource = "*"
      }
    ]
  })
}

# Output the role ARN for GitHub secrets
output "github_actions_role_arn" {
  value       = aws_iam_role.github_actions.arn
  description = "ARN to use in GitHub secrets as AWS_ROLE_ARN"
}

output "github_actions_role_name" {
  value       = aws_iam_role.github_actions.name
  description = "Name of the GitHub Actions IAM role"
}

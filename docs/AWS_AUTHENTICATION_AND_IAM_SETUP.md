# AWS Authentication and IAM Setup Guide

## Part 1: GitHub Actions OIDC Authentication Setup

### Why OIDC Instead of Access Keys?

The current workflow uses **OIDC (OpenID Connect)** for authentication, which is more secure than storing AWS access keys because:

- ✅ **No long-lived credentials** stored in GitHub secrets
- ✅ **Temporary credentials** generated per workflow run
- ✅ **Automatic credential rotation** - credentials expire after workflow completes
- ✅ **Audit trail** - AWS CloudTrail logs which GitHub workflow assumed the role
- ✅ **Least privilege** - role can be scoped to specific repositories/branches

### Step 1: Create an IAM OIDC Provider in AWS

Run these AWS CLI commands to set up the GitHub OIDC provider:

```bash
# Create the OIDC provider (one-time setup)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

**Expected output**: You'll get a provider ARN like `arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com`

### Step 2: Create an IAM Role for GitHub Actions

Create a file `github-actions-role.tf` in your Terraform root:

```hcl
# Data source to get the OIDC provider
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

# IAM role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name = "github-actions-rag-pipeline-role"

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
            "token.actions.githubusercontent.com:sub" = "repo:YOUR_GITHUB_ORG/YOUR_REPO:*"
          }
        }
      }
    ]
  })
}

# Attach policies to the role (see Part 2 below for detailed permissions)
resource "aws_iam_role_policy" "github_actions_policy" {
  name = "github-actions-rag-pipeline-policy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:*",
          "dynamodb:*",
          "opensearchserverless:*",
          "bedrock:*",
          "events:*",
          "states:*",
          "lambda:*",
          "apigateway:*",
          "iam:PassRole",
          "iam:CreateRole",
          "iam:PutRolePolicy",
          "iam:GetRole",
          "iam:GetRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:DeleteRole",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:GetPolicy",
          "iam:GetPolicyVersion",
          "iam:ListPolicies",
          "iam:ListPolicyVersions",
          "iam:CreatePolicy",
          "iam:DeletePolicy",
          "iam:TagRole",
          "iam:UntagRole",
          "iam:ListRoleTags",
          "cloudwatch:*",
          "logs:*",
          "kms:*"
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
```

### Step 3: Add the Role ARN to GitHub Secrets

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Create a new secret named `AWS_ROLE_ARN`
4. Paste the role ARN from Terraform output

### Step 4: Update GitHub Actions Workflow

The workflow already has the correct configuration:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: ${{ env.AWS_REGION }}
```

This will:
1. Use GitHub's OIDC token to assume the IAM role
2. Get temporary credentials valid for 1 hour
3. Automatically clean up after workflow completes

---

## Part 2: IAM Permissions Audit and Fixes

### Current IAM Roles Analysis

#### ✅ **Bedrock Knowledge Base Role** - SUFFICIENT

**Permissions**:
- `s3:GetObject` - Read documents from S3 ✓
- `s3:ListBucket` - List S3 bucket contents ✓
- `aoss:APIAccessAll` - Full access to OpenSearch collection ✓

**Status**: All required permissions present.

---

#### ✅ **EventBridge Role** - SUFFICIENT

**Permissions**:
- `states:StartExecution` - Invoke Step Functions state machine ✓

**Status**: All required permissions present.

---

#### ✅ **Step Functions Role** - SUFFICIENT

**Permissions**:
- `lambda:InvokeFunction` - Invoke Indexer Lambda ✓

**Status**: All required permissions present.

---

#### ⚠️ **Search Lambda Role** - NEEDS FIX

**Current Permissions**:
- `aoss:*` - Full OpenSearch access ✓
- `lambda:InvokeFunction` - Invoke RAG Lambda ✓

**Missing Permissions**:
- ❌ `logs:CreateLogGroup` - Create CloudWatch log groups
- ❌ `logs:CreateLogStream` - Create log streams
- ❌ `logs:PutLogEvents` - Write logs

**Fix**: Add CloudWatch Logs permissions

```hcl
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
```

---

#### ⚠️ **Suggestions Lambda Role** - NEEDS FIX

**Current Permissions**:
- `aoss:*` - Full OpenSearch access ✓

**Missing Permissions**:
- ❌ `logs:CreateLogGroup` - Create CloudWatch log groups
- ❌ `logs:CreateLogStream` - Create log streams
- ❌ `logs:PutLogEvents` - Write logs

**Fix**: Add CloudWatch Logs permissions

```hcl
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
```

---

#### ⚠️ **RAG Lambda Role** - NEEDS FIXES

**Current Permissions**:
- `bedrock:InvokeAgent` - Invoke Bedrock Agent Runtime ✓

**Missing Permissions**:
- ❌ `logs:CreateLogGroup` - Create CloudWatch log groups
- ❌ `logs:CreateLogStream` - Create log streams
- ❌ `logs:PutLogEvents` - Write logs
- ❌ `bedrock:InvokeModel` - Invoke embedding models (if needed)

**Fix**: Add CloudWatch Logs and additional Bedrock permissions

```hcl
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
```

---

#### ⚠️ **Indexer Lambda Role** - NEEDS FIX

**Current Permissions**:
- `aoss:*` - Full OpenSearch access ✓

**Missing Permissions**:
- ❌ `logs:CreateLogGroup` - Create CloudWatch log groups
- ❌ `logs:CreateLogStream` - Create log streams
- ❌ `logs:PutLogEvents` - Write logs
- ❌ `s3:GetObject` - Read S3 event details (optional but recommended)

**Fix**: Add CloudWatch Logs and S3 read permissions

```hcl
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
```

---

### Summary of Required Changes

| Component | Issue | Fix |
|-----------|-------|-----|
| Search Lambda | Missing CloudWatch Logs | Add logs policy |
| Suggestions Lambda | Missing CloudWatch Logs | Add logs policy |
| RAG Lambda | Missing CloudWatch Logs + Bedrock InvokeModel | Add logs + bedrock policy |
| Indexer Lambda | Missing CloudWatch Logs + S3 read | Add logs + s3 policy |
| GitHub Actions | Needs OIDC setup | Create IAM role + add to secrets |

---

## Implementation Steps

### 1. Update Lambda Module

Add the missing IAM policies to `terraform/lambda/main.tf`:

```hcl
# Add after search_lambda_policy definition
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

# Similar additions for suggestions_lambda_logs, rag_lambda_logs, indexer_lambda_logs
```

### 2. Set Up GitHub OIDC

Run the AWS CLI command to create the OIDC provider (one-time setup).

### 3. Create GitHub Actions IAM Role

Apply the `github-actions-role.tf` Terraform configuration.

### 4. Add Role ARN to GitHub Secrets

Store the role ARN in GitHub repository secrets.

### 5. Deploy

The workflow will now use OIDC authentication without storing any AWS credentials.

---

## Verification

After setup, verify everything works:

```bash
# Check OIDC provider exists
aws iam list-open-id-connect-providers

# Check GitHub Actions role
aws iam get-role --role-name github-actions-rag-pipeline-role

# Run a test workflow dispatch
# The workflow should authenticate without any stored credentials
```

---

## Security Best Practices

1. **Scope the OIDC role** to specific repositories/branches:
   ```
   repo:YOUR_ORG/YOUR_REPO:ref:refs/heads/main
   ```

2. **Use least privilege** - Only grant permissions needed for deployment

3. **Rotate credentials** - OIDC tokens expire after 1 hour automatically

4. **Monitor access** - Check CloudTrail for role assumption events

5. **Audit logs** - Review Lambda CloudWatch logs for any errors


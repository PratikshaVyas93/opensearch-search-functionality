# GitHub Secrets Setup Guide

This guide explains how to set up AWS credentials as GitHub secrets for the RAG Pipeline deployment workflow.

## Prerequisites

- AWS account with appropriate permissions
- GitHub repository access
- AWS IAM user with programmatic access

## Step 1: Create AWS IAM User (if not already created)

1. Go to AWS Console → IAM → Users
2. Click "Create user"
3. Enter username (e.g., `github-rag-pipeline`)
4. Click "Next"
5. Select "Attach policies directly"
6. Search for and attach these policies:
   - `AmazonS3FullAccess`
   - `AmazonDynamoDBFullAccess`
   - `AmazonOpenSearchServiceFullAccess`
   - `AmazonBedrockFullAccess`
   - `AWSLambdaFullAccess`
   - `IAMFullAccess`
   - `AmazonEventBridgeFullAccess`
   - `AWSStepFunctionsFullAccess`
   - `APIGatewayAdministrator`
   - `CloudWatchLogsFullAccess`
7. Click "Next" → "Create user"

## Step 2: Generate Access Keys

1. Go to AWS Console → IAM → Users
2. Click on the user you created
3. Go to "Security credentials" tab
4. Scroll to "Access keys" section
5. Click "Create access key"
6. Select "Command Line Interface (CLI)"
7. Check the acknowledgment box
8. Click "Create access key"
9. Copy the Access Key ID and Secret Access Key
   - **Important**: Save these securely. You won't be able to see the secret key again.

## Step 3: Add GitHub Secrets

### Method 1: Via GitHub Web UI

1. Go to your GitHub repository
2. Click "Settings" (top right)
3. In left sidebar, click "Secrets and variables" → "Actions"
4. Click "New repository secret"
5. Create first secret:
   - **Name**: `AWS_ACCESS_KEY_ID`
   - **Value**: Paste your AWS Access Key ID
   - Click "Add secret"
6. Click "New repository secret" again
7. Create second secret:
   - **Name**: `AWS_SECRET_ACCESS_KEY`
   - **Value**: Paste your AWS Secret Access Key
   - Click "Add secret"

### Method 2: Via GitHub CLI

```bash
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Login to GitHub
gh auth login

# Add AWS_ACCESS_KEY_ID secret
gh secret set AWS_ACCESS_KEY_ID --body "YOUR_ACCESS_KEY_ID"

# Add AWS_SECRET_ACCESS_KEY secret
gh secret set AWS_SECRET_ACCESS_KEY --body "YOUR_SECRET_ACCESS_KEY"

# Verify secrets are set
gh secret list
```

## Step 4: Verify Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. You should see both secrets listed:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
3. Secrets are masked and cannot be viewed after creation

## Step 5: Test Deployment

1. Go to repository → Actions tab
2. Select "Deploy RAG Pipeline Infrastructure" workflow
3. Click "Run workflow"
4. Select environment (dev/staging/prod)
5. Select branch (main)
6. Click "Run workflow"
7. Monitor the workflow execution

## Security Best Practices

### ✅ DO:
- Use a dedicated IAM user for GitHub Actions
- Rotate access keys regularly (every 90 days)
- Use least-privilege IAM policies
- Store access keys securely
- Monitor IAM user activity in CloudTrail
- Use environment-specific credentials if possible

### ❌ DON'T:
- Commit credentials to repository
- Share access keys with team members
- Use root AWS account credentials
- Reuse credentials across multiple services
- Leave old access keys active

## Rotating Access Keys

To rotate access keys:

1. Create new access key in AWS IAM
2. Update GitHub secrets with new credentials
3. Test deployment with new credentials
4. Delete old access key from AWS IAM
5. Document the rotation date

## Troubleshooting

### Issue: "Unable to locate credentials"

**Solution**:
1. Verify secrets are named exactly: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
2. Check that secrets are set in the correct repository (not organization level)
3. Verify IAM user has active access keys

### Issue: "Access Denied" errors during deployment

**Solution**:
1. Verify IAM user has all required policies attached
2. Check AWS region is correct (default: us-east-1)
3. Verify IAM user has permissions for all services used

### Issue: Secrets not visible in workflow

**Solution**:
1. Secrets are automatically available to all workflows in the repository
2. Secrets are masked in logs (shown as `***`)
3. Verify workflow file references correct secret names

## Cleanup

To remove secrets:

1. Go to repository Settings → Secrets and variables → Actions
2. Click the secret you want to delete
3. Click "Delete"
4. Confirm deletion

## Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS Access Keys Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

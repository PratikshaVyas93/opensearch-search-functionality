# Quick Start: Security Setup for RAG Pipeline

## TL;DR - 3 Steps to Secure Deployment

### Step 1: Create OIDC Provider (One-time AWS Setup)

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### Step 2: Deploy GitHub Actions IAM Role

```bash
cd terraform/github-oidc
terraform init
terraform apply \
  -var="github_org=YOUR_ORG" \
  -var="github_repo=YOUR_REPO" \
  -var="environment=dev"
```

Copy the output `github_actions_role_arn`.

### Step 3: Add Role ARN to GitHub Secrets

1. Go to: `https://github.com/YOUR_ORG/YOUR_REPO/settings/secrets/actions`
2. Click "New repository secret"
3. Name: `AWS_ROLE_ARN`
4. Value: Paste the role ARN from Step 2
5. Click "Add secret"

**Done!** Your workflow now authenticates securely without storing AWS credentials.

---

## What Was Fixed?

### ✅ Authentication
- **Before**: Would need AWS access keys stored in GitHub secrets (insecure)
- **After**: Uses OIDC with temporary credentials (secure)

### ✅ Lambda Permissions
- **Before**: Missing CloudWatch Logs, S3, and Bedrock permissions
- **After**: All Lambda functions have complete permissions

| Component | Fixed |
|-----------|-------|
| Search Lambda | ✅ Added CloudWatch Logs |
| Suggestions Lambda | ✅ Added CloudWatch Logs |
| RAG Lambda | ✅ Added CloudWatch Logs + Bedrock InvokeModel |
| Indexer Lambda | ✅ Added CloudWatch Logs + S3 read |

---

## How It Works

### OIDC Authentication Flow

```
1. GitHub Actions workflow starts
   ↓
2. Workflow requests OIDC token from GitHub
   ↓
3. GitHub provides OIDC token (valid for 1 hour)
   ↓
4. Workflow exchanges OIDC token for AWS credentials
   ↓
5. AWS verifies token signature and trust relationship
   ↓
6. AWS returns temporary credentials (valid for 1 hour)
   ↓
7. Workflow uses temporary credentials to deploy
   ↓
8. Credentials automatically expire after workflow completes
```

**Key Benefits**:
- ✅ No long-lived credentials stored
- ✅ Automatic credential rotation
- ✅ Full audit trail in CloudTrail
- ✅ Least privilege access

---

## Verification

### Check OIDC Provider

```bash
aws iam list-open-id-connect-providers
```

Should show: `arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com`

### Check GitHub Actions Role

```bash
aws iam get-role --role-name github-actions-rag-pipeline-role
```

Should show the role with OIDC trust relationship.

### Check GitHub Secret

```bash
# In GitHub UI, verify AWS_ROLE_ARN secret exists
# (You can't view the value, only confirm it exists)
```

### Test Workflow

Push code to trigger the workflow. It should:
1. Authenticate using OIDC (no credentials needed)
2. Deploy infrastructure
3. Complete successfully

---

## Troubleshooting

### Error: "User is not authorized to perform: sts:AssumeRoleWithWebIdentity"

**Cause**: OIDC provider not created or role trust policy incorrect.

**Fix**:
```bash
# Verify OIDC provider exists
aws iam list-open-id-connect-providers

# If not, create it
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### Error: "Role ARN not found in GitHub secrets"

**Cause**: `AWS_ROLE_ARN` secret not added to GitHub.

**Fix**:
1. Go to GitHub repository settings
2. Secrets and variables → Actions
3. Add new secret `AWS_ROLE_ARN` with the role ARN

### Error: "Lambda logs not appearing in CloudWatch"

**Cause**: Lambda missing CloudWatch Logs permissions.

**Fix**: Already fixed in updated `terraform/lambda/main.tf`. Re-apply:
```bash
cd terraform/lambda
terraform apply
```

### Error: "Indexer Lambda can't read S3 events"

**Cause**: Lambda missing S3 read permissions.

**Fix**: Already fixed in updated `terraform/lambda/main.tf`. Re-apply:
```bash
cd terraform/lambda
terraform apply
```

---

## Security Best Practices

### ✅ Do's

- ✅ Use OIDC for GitHub Actions authentication
- ✅ Scope OIDC role to specific repositories
- ✅ Use least privilege IAM policies
- ✅ Rotate credentials regularly (automatic with OIDC)
- ✅ Monitor CloudTrail for role assumption
- ✅ Review Lambda CloudWatch logs regularly

### ❌ Don'ts

- ❌ Don't store AWS access keys in GitHub secrets
- ❌ Don't use overly permissive IAM policies
- ❌ Don't share AWS credentials between projects
- ❌ Don't commit credentials to version control
- ❌ Don't use root AWS account credentials

---

## Files Created/Updated

### New Files
- `terraform/github-oidc/main.tf` - OIDC provider and IAM role
- `terraform/github-oidc/variables.tf` - Variables for OIDC module
- `scripts/setup-github-oidc.sh` - Automated setup script
- `docs/AWS_AUTHENTICATION_AND_IAM_SETUP.md` - Detailed setup guide
- `docs/SECURITY_FIXES_SUMMARY.md` - Summary of all fixes
- `docs/QUICK_START_SECURITY.md` - This file

### Updated Files
- `terraform/lambda/main.tf` - Added missing IAM policies
- `terraform/lambda/variables.tf` - Added s3_bucket_arn variable
- `.github/workflows/deploy.yml` - Already configured for OIDC

---

## Next Steps

1. **Run setup script** (optional, automated):
   ```bash
   bash scripts/setup-github-oidc.sh
   ```

2. **Or manually**:
   - Create OIDC provider (Step 1 above)
   - Deploy Terraform module (Step 2 above)
   - Add secret to GitHub (Step 3 above)

3. **Deploy infrastructure**:
   ```bash
   git push origin main
   # Workflow will run and deploy using OIDC authentication
   ```

4. **Monitor deployment**:
   - Check GitHub Actions workflow logs
   - Verify resources created in AWS Console
   - Check CloudWatch Logs for Lambda execution

---

## Additional Resources

- [GitHub OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [AWS IAM OIDC Providers](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc.html)
- [AWS CloudTrail Logging](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/)
- [Lambda Execution Role Permissions](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)

---

## Summary

✅ **Authentication**: Secure OIDC-based authentication without storing credentials
✅ **Permissions**: All Lambda functions have complete IAM permissions
✅ **Automation**: Setup script for easy deployment
✅ **Documentation**: Comprehensive guides for setup and troubleshooting

Your RAG pipeline infrastructure is now ready for secure deployment! 🚀

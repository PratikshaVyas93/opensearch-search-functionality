# Security Fixes Summary

## Issues Identified and Fixed

### 1. AWS Authentication Method ✅ DOCUMENTED

**Issue**: How does the workflow authenticate without AWS access keys?

**Solution**: Uses **GitHub OIDC (OpenID Connect)**
- No long-lived credentials stored in secrets
- Temporary credentials generated per workflow run
- Automatic credential rotation (1-hour expiry)
- Full audit trail in CloudTrail

**Setup Required**:
1. Create OIDC provider in AWS (one-time)
2. Create IAM role for GitHub Actions
3. Store role ARN in GitHub secrets
4. Workflow uses OIDC token to assume role

See `docs/AWS_AUTHENTICATION_AND_IAM_SETUP.md` for detailed setup instructions.

---

### 2. Lambda IAM Permissions ✅ FIXED

**Issues Found**:

| Lambda | Missing Permissions | Status |
|--------|-------------------|--------|
| Search Lambda | CloudWatch Logs | ✅ FIXED |
| Suggestions Lambda | CloudWatch Logs | ✅ FIXED |
| RAG Lambda | CloudWatch Logs + Bedrock InvokeModel | ✅ FIXED |
| Indexer Lambda | CloudWatch Logs + S3 read | ✅ FIXED |

**Changes Made**:

#### Search Lambda
```hcl
# Added logs policy
- logs:CreateLogGroup
- logs:CreateLogStream
- logs:PutLogEvents
```

#### Suggestions Lambda
```hcl
# Added logs policy
- logs:CreateLogGroup
- logs:CreateLogStream
- logs:PutLogEvents
```

#### RAG Lambda
```hcl
# Added logs policy
- logs:CreateLogGroup
- logs:CreateLogStream
- logs:PutLogEvents

# Added Bedrock model invocation
- bedrock:InvokeModel (on foundation-model/*)
```

#### Indexer Lambda
```hcl
# Added logs policy
- logs:CreateLogGroup
- logs:CreateLogStream
- logs:PutLogEvents

# Added S3 read permissions
- s3:GetObject
- s3:GetObjectVersion
```

---

## IAM Permissions Audit Results

### ✅ Bedrock Knowledge Base Role - SUFFICIENT
- ✓ S3 read access (GetObject, ListBucket)
- ✓ OpenSearch write access (aoss:APIAccessAll)

### ✅ EventBridge Role - SUFFICIENT
- ✓ Step Functions invocation (states:StartExecution)

### ✅ Step Functions Role - SUFFICIENT
- ✓ Lambda invocation (lambda:InvokeFunction)

### ✅ Search Lambda Role - NOW SUFFICIENT
- ✓ OpenSearch access (aoss:*)
- ✓ RAG Lambda invocation (lambda:InvokeFunction)
- ✓ CloudWatch Logs (NEW)

### ✅ Suggestions Lambda Role - NOW SUFFICIENT
- ✓ OpenSearch access (aoss:*)
- ✓ CloudWatch Logs (NEW)

### ✅ RAG Lambda Role - NOW SUFFICIENT
- ✓ Bedrock Agent invocation (bedrock:InvokeAgent)
- ✓ Bedrock model invocation (bedrock:InvokeModel) (NEW)
- ✓ CloudWatch Logs (NEW)

### ✅ Indexer Lambda Role - NOW SUFFICIENT
- ✓ OpenSearch write access (aoss:*)
- ✓ S3 read access (s3:GetObject, s3:GetObjectVersion) (NEW)
- ✓ CloudWatch Logs (NEW)

---

## Files Updated

1. **terraform/lambda/main.tf**
   - Added CloudWatch Logs policies for all 4 Lambda functions
   - Added Bedrock InvokeModel permission for RAG Lambda
   - Added S3 read permissions for Indexer Lambda
   - Updated depends_on to include new policies

2. **terraform/lambda/variables.tf**
   - Added `s3_bucket_arn` variable for Indexer Lambda

3. **docs/AWS_AUTHENTICATION_AND_IAM_SETUP.md** (NEW)
   - Complete OIDC setup guide
   - IAM permissions audit
   - Implementation steps
   - Security best practices

4. **docs/SECURITY_FIXES_SUMMARY.md** (NEW)
   - This file - summary of all fixes

---

## Deployment Instructions

### Step 1: Set Up GitHub OIDC (One-time)

```bash
# Create OIDC provider
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### Step 2: Create GitHub Actions IAM Role

Use the Terraform configuration from `docs/AWS_AUTHENTICATION_AND_IAM_SETUP.md`:

```bash
terraform apply -target=aws_iam_role.github_actions
```

### Step 3: Add Role ARN to GitHub Secrets

1. Go to GitHub repository settings
2. Secrets and variables → Actions
3. Create secret `AWS_ROLE_ARN` with the role ARN

### Step 4: Deploy Infrastructure

The updated Terraform modules now have all required IAM permissions:

```bash
# Deploy with GitHub Actions workflow
# Or manually:
cd terraform/backend && terraform apply
cd ../s3 && terraform apply
cd ../opensearch && terraform apply
python scripts/create_indexes.py
cd ../bedrock && terraform apply
cd ../eventbridge && terraform apply
cd ../lambda && terraform apply  # Now has all required permissions
cd ../apigateway && terraform apply
```

---

## Verification Checklist

- [ ] OIDC provider created in AWS
- [ ] GitHub Actions IAM role created
- [ ] Role ARN stored in GitHub secrets
- [ ] Lambda module updated with new IAM policies
- [ ] S3 bucket ARN variable added to Lambda module
- [ ] Terraform plan shows new IAM policies
- [ ] Workflow runs successfully without stored credentials
- [ ] Lambda functions can write to CloudWatch Logs
- [ ] Indexer Lambda can read from S3
- [ ] RAG Lambda can invoke Bedrock models

---

## Security Best Practices Applied

1. **No Long-Lived Credentials**
   - OIDC tokens expire after 1 hour
   - Automatic credential rotation
   - No secrets stored in GitHub

2. **Least Privilege Access**
   - Each Lambda has only required permissions
   - CloudWatch Logs scoped to all regions (can be restricted)
   - S3 access scoped to specific bucket

3. **Audit Trail**
   - All AWS API calls logged in CloudTrail
   - GitHub OIDC token exchanges logged
   - Lambda execution logs in CloudWatch

4. **Secure Defaults**
   - No hardcoded credentials
   - All resource names from variables
   - IAM roles follow AWS best practices

---

## Troubleshooting

### Issue: "User is not authorized to perform: sts:AssumeRoleWithWebIdentity"

**Solution**: Ensure OIDC provider is created and role trust policy is correct.

### Issue: Lambda logs not appearing in CloudWatch

**Solution**: Verify Lambda has CloudWatch Logs permissions (now included in updated module).

### Issue: Indexer Lambda can't read S3 events

**Solution**: Verify S3 bucket ARN is passed to Lambda module (now required variable).

### Issue: RAG Lambda can't invoke Bedrock

**Solution**: Verify bedrock:InvokeModel permission is attached (now included in updated module).

---

## Next Steps

1. Apply the security fixes to your infrastructure
2. Follow the OIDC setup guide in `docs/AWS_AUTHENTICATION_AND_IAM_SETUP.md`
3. Test the workflow with GitHub Actions
4. Monitor CloudWatch Logs for any permission errors
5. Review CloudTrail for audit trail

All components now have sufficient IAM permissions for full functionality! 🔒

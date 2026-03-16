# RAG Pipeline Infrastructure - Quick Start Guide

Get the RAG pipeline deployed in 5 minutes.

## Prerequisites

- AWS account
- GitHub repository
- AWS CLI installed locally

## 5-Minute Setup

### 1. Create AWS IAM User (2 minutes)

```bash
# Create IAM user
aws iam create-user --user-name github-rag-pipeline

# Attach policies
aws iam attach-user-policy --user-name github-rag-pipeline \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Create access key
aws iam create-access-key --user-name github-rag-pipeline
```

Save the `AccessKeyId` and `SecretAccessKey` from the output.

### 2. Add GitHub Secrets (2 minutes)

1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `AWS_ACCESS_KEY_ID` with your access key
4. Add `AWS_SECRET_ACCESS_KEY` with your secret key

### 3. Trigger Deployment (1 minute)

1. Go to GitHub repository → Actions tab
2. Select "Deploy RAG Pipeline Infrastructure"
3. Click "Run workflow"
4. Select environment: `dev`
5. Select branch: `main`
6. Click "Run workflow"

**Done!** Deployment will complete in ~10-15 minutes.

---

## Verify Deployment

### Check Workflow Status
- Go to Actions tab
- Watch workflow execution
- All steps should show ✓

### Get API Endpoint
- After workflow completes
- Check "Output deployment summary" step
- Copy API endpoint URL

### Test the System

```bash
# Test suggestions endpoint
curl -X GET "https://YOUR_API_ENDPOINT/suggestions?q=test"

# Test search endpoint
curl -X POST "https://YOUR_API_ENDPOINT/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

---

## Next Steps

1. **Upload Documents**: Upload test documents to S3 bucket
2. **Monitor Logs**: Check CloudWatch logs for Lambda functions
3. **Scale Up**: Deploy to staging/prod environments
4. **Integrate**: Connect to your application

---

## Troubleshooting

### Deployment Failed
1. Check workflow logs in GitHub Actions
2. Verify AWS credentials are correct
3. Check AWS IAM permissions
4. See `IMPLEMENTATION_GUIDE.md` for detailed troubleshooting

### API Returns 502
1. Check Lambda logs in CloudWatch
2. Verify OpenSearch collection is active
3. Check Lambda environment variables
4. See `IMPLEMENTATION_GUIDE.md` for solutions

### Need Help?
- Read `IMPLEMENTATION_GUIDE.md` for complete documentation
- Check `DEPLOYMENT_CHECKLIST.md` for verification steps
- Review `GITHUB_SECRETS_SETUP.md` for secrets configuration

---

## Key Files

- `IMPLEMENTATION_GUIDE.md` - Complete reference guide
- `GITHUB_SECRETS_SETUP.md` - Secrets setup instructions
- `DEPLOYMENT_CHECKLIST.md` - Deployment verification
- `IMPLEMENTATION_COMPLETE.md` - What's been implemented

---

**That's it! Your RAG pipeline is now deployed and ready to use.**

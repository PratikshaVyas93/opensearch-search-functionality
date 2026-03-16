# RAG Pipeline Infrastructure - Deployment Checklist

Complete this checklist to ensure successful deployment of the RAG pipeline infrastructure.

## Pre-Deployment Phase

### AWS Account Setup
- [ ] AWS account created and verified
- [ ] AWS region selected (default: us-east-1)
- [ ] Billing alerts configured
- [ ] CloudTrail enabled for audit logging

### IAM User Setup
- [ ] IAM user created for GitHub Actions (e.g., `github-rag-pipeline`)
- [ ] Access key and secret key generated
- [ ] Required IAM policies attached:
  - [ ] AmazonS3FullAccess
  - [ ] AmazonDynamoDBFullAccess
  - [ ] AmazonOpenSearchServiceFullAccess
  - [ ] AmazonBedrockFullAccess
  - [ ] AWSLambdaFullAccess
  - [ ] IAMFullAccess
  - [ ] AmazonEventBridgeFullAccess
  - [ ] AWSStepFunctionsFullAccess
  - [ ] APIGatewayAdministrator
  - [ ] CloudWatchLogsFullAccess
- [ ] Access keys tested locally with AWS CLI

### GitHub Repository Setup
- [ ] Repository created or forked
- [ ] Repository cloned locally
- [ ] All code files present:
  - [ ] Terraform modules in `terraform/` directory
  - [ ] Lambda functions in `terraform/lambda/` subdirectories
  - [ ] Python scripts in `scripts/` directory
  - [ ] GitHub Actions workflow in `.github/workflows/deploy.yml`
  - [ ] Documentation files created

### GitHub Secrets Configuration
- [ ] GitHub repository accessed
- [ ] Settings → Secrets and variables → Actions opened
- [ ] `AWS_ACCESS_KEY_ID` secret created
- [ ] `AWS_SECRET_ACCESS_KEY` secret created
- [ ] Secrets verified (listed in Actions secrets)

### Local Environment Setup
- [ ] Terraform installed (version >= 1.0)
- [ ] AWS CLI v2 installed
- [ ] Python 3.13 installed
- [ ] Git installed
- [ ] All tools verified with version commands:
  ```bash
  terraform version
  aws --version
  python --version
  git --version
  ```

### Code Verification
- [ ] All Terraform files have correct syntax
- [ ] All Lambda functions have correct Python syntax
- [ ] `scripts/requirements.txt` contains all dependencies
- [ ] `scripts/create_indexes.py` is executable
- [ ] GitHub Actions workflow YAML is valid

## Deployment Phase

### Pre-Deployment Checks
- [ ] No uncommitted changes in repository
- [ ] Latest code pushed to GitHub
- [ ] Correct branch selected for deployment
- [ ] Environment name decided (dev/staging/prod)

### Workflow Execution
- [ ] GitHub Actions workflow triggered manually
- [ ] Environment selected (dev/staging/prod)
- [ ] Branch selected (main or other)
- [ ] Workflow started successfully

### Deployment Monitoring
- [ ] Workflow execution started
- [ ] Step 1: Checkout - ✓ Passed
- [ ] Step 2: Configure AWS credentials - ✓ Passed
- [ ] Step 3: Deploy backend - ✓ Passed
- [ ] Step 4: Deploy S3 - ✓ Passed
- [ ] Step 5: Deploy OpenSearch - ✓ Passed
- [ ] Step 6: Create indexes - ✓ Passed
- [ ] Step 7: Deploy Bedrock - ✓ Passed
- [ ] Step 8: Deploy EventBridge - ✓ Passed
- [ ] Step 9: Deploy Lambda - ✓ Passed
- [ ] Step 10: Deploy API Gateway - ✓ Passed
- [ ] Step 11: Output summary - ✓ Passed

### Deployment Verification
- [ ] Workflow completed successfully
- [ ] No errors in workflow logs
- [ ] API endpoint URL displayed in output
- [ ] All resources created in AWS Console

## Post-Deployment Phase

### AWS Resource Verification
- [ ] S3 bucket created and accessible
- [ ] DynamoDB table created for state locking
- [ ] OpenSearch collection active and accessible
- [ ] Bedrock Knowledge Base created
- [ ] Lambda functions deployed and accessible
- [ ] API Gateway HTTP API created
- [ ] EventBridge rule active
- [ ] Step Functions state machine created
- [ ] IAM roles created with correct permissions

### OpenSearch Verification
- [ ] OpenSearch collection endpoint accessible
- [ ] Three indexes created:
  - [ ] chunk-index (with knn_vector mapping)
  - [ ] metadata-index
  - [ ] suggestions-index
- [ ] Indexes have correct mappings
- [ ] Collection has encryption enabled
- [ ] Access policies configured

### Lambda Function Verification
- [ ] Search Lambda deployed
- [ ] Suggestions Lambda deployed
- [ ] RAG Lambda deployed
- [ ] Indexer Lambda deployed
- [ ] All Lambda functions have correct environment variables:
  - [ ] OPENSEARCH_ENDPOINT
  - [ ] RAG_LAMBDA_NAME (for Search Lambda)
  - [ ] BEDROCK_MODEL_ID (for RAG Lambda)
  - [ ] AWS_REGION
- [ ] All Lambda functions have correct IAM roles
- [ ] Lambda functions can be invoked

### API Gateway Verification
- [ ] HTTP API created
- [ ] Two routes configured:
  - [ ] POST /search
  - [ ] GET /suggestions
- [ ] Routes integrated with correct Lambda functions
- [ ] No /upload or /coach routes present
- [ ] API endpoint URL accessible
- [ ] CORS configured if needed

### Integration Testing
- [ ] Upload test document to S3
- [ ] Verify Step Functions execution triggered
- [ ] Verify Indexer Lambda executed successfully
- [ ] Verify metadata indexed in OpenSearch
- [ ] Verify suggestions indexed in OpenSearch
- [ ] Query suggestions endpoint: `GET /suggestions?q=test`
- [ ] Verify suggestions returned
- [ ] Query search endpoint: `POST /search` with test query
- [ ] Verify search results returned
- [ ] Verify generated answer included in response

### Monitoring Setup
- [ ] CloudWatch log groups created for all Lambda functions
- [ ] CloudWatch logs accessible
- [ ] Log retention configured (recommended: 7-30 days)
- [ ] CloudWatch alarms configured (optional):
  - [ ] Lambda error rate alarm
  - [ ] OpenSearch CPU alarm
  - [ ] API Gateway 5xx error alarm

### Documentation Review
- [ ] IMPLEMENTATION_GUIDE.md reviewed
- [ ] GITHUB_SECRETS_SETUP.md reviewed
- [ ] DEPLOYMENT_CHECKLIST.md completed
- [ ] Architecture diagram understood
- [ ] Data flow understood
- [ ] Testing procedures understood

## Troubleshooting Phase

### If Deployment Fails
- [ ] Check workflow logs for error messages
- [ ] Verify AWS credentials are correct
- [ ] Verify IAM user has required permissions
- [ ] Check AWS service quotas (especially for OpenSearch)
- [ ] Verify Terraform state is not corrupted
- [ ] Check for resource naming conflicts
- [ ] Review CloudFormation events in AWS Console

### If Resources Not Created
- [ ] Check AWS Console for partial resources
- [ ] Verify Terraform state file in S3
- [ ] Check CloudFormation stacks
- [ ] Review IAM permissions
- [ ] Check AWS service limits

### If Lambda Functions Fail
- [ ] Check CloudWatch logs for error messages
- [ ] Verify environment variables are set
- [ ] Verify IAM role has required permissions
- [ ] Test Lambda functions locally
- [ ] Check OpenSearch/Bedrock connectivity
- [ ] Verify network security groups

### If API Endpoints Return Errors
- [ ] Check Lambda function logs
- [ ] Verify API Gateway integration
- [ ] Test Lambda functions directly
- [ ] Check request/response format
- [ ] Verify authentication/authorization

## Post-Deployment Maintenance

### Regular Tasks
- [ ] Monitor CloudWatch logs daily
- [ ] Check AWS billing weekly
- [ ] Review Lambda performance metrics
- [ ] Monitor OpenSearch cluster health
- [ ] Rotate AWS access keys every 90 days
- [ ] Update dependencies monthly
- [ ] Review security policies quarterly

### Backup and Recovery
- [ ] Terraform state backed up
- [ ] OpenSearch indexes backed up
- [ ] Disaster recovery plan documented
- [ ] Backup restoration tested

### Scaling Considerations
- [ ] Monitor Lambda concurrent execution
- [ ] Monitor OpenSearch storage usage
- [ ] Monitor API Gateway request rate
- [ ] Plan for scaling if needed
- [ ] Document scaling procedures

## Sign-Off

- [ ] Deployment completed successfully
- [ ] All tests passed
- [ ] Documentation reviewed
- [ ] Team trained on system
- [ ] Monitoring configured
- [ ] Backup procedures documented
- [ ] Ready for production use

**Deployment Date**: _______________

**Deployed By**: _______________

**Environment**: _______________

**Notes**: 
```
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
```

---

## Quick Reference

### Useful AWS CLI Commands

```bash
# List S3 buckets
aws s3 ls

# List OpenSearch collections
aws opensearchserverless list-collections

# List Lambda functions
aws lambda list-functions

# List API Gateway APIs
aws apigatewayv2 get-apis

# Check Step Functions executions
aws stepfunctions list-executions --state-machine-arn <ARN>

# View CloudWatch logs
aws logs tail /aws/lambda/<function-name> --follow

# Get Terraform outputs
cd terraform/<module>
terraform output
```

### Useful GitHub Actions Commands

```bash
# View workflow runs
gh run list --workflow deploy.yml

# View specific run logs
gh run view <run-id> --log

# Trigger workflow manually
gh workflow run deploy.yml -f environment=dev -f branch=main
```

### Useful Terraform Commands

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan

# Apply configuration
terraform apply

# Destroy resources
terraform destroy

# View outputs
terraform output
```

---

## Support and Escalation

### For Issues:
1. Check CloudWatch logs
2. Review IMPLEMENTATION_GUIDE.md troubleshooting section
3. Check GitHub Actions workflow logs
4. Review AWS Console for resource status
5. Contact AWS support if needed

### Documentation:
- IMPLEMENTATION_GUIDE.md - Complete implementation guide
- GITHUB_SECRETS_SETUP.md - GitHub secrets setup
- DEPLOYMENT_CHECKLIST.md - This file
- .kiro/specs/rag-pipeline-infrastructure/ - Specification documents

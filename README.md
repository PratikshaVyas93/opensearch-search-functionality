# Document Search Platform

A serverless document ingestion, search, and suggestions platform on AWS using Terraform, Lambda, OpenSearch, and Bedrock.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Document Search Platform                     │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                          API Layer (HTTP API)                         │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  POST /search?query=...      GET /suggestions?prefix=...       │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
        ┌───────────▼──────────┐      ┌────────────▼──────────┐
        │  Search Lambda       │      │ Suggestions Lambda    │
        │  (metadata + vector) │      │ (prefix matching)     │
        └───────────┬──────────┘      └────────────┬──────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │   OpenSearch Serverless       │
                    │  ┌─────────────────────────┐  │
                    │  │ metadata-index          │  │
                    │  │ vector-index            │  │
                    │  │ suggestions-index       │  │
                    │  └─────────────────────────┘  │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
        ┌───────────▼──────────┐      ┌────────────▼──────────┐
        │  Bedrock Knowledge   │      │  Index Bootstrap      │
        │  Base (RAG)          │      │  Lambda               │
        └──────────────────────┘      └───────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                      Ingestion Pipeline (EventBridge)                 │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  S3 Upload → EventBridge → Step Functions → Lambda Pipeline    │ │
│  │                                                                  │ │
│  │  1. Document Processor Lambda (extract text & metadata)        │ │
│  │  2. Embedding Generator Lambda (Bedrock + OpenSearch index)    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                         Storage Layer                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  S3 Documents    │  │  OpenSearch      │  │  Bedrock         │   │
│  │  Bucket          │  │  Collection      │  │  Knowledge Base  │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

## Terraform Module Structure

```
infra/
├── main.tf                          # Root module orchestration
├── variables.tf                     # Root variables
├── outputs.tf                       # Root outputs
├── terraform.tfvars                 # Default values
├── lambda_layers/
│   └── opensearch/
│       └── python/
│           └── requirements.txt     # OpenSearch dependencies
└── modules/
    ├── iam/                         # IAM roles and policies
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── s3_documents/                # S3 bucket for documents
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── opensearch_collection/       # OpenSearch Serverless
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── opensearch_index_bootstrap_lambda/  # Index bootstrap
    │   ├── lambda_function.py
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── lambda_search/               # Search API Lambda
    │   ├── lambda_function.py
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── lambda_suggestions/          # Suggestions API Lambda
    │   ├── lambda_function.py
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── lambda_ingestion_processor/  # Document processor
    │   ├── lambda_function.py
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── lambda_embedding_generator/  # Embedding generator
    │   ├── lambda_function.py
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── step_functions_ingestion/    # Ingestion orchestration
    │   ├── state_machine.json
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── api_gateway/                 # HTTP API
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── bedrock_knowledge_base/      # Bedrock RAG
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Resource Naming Conventions

All resources follow the naming pattern: `${env}-${project_name}-{resource-type}`

Examples:
- S3 Bucket: `dev-opensearch-navco-search-documents-bucket`
- OpenSearch Collection: `dev-opensearch-navco-search-collection`
- Search Lambda: `dev-opensearch-navco-search-search`
- Suggestions Lambda: `dev-opensearch-navco-search-suggestions`
- Document Processor: `dev-opensearch-navco-search-processor`
- Embedding Generator: `dev-opensearch-navco-search-embedding`
- Step Functions: `dev-opensearch-navco-search-ingestion`
- API Gateway: `dev-opensearch-navco-search-api`
- Knowledge Base: `dev-opensearch-navco-search-kb`

## Resource Dependencies and Creation Sequence

### Phase 1: Infrastructure Foundation
1. **S3 Documents Bucket** - Document storage with versioning and EventBridge notifications
2. **OpenSearch Collection** - Serverless vector search with encryption and access policies
3. **IAM Module** - Roles and policies for all Lambda functions and services

### Phase 2: Index Bootstrap
4. **Index Bootstrap Lambda** - Creates metadata, vector, and suggestions indexes

### Phase 3: Search & Query APIs
5. **Search Lambda** - Searches metadata and vector indexes
6. **Suggestions Lambda** - Provides autocomplete suggestions

### Phase 4: Ingestion Pipeline
7. **Document Processor Lambda** - Extracts text and metadata from S3 documents
8. **Embedding Generator Lambda** - Generates embeddings and indexes documents
9. **Step Functions** - Orchestrates the ingestion workflow with EventBridge trigger

### Phase 5: API & Bedrock
10. **API Gateway** - HTTP API with /search and /suggestions routes
11. **Bedrock Knowledge Base** - RAG knowledge base with S3 data source

## GitHub Actions Workflow

The CI/CD workflow (`infra-ci-cd.yml`) implements a 2-phase deployment strategy:

### Phase 1: Core Infrastructure
- Terraform init, validate, and plan
- Deploy core infrastructure (S3, OpenSearch, IAM, Lambdas)
- Invoke Index Bootstrap Lambda to create indexes
- Wait for bootstrap to complete

### Phase 2: Dependent Infrastructure
- Deploy dependent infrastructure (API Gateway, Bedrock Knowledge Base)
- Generate deployment summary with API endpoints

### Workflow Inputs
- **environment**: dev, stg, or prod
- **branch**: Git branch to deploy (default: main)

### Workflow Execution
```bash
# Trigger via GitHub UI or CLI
gh workflow run infra-ci-cd.yml \
  -f environment=dev \
  -f branch=main
```

## Setup Instructions

### Prerequisites
- AWS Account with appropriate permissions
- Terraform >= 1.0
- AWS CLI configured
- GitHub repository with Actions enabled

### Step 1: Configure GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to Settings → Secrets and variables → Actions
2. Add these secrets:
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

```bash
# Or use GitHub CLI
gh secret set AWS_ACCESS_KEY_ID --body "your-access-key"
gh secret set AWS_SECRET_ACCESS_KEY --body "your-secret-key"
```

### Step 2: Customize Terraform Variables

Edit `infra/terraform.tfvars`:

```hcl
env          = "dev"              # dev, stg, or prod
project_name = "opensearch-navco-search"  # Your project name
region       = "us-east-1"        # AWS region
bedrock_model_id = "amazon.titan-embed-text-v1"  # Bedrock model
```

### Step 3: Deploy Infrastructure

Option A: Using GitHub Actions (Recommended)
1. Go to Actions → Infrastructure CI/CD
2. Click "Run workflow"
3. Select environment and branch
4. Click "Run workflow"

Option B: Using Terraform CLI
```bash
cd infra
terraform init
terraform plan -var="env=dev"
terraform apply -var="env=dev"
```

### Step 4: Verify Deployment

After deployment, check the outputs:

```bash
cd infra
terraform output api_endpoint
terraform output search_endpoint
terraform output suggestions_endpoint
```

## Testing the System

### Test Search API

```bash
# Search for documents
curl -X POST "https://your-api-endpoint/search?query=test" \
  -H "Content-Type: application/json"

# Response
{
  "query": "test",
  "results": [
    {
      "id": "document-id",
      "score": 0.95,
      "source": {
        "title": "Document Title",
        "content": "Document content...",
        "upload_date": "2024-01-01T00:00:00"
      }
    }
  ],
  "count": 1
}
```

### Test Suggestions API

```bash
# Get suggestions for prefix
curl -X GET "https://your-api-endpoint/suggestions?prefix=test" \
  -H "Content-Type: application/json"

# Response
{
  "prefix": "test",
  "suggestions": [
    {
      "suggestion": "test document",
      "weight": 10,
      "score": 0.98
    }
  ],
  "count": 1
}
```

### Upload Document for Ingestion

```bash
# Upload a document to S3
aws s3 cp document.txt s3://dev-opensearch-navco-search-documents-bucket/

# This triggers:
# 1. EventBridge rule detects S3 upload
# 2. Step Functions starts ingestion workflow
# 3. Document Processor extracts text and metadata
# 4. Embedding Generator creates embeddings and indexes document
# 5. Document becomes searchable via API
```

### Monitor Ingestion Pipeline

```bash
# Check Step Functions execution
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:ACCOUNT:stateMachine:dev-opensearch-navco-search-ingestion

# Check Lambda logs
aws logs tail /aws/lambda/dev-opensearch-navco-search-processor --follow
aws logs tail /aws/lambda/dev-opensearch-navco-search-embedding --follow
```

## Troubleshooting

### Issue: Index Bootstrap Lambda Fails

**Symptoms**: Deployment fails at index bootstrap step

**Solutions**:
1. Check Lambda logs: `aws logs tail /aws/lambda/dev-opensearch-navco-search-index-bootstrap --follow`
2. Verify OpenSearch collection is accessible
3. Check IAM permissions for the Lambda role
4. Ensure OpenSearch layer is properly deployed

### Issue: Search Returns No Results

**Symptoms**: Search API returns empty results

**Solutions**:
1. Verify documents were uploaded to S3
2. Check Step Functions execution: `aws stepfunctions list-executions --state-machine-arn <arn>`
3. Check embedding generator logs for errors
4. Verify OpenSearch indexes exist: `aws opensearchserverless batch-get-collection-status`

### Issue: Bedrock Throttling

**Symptoms**: Embedding generator fails with throttling errors

**Solutions**:
1. The embedding generator has built-in retry logic with exponential backoff
2. Increase Lambda timeout if needed
3. Request Bedrock quota increase from AWS

### Issue: API Gateway Returns 502

**Symptoms**: API endpoints return HTTP 502 errors

**Solutions**:
1. Check Lambda function logs
2. Verify Lambda has correct IAM permissions
3. Check OpenSearch endpoint connectivity
4. Verify environment variables are set correctly

### Issue: Terraform State Lock

**Symptoms**: Terraform operations hang or fail with lock error

**Solutions**:
```bash
# Force unlock (use with caution)
terraform force-unlock <LOCK_ID>

# Or use S3 backend with DynamoDB lock table
# Configure in terraform block
```

## Monitoring and Logging

### CloudWatch Logs

All Lambda functions log to CloudWatch:

```bash
# View logs for specific Lambda
aws logs tail /aws/lambda/dev-opensearch-navco-search-search --follow

# View logs for all components
aws logs tail /aws/apigateway/dev-opensearch-navco-search-api --follow
aws logs tail /aws/stepfunctions/dev-opensearch-navco-search-ingestion --follow
```

### CloudWatch Metrics

Monitor key metrics:

```bash
# Lambda invocations and errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=dev-opensearch-navco-search-search \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### OpenSearch Monitoring

```bash
# Check collection status
aws opensearchserverless batch-get-collection-status \
  --names dev-opensearch-navco-search-collection

# Check index stats
aws opensearchserverless batch-get-effective-lifecycle-policy \
  --resource-identifiers resourceType=collection,resourceId=dev-opensearch-navco-search-collection
```

## Cost Optimization

### Recommendations

1. **OpenSearch**: Use Serverless for variable workloads (pay per request)
2. **Lambda**: Set appropriate timeout and memory values
3. **S3**: Enable lifecycle policies to archive old documents
4. **Bedrock**: Monitor token usage and request quota
5. **CloudWatch**: Set appropriate log retention periods

### Estimated Monthly Costs (dev environment)

- OpenSearch Serverless: $0.30 - $5.00 (variable)
- Lambda: $0.20 - $2.00 (based on invocations)
- S3: $0.10 - $1.00 (based on storage)
- Bedrock: $0.50 - $5.00 (based on embeddings)
- **Total**: ~$1.10 - $13.00/month

## Security Best Practices

1. **IAM Policies**: Use least-privilege permissions (already implemented)
2. **Encryption**: All data encrypted at rest (S3, OpenSearch)
3. **Network**: OpenSearch allows public access (configure for private VPC if needed)
4. **Secrets**: Use AWS Secrets Manager for sensitive data
5. **Logging**: All operations logged to CloudWatch
6. **Access Control**: API Gateway can be restricted with API keys or authentication

## Cleanup

To remove all resources:

```bash
cd infra
terraform destroy -var="env=dev"

# Or via GitHub Actions
# Manually delete the stack or add a destroy workflow
```

## Support and Documentation

- [AWS Terraform Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [OpenSearch Python Client](https://opensearch-project.github.io/opensearch-py/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)

## License

This project is provided as-is for educational and commercial use.

# RAG Pipeline Infrastructure - Complete Implementation Guide

## Overview

This document provides a comprehensive guide for implementing, deploying, and testing the complete AWS Retrieval-Augmented Generation (RAG) pipeline infrastructure. The system consists of two main pipelines:

1. **Ingestion Pipeline**: S3 → EventBridge → Step Functions → Lambda Indexer → OpenSearch
2. **Search/Retrieval Pipeline**: API Gateway → Lambda Proxies → OpenSearch/Bedrock → LLM Response

All infrastructure is provisioned using Terraform with modular design, and deployment is orchestrated via GitHub Actions.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Lambda Functions Implementation](#lambda-functions-implementation)
4. [GitHub Actions Workflow Setup](#github-actions-workflow-setup)
5. [Deployment Instructions](#deployment-instructions)
6. [Testing Guide](#testing-guide)
7. [Troubleshooting](#troubleshooting)
8. [Environment Variables Reference](#environment-variables-reference)

---

## Prerequisites

### Required Tools
- Terraform >= 1.0
- AWS CLI v2
- Python 3.13
- Git
- GitHub account with repository access

### AWS Permissions Required
Your AWS credentials must have permissions for:
- S3 (create buckets, manage versioning)
- DynamoDB (create tables)
- OpenSearch Serverless (create collections, manage indexes)
- Bedrock (create knowledge bases, invoke models)
- Lambda (create functions, manage roles)
- IAM (create roles and policies)
- EventBridge (create rules)
- Step Functions (create state machines)
- API Gateway (create HTTP APIs)
- CloudWatch (logs)

### GitHub Secrets Required
Add the following secrets to your GitHub repository:

```
AWS_ACCESS_KEY_ID          - Your AWS access key
AWS_SECRET_ACCESS_KEY      - Your AWS secret access key
```

To add secrets:
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `AWS_ACCESS_KEY_ID` with your access key
4. Add `AWS_SECRET_ACCESS_KEY` with your secret key

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  S3 Bucket                                                      │
│  (Document Upload)                                              │
│         │                                                       │
│         ├─→ EventBridge Rule                                    │
│             (S3 ObjectCreated Event)                            │
│                    │                                            │
│                    ├─→ Step Functions State Machine             │
│                        (Orchestration)                          │
│                             │                                   │
│                             ├─→ Indexer Lambda                  │
│                                 (Extract Metadata)              │
│                                      │                          │
│                                      ├─→ OpenSearch             │
│                                          (metadata-index,       │
│                                           suggestions-index)    │
│                                                                 │
│  Bedrock Knowledge Base (Async)                                │
│  (Chunk + Embed with Titan)                                    │
│         │                                                       │
│         ├─→ OpenSearch (chunk-index)                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   SEARCH/RETRIEVAL PIPELINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client Request                                                 │
│         │                                                       │
│         ├─→ API Gateway                                         │
│             ├─ POST /search                                     │
│             └─ GET /suggestions                                 │
│                    │                                            │
│         ┌──────────┴──────────┐                                 │
│         │                     │                                 │
│    Search Lambda        Suggestions Lambda                      │
│    (Query OpenSearch)   (Query suggestions-index)               │
│         │                     │                                 │
│         ├─→ OpenSearch        └─→ Response                      │
│             (chunk-index,                                       │
│              metadata-index)                                    │
│             │                                                   │
│             ├─→ RAG Lambda                                      │
│                 (Invoke Bedrock)                                │
│                 │                                               │
│                 ├─→ Bedrock Agent Runtime                       │
│                     (Claude 3 Haiku)                            │
│                     │                                           │
│                     └─→ Generated Answer                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

**Ingestion Flow:**
1. Document uploaded to S3
2. S3 ObjectCreated event triggers EventBridge rule
3. EventBridge invokes Step Functions state machine
4. Step Functions invokes Indexer Lambda
5. Indexer Lambda extracts metadata and indexes to OpenSearch
6. Bedrock Knowledge Base independently reads from S3, chunks documents, generates embeddings, stores in chunk-index

**Search Flow:**
1. Client sends search query to API Gateway `/search` endpoint
2. Search Lambda queries OpenSearch (chunk-index + metadata-index)
3. Search Lambda invokes RAG Lambda with retrieved context
4. RAG Lambda invokes Bedrock Agent Runtime with Claude 3 Haiku
5. Bedrock generates answer based on context
6. Response returned to client with results and generated answer

---

## Lambda Functions Implementation

### 1. Search Lambda (`terraform/lambda/search/index.py`)

**Purpose**: Proxy search requests to OpenSearch and invoke RAG Lambda for answer generation.

**Key Features**:
- Multi-index search (chunk-index + metadata-index)
- Relevance scoring and sorting
- RAG Lambda invocation with context
- Error handling with HTTP 502 responses

**Environment Variables**:
- `OPENSEARCH_ENDPOINT`: OpenSearch collection endpoint
- `RAG_LAMBDA_NAME`: Name of RAG Lambda function
- `AWS_REGION`: AWS region

**Request Format**:
```json
{
  "body": {
    "query": "search query string"
  }
}
```

**Response Format**:
```json
{
  "statusCode": 200,
  "body": {
    "results": [
      {
        "index": "chunk-index",
        "score": 0.95,
        "source": {
          "text": "document text",
          "embedding": [...],
          "source_uri": "s3://bucket/key"
        }
      }
    ],
    "generated_answer": "LLM-generated answer based on context"
  }
}
```

### 2. Suggestions Lambda (`terraform/lambda/suggestions/index.py`)

**Purpose**: Provide autocomplete suggestions from OpenSearch suggestions-index.

**Key Features**:
- Prefix-based matching
- Weight-based sorting
- Document association
- Error handling with HTTP 502 responses

**Environment Variables**:
- `OPENSEARCH_ENDPOINT`: OpenSearch collection endpoint
- `AWS_REGION`: AWS region

**Request Format**:
```
GET /suggestions?q=search_prefix
```

**Response Format**:
```json
{
  "statusCode": 200,
  "body": {
    "suggestions": [
      {
        "text": "suggestion text",
        "weight": 10,
        "doc_id": "document-id"
      }
    ]
  }
}
```

### 3. RAG Lambda (`terraform/lambda/rag/index.py`)

**Purpose**: Invoke Bedrock Agent Runtime with retrieved context for LLM-based answer generation.

**Key Features**:
- Exponential backoff retry logic (up to 3 attempts)
- Throttling handling
- Context-aware prompt building
- Claude 3 Haiku model integration

**Environment Variables**:
- `BEDROCK_MODEL_ID`: Bedrock model ID (default: anthropic.claude-3-haiku-20240307-v1:0)
- `AWS_REGION`: AWS region

**Request Format**:
```json
{
  "query": "original search query",
  "context": "[search results as JSON string]"
}
```

**Response Format**:
```json
{
  "statusCode": 200,
  "body": {
    "answer": "Generated answer from Bedrock"
  }
}
```

**Retry Logic**:
- Attempt 1: Immediate
- Attempt 2: Wait 1 second
- Attempt 3: Wait 2 seconds
- Handles ThrottlingException and general exceptions

### 4. Indexer Lambda (`terraform/lambda/indexer/index.py`)

**Purpose**: Extract document metadata from S3 and index to OpenSearch.

**Key Features**:
- S3 metadata extraction
- Metadata indexing to metadata-index
- Suggestion generation and indexing
- Exception raising on failure (for Step Functions visibility)

**Environment Variables**:
- `OPENSEARCH_ENDPOINT`: OpenSearch collection endpoint
- `AWS_REGION`: AWS region

**Request Format** (from Step Functions):
```json
{
  "detail": {
    "bucket": {
      "name": "bucket-name"
    },
    "object": {
      "key": "document-key"
    }
  }
}
```

**Response Format**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Document indexed successfully",
    "doc_id": "document-id",
    "metadata_response": {...},
    "suggestions_response": {...}
  }
}
```

---

## GitHub Actions Workflow Setup

### Workflow File: `.github/workflows/deploy.yml`

The workflow is triggered manually via `workflow_dispatch` with two inputs:

**Inputs**:
- `environment`: Target environment (dev, staging, prod)
- `branch`: Git branch to deploy from (default: main)

**Deployment Steps** (in order):

1. **Checkout Code**: Clone repository at specified branch
2. **Configure AWS Credentials**: Use GitHub secrets for AWS access
3. **Deploy Backend**: S3 state bucket + DynamoDB lock table
4. **Deploy S3**: Document storage bucket
5. **Deploy OpenSearch**: Serverless collection
6. **Create Indexes**: Python script creates OpenSearch indexes
7. **Deploy Bedrock**: Knowledge Base with Titan Embeddings
8. **Deploy EventBridge**: S3 event rule + Step Functions state machine
9. **Deploy Lambda**: All four Lambda functions with IAM roles
10. **Deploy API Gateway**: HTTP API with /search and /suggestions routes
11. **Output Summary**: Display deployment results

### Environment Variables in Workflow

All resource names are parameterized:

```yaml
TF_VAR_state_bucket_name: opensearch-project-{environment}-tf-state
TF_VAR_lock_table_name: opensearch-project-{environment}-tf-lock
TF_VAR_bucket_name: opensearch-project-{environment}-bucket
TF_VAR_collection_name: opensearch-project-{environment}-collection
TF_VAR_knowledge_base_name: opensearch-project-{environment}-kb
TF_VAR_search_lambda_name: opensearch-project-{environment}-search
TF_VAR_suggestions_lambda_name: opensearch-project-{environment}-suggestions
TF_VAR_rag_lambda_name: opensearch-project-{environment}-rag
TF_VAR_indexer_lambda_name: opensearch-project-{environment}-indexer
TF_VAR_api_name: opensearch-project-{environment}-api
```

### Workflow Execution

**To trigger deployment**:

1. Go to GitHub repository → Actions tab
2. Select "Deploy RAG Pipeline Infrastructure" workflow
3. Click "Run workflow"
4. Select environment (dev/staging/prod)
5. Select branch (default: main)
6. Click "Run workflow"

**Monitor execution**:
- Workflow runs sequentially through all steps
- Each step must complete successfully before next begins
- Failure in any step halts the workflow
- Check logs for detailed error messages

---

## Deployment Instructions

### Step 1: Prepare AWS Credentials

1. Create AWS IAM user with programmatic access
2. Attach policies for required services (see Prerequisites)
3. Generate access key and secret key
4. Store securely (never commit to repository)

### Step 2: Add GitHub Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. Add `AWS_ACCESS_KEY_ID`
3. Add `AWS_SECRET_ACCESS_KEY`

### Step 3: Verify Terraform Modules

Ensure all Terraform modules exist:
```
terraform/
├── backend/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── s3/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── opensearch/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── bedrock/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── eventbridge/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── lambda/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── search/
│   │   └── index.py
│   ├── suggestions/
│   │   └── index.py
│   ├── rag/
│   │   └── index.py
│   └── indexer/
│       └── index.py
└── apigateway/
    ├── main.tf
    ├── variables.tf
    └── outputs.tf
```

### Step 4: Verify Python Dependencies

Ensure `scripts/requirements.txt` contains:
```
opensearch-py>=2.0.0
boto3>=1.26.0
requests-aws4auth>=1.2.3
```

### Step 5: Trigger Deployment

1. Go to GitHub Actions
2. Select "Deploy RAG Pipeline Infrastructure"
3. Click "Run workflow"
4. Select environment and branch
5. Monitor execution

### Step 6: Verify Deployment

After workflow completes:

1. Check AWS Console for created resources
2. Verify S3 bucket exists
3. Verify OpenSearch collection is active
4. Verify Lambda functions are deployed
5. Verify API Gateway endpoint is created

---

## Testing Guide

### Manual Testing

#### Test 1: Upload Document to S3

```bash
# Upload a test document
aws s3 cp test-document.txt s3://opensearch-project-dev-bucket/documents/

# Verify Step Functions execution
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:ACCOUNT_ID:stateMachine:opensearch-project-dev-state-machine
```

#### Test 2: Query Suggestions Endpoint

```bash
# Get suggestions
curl -X GET "https://API_ENDPOINT/suggestions?q=test"

# Expected response:
{
  "suggestions": [
    {
      "text": "test document",
      "weight": 10,
      "doc_id": "documents-test-document-txt"
    }
  ]
}
```

#### Test 3: Query Search Endpoint

```bash
# Search with query
curl -X POST "https://API_ENDPOINT/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search query"
  }'

# Expected response:
{
  "results": [
    {
      "index": "chunk-index",
      "score": 0.95,
      "source": {
        "text": "relevant document text",
        "embedding": [...],
        "source_uri": "s3://bucket/key"
      }
    }
  ],
  "generated_answer": "LLM-generated answer based on context"
}
```

#### Test 4: Verify OpenSearch Indexes

```bash
# List indexes
curl -X GET "https://OPENSEARCH_ENDPOINT/_cat/indices"

# Query chunk-index
curl -X GET "https://OPENSEARCH_ENDPOINT/chunk-index/_search"

# Query metadata-index
curl -X GET "https://OPENSEARCH_ENDPOINT/metadata-index/_search"

# Query suggestions-index
curl -X GET "https://OPENSEARCH_ENDPOINT/suggestions-index/_search"
```

### Automated Testing

#### Unit Tests for Lambda Functions

Create `tests/test_lambda_functions.py`:

```python
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

# Test Search Lambda
def test_search_lambda_valid_query():
    from terraform.lambda.search.index import lambda_handler
    
    event = {
        'body': json.dumps({'query': 'test query'})
    }
    
    with patch('terraform.lambda.search.index.opensearch_client') as mock_os:
        mock_os.search.return_value = {
            'hits': {
                'hits': [
                    {
                        '_score': 0.95,
                        '_source': {'text': 'test document'}
                    }
                ]
            }
        }
        
        with patch('terraform.lambda.search.index.lambda_client') as mock_lambda:
            mock_lambda.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({'answer': 'test answer'}))
            }
            
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200

# Test Suggestions Lambda
def test_suggestions_lambda_valid_prefix():
    from terraform.lambda.suggestions.index import lambda_handler
    
    event = {
        'queryStringParameters': {'q': 'test'}
    }
    
    with patch('terraform.lambda.suggestions.index.opensearch_client') as mock_os:
        mock_os.search.return_value = {
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'text': 'test suggestion',
                            'weight': 10,
                            'doc_id': 'doc-1'
                        }
                    }
                ]
            }
        }
        
        response = lambda_handler(event, None)
        assert response['statusCode'] == 200

# Test RAG Lambda
def test_rag_lambda_valid_context():
    from terraform.lambda.rag.index import lambda_handler
    
    event = {
        'query': 'test query',
        'context': json.dumps([{'source': {'text': 'context text'}}])
    }
    
    with patch('terraform.lambda.rag.index.bedrock_client') as mock_bedrock:
        mock_bedrock.invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({'completion': 'test answer'}))
        }
        
        response = lambda_handler(event, None)
        assert response['statusCode'] == 200

# Test Indexer Lambda
def test_indexer_lambda_valid_event():
    from terraform.lambda.indexer.index import lambda_handler
    
    event = {
        'detail': {
            'bucket': {'name': 'test-bucket'},
            'object': {'key': 'test-document.txt'}
        }
    }
    
    with patch('terraform.lambda.indexer.index.s3_client') as mock_s3:
        mock_s3.head_object.return_value = {
            'LastModified': MagicMock(isoformat=lambda: '2024-01-01T00:00:00'),
            'Metadata': {}
        }
        
        with patch('terraform.lambda.indexer.index.opensearch_client') as mock_os:
            mock_os.index.return_value = {'_id': 'doc-1'}
            
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
```

Run tests:
```bash
pytest tests/test_lambda_functions.py -v
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: AWS Credentials Not Found

**Error**: `Unable to locate credentials`

**Solution**:
1. Verify GitHub secrets are set correctly
2. Check AWS access key and secret key are valid
3. Ensure IAM user has required permissions
4. Verify secrets are named exactly: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

#### Issue 2: OpenSearch Index Creation Fails

**Error**: `Failed to create indexes`

**Solution**:
1. Verify OpenSearch collection is active
2. Check network connectivity to OpenSearch endpoint
3. Verify IAM role has OpenSearch permissions
4. Check Python dependencies are installed: `pip install -r scripts/requirements.txt`

#### Issue 3: Lambda Function Timeout

**Error**: `Task timed out after 30.00 seconds`

**Solution**:
1. Increase Lambda timeout in Terraform (default: 60 seconds)
2. Check OpenSearch/Bedrock response times
3. Verify network connectivity
4. Check CloudWatch logs for detailed errors

#### Issue 4: Bedrock Throttling

**Error**: `ThrottlingException`

**Solution**:
1. Retry logic is built-in (up to 3 attempts with exponential backoff)
2. Check Bedrock quota in AWS Console
3. Request quota increase if needed
4. Implement request rate limiting

#### Issue 5: API Gateway Returns 502

**Error**: `502 Bad Gateway`

**Solution**:
1. Check Lambda function logs in CloudWatch
2. Verify Lambda has correct environment variables
3. Check OpenSearch/Bedrock connectivity
4. Verify IAM roles have required permissions

### Debugging Steps

1. **Check CloudWatch Logs**:
   ```bash
   aws logs tail /aws/lambda/opensearch-project-dev-search --follow
   ```

2. **Verify OpenSearch Connection**:
   ```bash
   curl -X GET "https://OPENSEARCH_ENDPOINT/_cluster/health"
   ```

3. **Test Lambda Locally**:
   ```bash
   sam local invoke SearchLambda -e test-event.json
   ```

4. **Check Step Functions Execution**:
   ```bash
   aws stepfunctions describe-execution \
     --execution-arn arn:aws:states:us-east-1:ACCOUNT_ID:execution:opensearch-project-dev-state-machine:EXECUTION_ID
   ```

---

## Environment Variables Reference

### Terraform Variables

| Variable | Format | Example | Purpose |
|---|---|---|---|
| `TF_VAR_state_bucket_name` | String | `opensearch-project-dev-tf-state` | S3 bucket for Terraform state |
| `TF_VAR_lock_table_name` | String | `opensearch-project-dev-tf-lock` | DynamoDB table for state locking |
| `TF_VAR_bucket_name` | String | `opensearch-project-dev-bucket` | S3 bucket for documents |
| `TF_VAR_collection_name` | String | `opensearch-project-dev-collection` | OpenSearch collection name |
| `TF_VAR_knowledge_base_name` | String | `opensearch-project-dev-kb` | Bedrock Knowledge Base name |
| `TF_VAR_search_lambda_name` | String | `opensearch-project-dev-search` | Search Lambda function name |
| `TF_VAR_suggestions_lambda_name` | String | `opensearch-project-dev-suggestions` | Suggestions Lambda function name |
| `TF_VAR_rag_lambda_name` | String | `opensearch-project-dev-rag` | RAG Lambda function name |
| `TF_VAR_indexer_lambda_name` | String | `opensearch-project-dev-indexer` | Indexer Lambda function name |
| `TF_VAR_api_name` | String | `opensearch-project-dev-api` | API Gateway name |

### Lambda Environment Variables

| Variable | Lambda Functions | Example | Purpose |
|---|---|---|---|
| `OPENSEARCH_ENDPOINT` | All | `https://abc123.us-east-1.aoss.amazonaws.com` | OpenSearch collection endpoint |
| `RAG_LAMBDA_NAME` | Search | `opensearch-project-dev-rag` | RAG Lambda function name |
| `BEDROCK_MODEL_ID` | RAG | `anthropic.claude-3-haiku-20240307-v1:0` | Bedrock model ID |
| `AWS_REGION` | All | `us-east-1` | AWS region |

### GitHub Secrets

| Secret | Value | Purpose |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | AWS authentication |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | AWS authentication |

---

## Summary

This implementation provides a complete, production-ready RAG pipeline infrastructure with:

✅ **Modular Terraform Design**: Each component is independently deployable
✅ **Automated Deployment**: GitHub Actions orchestrates full deployment
✅ **Error Handling**: Comprehensive error handling and retry logic
✅ **Scalability**: Serverless architecture scales automatically
✅ **Security**: IAM roles with least-privilege permissions
✅ **Monitoring**: CloudWatch logs for all components
✅ **Testing**: Unit tests and integration test guides

For questions or issues, refer to the Troubleshooting section or check CloudWatch logs for detailed error messages.

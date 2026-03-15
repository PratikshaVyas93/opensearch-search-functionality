# Lambda Functions

This directory contains all Lambda function code for the Document Search Platform.

## Structure

```
lambda/
├── search/
│   └── index.py              # Search API - queries metadata and vector indexes
├── suggestions/
│   └── index.py              # Suggestions API - provides autocomplete suggestions
├── processor/
│   └── index.py              # Document Processor - extracts text and metadata from S3
├── embedding/
│   └── index.py              # Embedding Generator - generates embeddings via Bedrock
└── bootstrap/
    └── index.py              # Index Bootstrap - creates OpenSearch indexes
```

## Lambda Functions

### 1. Search Lambda (`search/index.py`)

**Purpose**: Searches documents in OpenSearch metadata and vector indexes

**Handler**: `index.handler`

**Environment Variables**:
- `OPENSEARCH_ENDPOINT` - OpenSearch collection endpoint
- `AWS_REGION` - AWS region

**Input**: Query parameter `?query=search_term`

**Output**: JSON with search results

### 2. Suggestions Lambda (`suggestions/index.py`)

**Purpose**: Provides autocomplete suggestions based on prefix

**Handler**: `index.handler`

**Environment Variables**:
- `OPENSEARCH_ENDPOINT` - OpenSearch collection endpoint
- `AWS_REGION` - AWS region

**Input**: Query parameter `?prefix=search_prefix`

**Output**: JSON with suggestions

### 3. Document Processor Lambda (`processor/index.py`)

**Purpose**: Extracts text and metadata from S3 documents

**Handler**: `index.handler`

**Input**: S3 object information from Step Functions
```json
{
  "bucket": "bucket-name",
  "key": "document-path"
}
```

**Output**: Processed document with content and metadata

### 4. Embedding Generator Lambda (`embedding/index.py`)

**Purpose**: Generates embeddings using Bedrock and indexes documents

**Handler**: `index.handler`

**Environment Variables**:
- `OPENSEARCH_ENDPOINT` - OpenSearch collection endpoint
- `AWS_REGION` - AWS region
- `BEDROCK_MODEL_ID` - Bedrock model ID (default: amazon.titan-embed-text-v1)

**Input**: Processed document from Document Processor
```json
{
  "body": {
    "content": "document text",
    "metadata": {
      "document_id": "doc-id",
      "title": "document title",
      ...
    }
  }
}
```

**Output**: Embedding generation result

### 5. Index Bootstrap Lambda (`bootstrap/index.py`)

**Purpose**: Creates OpenSearch indexes on deployment

**Handler**: `index.handler`

**Environment Variables**:
- `OPENSEARCH_ENDPOINT` - OpenSearch collection endpoint
- `AWS_REGION` - AWS region

**Creates**:
- `metadata-index` - Document metadata
- `vector-index` - Embeddings
- `suggestions-index` - Autocomplete suggestions

## Dependencies

All Lambda functions require the OpenSearch Python layer:
- `opensearchpy` - OpenSearch Python client
- `requests-aws4auth` - AWS authentication for OpenSearch

The layer is defined in `infra/lambda_layers/opensearch/python/requirements.txt`

## Terraform Integration

Each Lambda function is deployed via a Terraform module in `infra/modules/`:

- `lambda_search/` → `lambda/search/index.py`
- `lambda_suggestions/` → `lambda/suggestions/index.py`
- `lambda_ingestion_processor/` → `lambda/processor/index.py`
- `lambda_embedding_generator/` → `lambda/embedding/index.py`
- `opensearch_index_bootstrap_lambda/` → `lambda/bootstrap/index.py`

The Terraform modules handle:
- Archiving the Lambda code
- Creating the Lambda function
- Setting environment variables
- Attaching IAM roles
- Attaching Lambda layers

## Local Development

To test Lambda functions locally:

1. Install dependencies:
```bash
pip install opensearchpy requests-aws4auth boto3
```

2. Set environment variables:
```bash
export OPENSEARCH_ENDPOINT=your-endpoint
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=amazon.titan-embed-text-v1
```

3. Test the handler:
```python
from lambda.search.index import handler

event = {
    'queryStringParameters': {
        'query': 'test'
    }
}
context = {}

result = handler(event, context)
print(result)
```

## Deployment

Lambda functions are deployed automatically via Terraform:

```bash
cd infra
terraform apply -var="env=dev"
```

Terraform will:
1. Archive each Lambda function
2. Create the Lambda function with correct handler
3. Set environment variables
4. Attach IAM roles and layers

## Monitoring

View Lambda logs in CloudWatch:

```bash
# Search Lambda
aws logs tail /aws/lambda/dev-opensearch-navco-search-search --follow

# Suggestions Lambda
aws logs tail /aws/lambda/dev-opensearch-navco-search-suggestions --follow

# Processor Lambda
aws logs tail /aws/lambda/dev-opensearch-navco-search-processor --follow

# Embedding Lambda
aws logs tail /aws/lambda/dev-opensearch-navco-search-embedding --follow

# Bootstrap Lambda
aws logs tail /aws/lambda/dev-opensearch-navco-search-index-bootstrap --follow
```

## Error Handling

All Lambda functions include:
- Comprehensive logging to CloudWatch
- Error handling with appropriate HTTP status codes
- Retry logic where applicable (e.g., Bedrock throttling)

## Updates

To update a Lambda function:

1. Edit the corresponding file in `lambda/{function-name}/index.py`
2. Run Terraform to redeploy:
```bash
cd infra
terraform apply -var="env=dev"
```

Terraform will detect the code change and redeploy the Lambda function.


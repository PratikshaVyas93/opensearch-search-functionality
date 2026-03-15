# Design: Document Ingestion, Search & Suggestions Platform

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION LAYER                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  User                                                               │
│    ├─ Upload Document → S3 Bucket                                  │
│    ├─ Query /search → API Gateway                                  │
│    └─ Query /suggestions → API Gateway                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      API LAYER (API Gateway)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  POST /search                    GET /suggestions                   │
│    ↓                                ↓                               │
│  Search Lambda                  Suggestions Lambda                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    SEARCH/QUERY LAYER (Lambdas)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Search Lambda                  Suggestions Lambda                  │
│    ├─ Query metadata-index        ├─ Query suggestions-index       │
│    ├─ Query vector-index          └─ Return top 10 suggestions     │
│    └─ Return top 10 results                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    DATA STORAGE LAYER (OpenSearch)                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  metadata-index          vector-index          suggestions-index    │
│  ├─ doc_id              ├─ embedding           ├─ suggestion_id    │
│  ├─ title               ├─ text                ├─ text             │
│  ├─ source              ├─ metadata            ├─ weight           │
│  ├─ upload_date         └─ source_uri          └─ doc_id           │
│  └─ tags                                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   INGESTION PIPELINE (Step Functions)               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  S3 Upload Event                                                    │
│    ↓                                                                │
│  Step Functions Ingestion Workflow                                  │
│    ├─ Step 1: Document Processor Lambda                            │
│    │   ├─ Read document from S3                                    │
│    │   ├─ Extract text and metadata                                │
│    │   └─ Pass to next step                                        │
│    │                                                               │
│    └─ Step 2: Embedding Generator Lambda                           │
│        ├─ Call Bedrock Embeddings                                  │
│        ├─ Write to vector-index                                    │
│        ├─ Write to metadata-index                                  │
│        └─ Write to suggestions-index                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER (Terraform)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  IAM Module              S3 Module              OpenSearch Module   │
│  ├─ Search Lambda role   ├─ Documents bucket   ├─ Collection       │
│  ├─ Suggestions role     └─ Event config       ├─ Access policies  │
│  ├─ Processor role                             └─ Encryption       │
│  ├─ Embedding role                                                 │
│  ├─ Bootstrap role                             Bedrock Module      │
│  └─ Step Functions role                        ├─ Knowledge Base    │
│                                                └─ Embeddings config │
│                                                                     │
│  Lambda Modules          Step Functions Module  API Gateway Module  │
│  ├─ Search Lambda        ├─ State machine      ├─ HTTP API         │
│  ├─ Suggestions Lambda   └─ IAM role           ├─ /search route    │
│  ├─ Processor Lambda                           └─ /suggestions     │
│  ├─ Embedding Lambda                                               │
│  └─ Bootstrap Lambda                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Terraform Module Structure

```
infra/
├── main.tf                          # Root module
├── variables.tf                     # Root variables (env, project_name, region)
├── outputs.tf                       # Root outputs
├── terraform.tfvars                 # Default values
│
├── modules/
│   ├── iam/
│   │   ├── main.tf                  # IAM roles and policies
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── s3_documents/
│   │   ├── main.tf                  # S3 bucket + event config
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── opensearch_collection/
│   │   ├── main.tf                  # OpenSearch collection
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── opensearch_index_bootstrap_lambda/
│   │   ├── main.tf                  # Bootstrap Lambda
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── lambda_function.py       # Python code
│   │
│   ├── lambda_search/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── lambda_function.py
│   │
│   ├── lambda_suggestions/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── lambda_function.py
│   │
│   ├── lambda_ingestion_processor/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── lambda_function.py
│   │
│   ├── lambda_embedding_generator/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── lambda_function.py
│   │
│   ├── step_functions_ingestion/
│   │   ├── main.tf                  # State machine
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── state_machine.json       # ASL definition
│   │
│   ├── api_gateway/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   └── bedrock_knowledge_base/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
└── .github/
    └── workflows/
        └── infra-ci-cd.yml          # GitHub Actions workflow
```

## Naming Conventions

All AWS resources follow this pattern:

```
${var.env}-${var.project_name}-{resource-type}
```

Examples:
- S3 bucket: `dev-opensearch-navco-search-documents-bucket`
- OpenSearch collection: `dev-opensearch-navco-search-collection`
- Search Lambda: `dev-opensearch-navco-search-search`
- Suggestions Lambda: `dev-opensearch-navco-search-suggestions`
- Document Processor Lambda: `dev-opensearch-navco-search-doc-processor`
- Embedding Generator Lambda: `dev-opensearch-navco-search-embedding-gen`
- Index Bootstrap Lambda: `dev-opensearch-navco-search-index-bootstrap`
- Step Functions: `dev-opensearch-navco-search-ingestion-workflow`
- API Gateway: `dev-opensearch-navco-search-api`
- IAM roles: `dev-opensearch-navco-search-{role-name}-role`

## Resource Dependencies

### Creation Sequence

1. **IAM Module** (no dependencies)
   - Creates all roles and policies
   - Outputs role ARNs

2. **S3 Module** (depends on IAM)
   - Creates S3 bucket
   - Configures S3 events
   - Outputs bucket name and ARN

3. **OpenSearch Collection Module** (depends on IAM)
   - Creates OpenSearch Serverless collection
   - Configures access policies
   - Outputs collection endpoint and ARN

4. **Index Bootstrap Lambda Module** (depends on OpenSearch Collection + IAM)
   - Creates Lambda function
   - Outputs Lambda ARN

5. **Invoke Index Bootstrap Lambda** (GitHub Actions step)
   - Calls Lambda to create indexes
   - Waits for completion

6. **Bedrock Knowledge Base Module** (depends on indexes being created)
   - Creates Knowledge Base
   - Configures Bedrock settings

7. **Ingestion Lambdas Module** (depends on IAM + S3 + OpenSearch)
   - Creates Document Processor Lambda
   - Creates Embedding Generator Lambda

8. **Step Functions Module** (depends on Ingestion Lambdas)
   - Creates state machine
   - Configures S3 event trigger

9. **Search & Suggestions Lambdas Module** (depends on IAM + OpenSearch)
   - Creates Search Lambda
   - Creates Suggestions Lambda

10. **API Gateway Module** (depends on Search & Suggestions Lambdas)
    - Creates HTTP API
    - Configures routes
    - Integrates with Lambdas

## Data Models

### metadata-index

```json
{
  "mappings": {
    "properties": {
      "doc_id": { "type": "keyword" },
      "title": { "type": "text" },
      "source": { "type": "keyword" },
      "upload_date": { "type": "date" },
      "tags": { "type": "keyword" },
      "size_bytes": { "type": "integer" }
    }
  }
}
```

### vector-index

```json
{
  "settings": { "index.knn": true },
  "mappings": {
    "properties": {
      "embedding": { "type": "knn_vector", "dimension": 1536 },
      "text": { "type": "text" },
      "doc_id": { "type": "keyword" },
      "source_uri": { "type": "keyword" }
    }
  }
}
```

### suggestions-index

```json
{
  "mappings": {
    "properties": {
      "suggestion_id": { "type": "keyword" },
      "text": { "type": "completion" },
      "weight": { "type": "integer" },
      "doc_id": { "type": "keyword" }
    }
  }
}
```

## GitHub Actions Workflow

### Trigger
- `workflow_dispatch` with inputs:
  - `environment`: dev, stg, prod
  - `branch`: git branch to deploy

### Environment Variables
```
TF_VAR_env = ${environment}
TF_VAR_project_name = opensearch-navco-search
AWS_ACCESS_KEY_ID = ${secrets.AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY = ${secrets.AWS_SECRET_ACCESS_KEY}
AWS_DEFAULT_REGION = us-east-1
```

### Workflow Stages

1. **Checkout** - Clone repository at specified branch
2. **Setup Terraform** - Install Terraform
3. **Terraform Init** - Initialize Terraform
4. **Terraform Plan** - Plan infrastructure changes
5. **Terraform Apply - Core Infrastructure**
   - IAM roles and policies
   - S3 bucket
   - OpenSearch collection
   - Index Bootstrap Lambda
6. **Invoke Index Bootstrap Lambda** - Create OpenSearch indexes
7. **Terraform Apply - Dependent Infrastructure**
   - Bedrock Knowledge Base
   - Ingestion Lambdas
   - Step Functions
   - Search & Suggestions Lambdas
   - API Gateway
8. **Output Summary** - Display deployment results

## Error Handling

### Lambda Functions
- All Lambdas return HTTP 502 on errors
- All Lambdas log errors to CloudWatch
- All Lambdas implement retry logic where appropriate

### Step Functions
- State machine handles Lambda failures
- State machine retries on transient errors
- State machine logs all executions

### Bedrock Integration
- Embedding Generator implements exponential backoff
- Handles ThrottlingException gracefully
- Retries up to 3 times

## Security Considerations

- AWS credentials via GitHub secrets (not hardcoded)
- IAM roles with least-privilege permissions
- OpenSearch collection encrypted
- No sensitive data in logs
- S3 bucket versioning enabled
- Public access blocked on S3

## Performance Targets

- Search Lambda: < 2 seconds response time
- Suggestions Lambda: < 500ms response time
- Document processing: < 5 minutes per document
- Concurrent Lambda executions: auto-scaled
- OpenSearch queries: < 1 second

## Monitoring & Logging

- All Lambdas log to CloudWatch
- Step Functions logs to CloudWatch
- API Gateway logs to CloudWatch
- CloudWatch alarms for errors (optional)
- X-Ray tracing for debugging (optional)

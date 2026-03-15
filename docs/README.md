# RAG Pipeline Infrastructure Documentation

## Overview

The RAG (Retrieval-Augmented Generation) pipeline is a complete AWS infrastructure for document ingestion, semantic search, and LLM-powered answer generation. The system is divided into two logical halves:

**Ingestion Pipeline**: Documents uploaded to S3 trigger an automated workflow that extracts metadata, generates suggestions, and creates vector embeddings for semantic search.

**Search Pipeline**: Users query the system through API endpoints that retrieve relevant documents and generate contextual answers using Claude 3 Haiku via Bedrock Agent Runtime.

All infrastructure is provisioned with Terraform using a modular architecture, with resource names managed via environment variables using the `opensearch-project-dev` prefix.

---

## Architecture

### High-Level Overview

The system consists of 11 AWS components working together in two distinct flows:

```
INGESTION FLOW:
S3 Bucket → EventBridge Rule → Step Functions → Indexer Lambda → OpenSearch
                                                                  ↓
                                                    Bedrock Knowledge Base
                                                    (async chunking & embedding)

SEARCH FLOW:
API Gateway → Search Lambda → OpenSearch → RAG Lambda → Bedrock Agent Runtime
           ↓
        Suggestions Lambda → OpenSearch
```

### Deployment Order

Infrastructure is deployed in strict dependency order:

1. **backend** — S3 state bucket and DynamoDB lock table
2. **s3** — Document storage bucket
3. **opensearch** — OpenSearch Serverless collection
4. **python index script** — Creates three OpenSearch indexes
5. **bedrock** — Bedrock Knowledge Base with Titan Embeddings
6. **eventbridge** — EventBridge rule and Step Functions state machine
7. **lambda** — All four Lambda functions
8. **apigateway** — HTTP API with /search and /suggestions routes

---

## Components

### 1. S3 Bucket

**Purpose**: Stores raw documents and metadata for ingestion.

**Configuration**:
- Versioning enabled for document history
- Public access blocked for security
- Triggers ObjectCreated events to EventBridge

**Environment Variable**: `TF_VAR_bucket_name` (e.g., `opensearch-project-dev-bucket`)

**Outputs**: Bucket name and ARN for downstream modules

---

### 2. EventBridge Rule

**Purpose**: Detects S3 ObjectCreated events and triggers the ingestion pipeline.

**Configuration**:
- Listens for `s3:ObjectCreated:*` events from the document bucket
- Routes events to Step Functions state machine
- Passes S3 event details as state machine input

**Outputs**: Rule ARN for monitoring and debugging

---

### 3. Step Functions State Machine

**Purpose**: Orchestrates the ingestion workflow with a single task.

**Definition**:
```json
{
  "Comment": "Ingestion pipeline - index document metadata and suggestions",
  "StartAt": "InvokeIndexer",
  "States": {
    "InvokeIndexer": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName.$": "$.Execution.Input.indexer_function_name",
        "Payload.$": "$"
      },
      "End": true
    }
  }
}
```

**Execution Flow**:
1. Receives S3 event from EventBridge
2. Invokes Indexer Lambda with event payload
3. Marks execution as FAILED if Lambda raises an exception
4. Marks execution as SUCCEEDED if Lambda completes normally

**Outputs**: State machine ARN for monitoring

---

### 4. Indexer Lambda

**Purpose**: Writes document metadata and suggestions to OpenSearch.

**Responsibilities**:
- Extracts metadata from S3 event (document key, upload timestamp)
- Generates suggestion entries from document title
- Writes metadata to `metadata-index`
- Writes suggestions to `suggestions-index`
- Raises exception on OpenSearch write failure (causes Step Functions execution to fail)

**Environment Variables**:
- `OPENSEARCH_ENDPOINT` — OpenSearch collection endpoint
- `OPENSEARCH_REGION` — AWS region for signing requests

**Error Handling**: Raises exception on OpenSearch errors; Step Functions marks execution as FAILED

---

### 5. OpenSearch Serverless Collection

**Purpose**: Hosts three indexes for metadata, suggestions, and vector embeddings.

**Configuration**:
- Encryption at rest enabled
- Access policies restrict to Lambda functions and Bedrock Knowledge Base
- Serverless capacity for automatic scaling

**Three Indexes**:

#### chunk-index
Stores vector embeddings from Bedrock Knowledge Base (Titan Embeddings, 1536 dimensions).

```json
{
  "settings": { "index.knn": true },
  "mappings": {
    "properties": {
      "id":         { "type": "keyword" },
      "text":       { "type": "text" },
      "embedding":  { "type": "knn_vector", "dimension": 1536 },
      "source_uri": { "type": "keyword" },
      "chunk_seq":  { "type": "integer" }
    }
  }
}
```

#### metadata-index
Stores per-document metadata written by Indexer Lambda.

```json
{
  "mappings": {
    "properties": {
      "doc_id":      { "type": "keyword" },
      "s3_key":      { "type": "keyword" },
      "title":       { "type": "text" },
      "uploaded_at": { "type": "date" },
      "tags":        { "type": "keyword" }
    }
  }
}
```

#### suggestions-index
Stores autocomplete suggestions written by Indexer Lambda.

```json
{
  "mappings": {
    "properties": {
      "suggestion_id": { "type": "keyword" },
      "text":          { "type": "completion" },
      "doc_id":        { "type": "keyword" },
      "weight":        { "type": "integer" }
    }
  }
}
```

**Environment Variable**: `TF_VAR_collection_name` (e.g., `opensearch-project-dev-collection`)

**Outputs**: Collection endpoint and ARN

---

### 6. Bedrock Knowledge Base

**Purpose**: Automatically chunks documents and generates vector embeddings.

**Configuration**:
- Model: Titan Embeddings (1536 dimensions)
- Data source: S3 bucket
- Vector store: OpenSearch `chunk-index`
- Runs asynchronously after document upload

**Workflow**:
1. Detects new documents in S3
2. Chunks documents into semantic segments
3. Generates embeddings for each chunk using Titan
4. Stores embeddings in `chunk-index`

**Environment Variable**: `TF_VAR_knowledge_base_name` (e.g., `opensearch-project-dev-kb`)

**Outputs**: Knowledge Base ID for Bedrock Agent Runtime

---

### 7. API Gateway

**Purpose**: Exposes HTTP endpoints for search and suggestions.

**Routes**:
- `POST /search` — Search for documents and generate answers
- `GET /suggestions` — Get autocomplete suggestions

**Configuration**:
- HTTP API (not REST API)
- No authentication required
- Lambda integrations for both routes
- CORS enabled for cross-origin requests

**Environment Variable**: `TF_VAR_api_name` (e.g., `opensearch-project-dev-api`)

**Outputs**: API endpoint URL (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com`)

---

### 8. Search Lambda

**Purpose**: Queries OpenSearch and invokes RAG Lambda for answer generation.

**Request Payload**:
```json
{
  "query": "What is machine learning?",
  "context_limit": 5,
  "filters": {
    "tags": ["tutorial"]
  }
}
```

**Responsibilities**:
1. Validates request payload
2. Queries `chunk-index` for semantic matches (KNN search)
3. Queries `metadata-index` for document metadata
4. Invokes RAG Lambda with retrieved context
5. Returns results with generated answer

**Response**:
```json
{
  "results": [
    {
      "doc_id": "doc-123",
      "title": "ML Basics",
      "chunk_text": "Machine learning is...",
      "relevance_score": 0.92
    }
  ],
  "generated_answer": "Machine learning is a subset of artificial intelligence..."
}
```

**Error Handling**: Returns HTTP 502 with error details on OpenSearch failure

**Environment Variables**:
- `OPENSEARCH_ENDPOINT` — OpenSearch collection endpoint
- `RAG_LAMBDA_NAME` — Name of RAG Lambda function

---

### 9. Suggestions Lambda

**Purpose**: Provides autocomplete suggestions from the suggestions index.

**Request**: `GET /suggestions?q=mach&limit=10`

**Responsibilities**:
1. Validates query parameter
2. Queries `suggestions-index` for completion matches
3. Returns sorted suggestions by weight

**Response**:
```json
{
  "suggestions": [
    {
      "text": "machine learning",
      "weight": 95,
      "doc_id": "doc-123"
    },
    {
      "text": "machine vision",
      "weight": 42,
      "doc_id": "doc-456"
    }
  ]
}
```

**Error Handling**: Returns HTTP 502 with error details on OpenSearch failure

**Environment Variable**: `OPENSEARCH_ENDPOINT` — OpenSearch collection endpoint

---

### 10. RAG Lambda

**Purpose**: Invokes Bedrock Agent Runtime to generate LLM-powered answers.

**Input** (from Search Lambda):
```json
{
  "query": "What is machine learning?",
  "context": [
    "Machine learning is a subset of artificial intelligence...",
    "ML algorithms learn patterns from data..."
  ]
}
```

**Responsibilities**:
1. Constructs prompt with query and context
2. Invokes Bedrock Agent Runtime with Claude 3 Haiku
3. Implements retry logic (up to 3 attempts with exponential backoff)
4. Returns generated answer

**Output**:
```json
{
  "generated_answer": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed..."
}
```

**Error Handling**: Returns HTTP 503 on Bedrock errors; Search Lambda retries with backoff

**Environment Variables**:
- `BEDROCK_MODEL_ID` — Claude 3 Haiku model ID
- `BEDROCK_REGION` — AWS region for Bedrock

---

### 11. Bedrock Agent Runtime

**Purpose**: Generates contextual answers using Claude 3 Haiku.

**Model**: `anthropic.claude-3-haiku-20240307-v1:0`

**Capabilities**:
- Processes natural language queries
- Generates answers based on provided context
- Supports streaming responses
- Handles multi-turn conversations

**Integration**: Called by RAG Lambda with retrieved document context

---

## Data Flow

### Ingestion Flow (Document Upload)

```
1. User uploads document to S3 bucket
   ↓
2. S3 triggers ObjectCreated event
   ↓
3. EventBridge Rule detects event
   ↓
4. EventBridge invokes Step Functions state machine
   ↓
5. Step Functions invokes Indexer Lambda
   ↓
6. Indexer Lambda writes to metadata-index and suggestions-index
   ↓
7. Bedrock Knowledge Base (async) chunks document and generates embeddings
   ↓
8. Embeddings stored in chunk-index
```

**Timeline**: Metadata indexing completes in seconds; embedding generation takes minutes.

### Search Flow (User Query)

```
1. User sends POST /search request to API Gateway
   ↓
2. API Gateway routes to Search Lambda
   ↓
3. Search Lambda queries chunk-index (KNN search for semantic matches)
   ↓
4. Search Lambda queries metadata-index (retrieves document metadata)
   ↓
5. Search Lambda invokes RAG Lambda with retrieved context
   ↓
6. RAG Lambda invokes Bedrock Agent Runtime
   ↓
7. Claude 3 Haiku generates answer based on context
   ↓
8. RAG Lambda returns generated answer to Search Lambda
   ↓
9. Search Lambda returns results and answer to API Gateway
   ↓
10. API Gateway returns response to user
```

**Timeline**: Complete search and answer generation takes 2-5 seconds.

### Suggestions Flow (Autocomplete)

```
1. User sends GET /suggestions?q=query request to API Gateway
   ↓
2. API Gateway routes to Suggestions Lambda
   ↓
3. Suggestions Lambda queries suggestions-index (completion search)
   ↓
4. Suggestions Lambda returns sorted suggestions to API Gateway
   ↓
5. API Gateway returns suggestions to user
```

**Timeline**: Suggestions returned in <500ms.

---

## End-to-End Test Guide

### Prerequisites

- AWS credentials configured with appropriate permissions
- Terraform infrastructure deployed via `deploy.yml` workflow
- API endpoint URL from Terraform outputs
- S3 bucket name from Terraform outputs
- OpenSearch endpoint from Terraform outputs

### Test 1: Document Upload and Ingestion

**Objective**: Verify the ingestion pipeline processes documents correctly.

**Steps**:

1. Create a test document file:
   ```bash
   cat > test-document.txt << 'EOF'
   Machine Learning Fundamentals
   
   Machine learning is a subset of artificial intelligence that enables
   systems to learn and improve from experience without being explicitly
   programmed. ML algorithms identify patterns in data and make predictions
   or decisions based on those patterns.
   EOF
   ```

2. Upload to S3:
   ```bash
   aws s3 cp test-document.txt s3://opensearch-project-dev-bucket/documents/
   ```

3. Monitor Step Functions execution:
   ```bash
   aws stepfunctions list-executions \
     --state-machine-arn <STATE_MACHINE_ARN> \
     --query 'executions[0]'
   ```

4. Verify execution completed successfully (status: SUCCEEDED)

5. Query metadata-index to confirm metadata was indexed:
   ```bash
   curl -X GET "https://<OPENSEARCH_ENDPOINT>/metadata-index/_search" \
     -H "Content-Type: application/json" \
     -d '{"query": {"match_all": {}}}'
   ```

**Expected Result**: Metadata document appears in metadata-index with fields: doc_id, s3_key, title, uploaded_at, tags.

---

### Test 2: Suggestions Endpoint

**Objective**: Verify the suggestions endpoint returns autocomplete suggestions.

**Steps**:

1. Query suggestions endpoint:
   ```bash
   curl -X GET "https://<API_ENDPOINT>/suggestions?q=mach&limit=10"
   ```

2. Verify response structure

**Expected Response**:
```json
{
  "suggestions": [
    {
      "text": "machine learning",
      "weight": 95,
      "doc_id": "doc-123"
    },
    {
      "text": "machine vision",
      "weight": 42,
      "doc_id": "doc-456"
    }
  ]
}
```

**Expected Result**: HTTP 200 with array of suggestions sorted by relevance.

---

### Test 3: Search Endpoint

**Objective**: Verify the search endpoint retrieves documents and generates answers.

**Steps**:

1. Send search request:
   ```bash
   curl -X POST "https://<API_ENDPOINT>/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is machine learning?",
       "context_limit": 5,
       "filters": {}
     }'
   ```

2. Verify response structure

3. Check that generated_answer contains relevant information

**Expected Response**:
```json
{
  "results": [
    {
      "doc_id": "doc-123",
      "title": "Machine Learning Fundamentals",
      "chunk_text": "Machine learning is a subset of artificial intelligence...",
      "relevance_score": 0.92
    }
  ],
  "generated_answer": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed..."
}
```

**Expected Result**: HTTP 200 with search results and LLM-generated answer.

---

## Sample Requests and Responses

### Search Request

```bash
curl -X POST "https://abc123.execute-api.us-east-1.amazonaws.com/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do neural networks work?",
    "context_limit": 5,
    "filters": {
      "tags": ["ai", "ml"]
    }
  }'
```

### Search Response

```json
{
  "results": [
    {
      "doc_id": "doc-001",
      "title": "Deep Learning Basics",
      "chunk_text": "Neural networks are computational models inspired by biological neurons. They consist of interconnected layers of nodes that process information through weighted connections.",
      "relevance_score": 0.95,
      "source_uri": "s3://opensearch-project-dev-bucket/documents/deep-learning.pdf"
    },
    {
      "doc_id": "doc-002",
      "title": "AI Fundamentals",
      "chunk_text": "Artificial neural networks are mathematical models that mimic the structure and function of biological neural networks found in animal brains.",
      "relevance_score": 0.87,
      "source_uri": "s3://opensearch-project-dev-bucket/documents/ai-intro.pdf"
    }
  ],
  "generated_answer": "Neural networks are computational models inspired by biological neurons. They work by processing information through interconnected layers of nodes with weighted connections. Each node receives inputs, applies a mathematical function (activation function), and passes the output to the next layer. Through training, the network adjusts these weights to minimize prediction errors, enabling it to learn complex patterns in data."
}
```

### Suggestions Request

```bash
curl -X GET "https://abc123.execute-api.us-east-1.amazonaws.com/suggestions?q=neural&limit=5"
```

### Suggestions Response

```json
{
  "suggestions": [
    {
      "text": "neural networks",
      "weight": 98,
      "doc_id": "doc-001"
    },
    {
      "text": "neural network training",
      "weight": 85,
      "doc_id": "doc-001"
    },
    {
      "text": "neural architecture",
      "weight": 72,
      "doc_id": "doc-003"
    }
  ]
}
```

---

## Troubleshooting

### Issue: Step Functions Execution Fails

**Symptoms**: Step Functions execution shows FAILED status.

**Diagnosis**:
1. Check Step Functions execution details for error message
2. Review Indexer Lambda CloudWatch logs
3. Verify OpenSearch collection is accessible

**Solutions**:
- Verify OpenSearch endpoint is correct in Lambda environment variables
- Check IAM role permissions for Indexer Lambda
- Ensure OpenSearch indexes exist (run index creation script manually if needed)

### Issue: Search Returns No Results

**Symptoms**: Search endpoint returns empty results array.

**Diagnosis**:
1. Verify documents were uploaded to S3
2. Check that Bedrock Knowledge Base has processed documents
3. Query chunk-index directly to verify embeddings exist

**Solutions**:
- Wait for Bedrock Knowledge Base to complete async processing (can take several minutes)
- Verify S3 bucket name matches Knowledge Base configuration
- Check OpenSearch collection access policies

### Issue: API Gateway Returns 502 Error

**Symptoms**: API endpoints return HTTP 502 Bad Gateway.

**Diagnosis**:
1. Check Lambda function CloudWatch logs
2. Verify Lambda has correct environment variables
3. Check Lambda timeout settings

**Solutions**:
- Increase Lambda timeout (default 30s may be insufficient for Bedrock calls)
- Verify OpenSearch and Bedrock endpoints are accessible from Lambda VPC
- Check IAM role permissions for Lambda functions

### Issue: Bedrock Agent Runtime Throttling

**Symptoms**: Search requests occasionally fail with 503 errors.

**Diagnosis**:
1. Check CloudWatch logs for throttling errors
2. Monitor Bedrock API usage

**Solutions**:
- RAG Lambda implements exponential backoff retry logic (up to 3 attempts)
- Consider increasing Bedrock provisioned throughput
- Implement request queuing for high-volume scenarios

### Issue: OpenSearch Collection Timeout

**Symptoms**: Search queries timeout or return 504 errors.

**Diagnosis**:
1. Check OpenSearch collection metrics in AWS Console
2. Monitor query latency in CloudWatch

**Solutions**:
- Increase OpenSearch Serverless capacity
- Optimize KNN search parameters (reduce context_limit)
- Add indexes for frequently filtered fields

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INGESTION PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐      ┌──────────────┐      ┌──────────────┐          │
│  │    S3    │─────▶│ EventBridge  │─────▶│ Step         │          │
│  │  Bucket  │      │    Rule      │      │ Functions    │          │
│  └──────────┘      └──────────────┘      └──────┬───────┘          │
│                                                  │                  │
│                                                  ▼                  │
│                                          ┌──────────────┐           │
│                                          │   Indexer    │           │
│                                          │   Lambda     │           │
│                                          └──────┬───────┘           │
│                                                  │                  │
│                                    ┌─────────────┴──────────────┐   │
│                                    ▼                            ▼   │
│                          ┌──────────────────┐      ┌──────────────┐│
│                          │  metadata-index  │      │suggestions-  ││
│                          │  suggestions-    │      │index         ││
│                          │  index           │      └──────────────┘│
│                          └──────────────────┘                      │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Bedrock Knowledge Base (async)                              │  │
│  │  - Chunks documents                                          │  │
│  │  - Generates Titan embeddings (1536 dims)                   │  │
│  │  - Stores in chunk-index                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          SEARCH PIPELINE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐                                                   │
│  │ API Gateway  │                                                   │
│  │ /search      │                                                   │
│  │ /suggestions │                                                   │
│  └──────┬───────┘                                                   │
│         │                                                            │
│    ┌────┴────┐                                                      │
│    ▼         ▼                                                      │
│ ┌──────────┐ ┌──────────────┐                                       │
│ │ Search   │ │ Suggestions  │                                       │
│ │ Lambda   │ │ Lambda       │                                       │
│ └────┬─────┘ └──────┬───────┘                                       │
│      │              │                                               │
│      ▼              ▼                                               │
│ ┌──────────────────────────────────────────────────────────────┐   │
│ │         OpenSearch Serverless Collection                     │   │
│ │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │   │
│ │  │ chunk-index  │  │metadata-index│  │suggestions- │       │   │
│ │  │(embeddings)  │  │(metadata)    │  │index        │       │   │
│ │  └──────────────┘  └──────────────┘  └──────────────┘       │   │
│ └──────────────────────────────────────────────────────────────┘   │
│      │                                                              │
│      ▼                                                              │
│ ┌──────────────┐                                                   │
│ │ RAG Lambda   │                                                   │
│ └──────┬───────┘                                                   │
│        │                                                            │
│        ▼                                                            │
│ ┌──────────────────────────────────────────────────────────────┐   │
│ │  Bedrock Agent Runtime (Claude 3 Haiku)                      │   │
│ │  - Generates contextual answers                              │   │
│ │  - Uses retrieved document context                           │   │
│ │  - Implements retry logic with exponential backoff           │   │
│ └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Environment Variables Reference

All resource names are configured via environment variables with the `opensearch-project-dev` prefix:

| Variable | Example Value | Used By |
|---|---|---|
| TF_VAR_state_bucket_name | opensearch-project-dev-tf-state | Terraform backend |
| TF_VAR_lock_table_name | opensearch-project-dev-tf-lock | Terraform backend |
| TF_VAR_bucket_name | opensearch-project-dev-bucket | S3, Bedrock KB |
| TF_VAR_collection_name | opensearch-project-dev-collection | OpenSearch |
| TF_VAR_knowledge_base_name | opensearch-project-dev-kb | Bedrock |
| TF_VAR_search_lambda_name | opensearch-project-dev-search | Lambda, API Gateway |
| TF_VAR_suggestions_lambda_name | opensearch-project-dev-suggestions | Lambda, API Gateway |
| TF_VAR_rag_lambda_name | opensearch-project-dev-rag | Lambda |
| TF_VAR_indexer_lambda_name | opensearch-project-dev-indexer | Lambda, Step Functions |
| TF_VAR_api_name | opensearch-project-dev-api | API Gateway |
| OPENSEARCH_ENDPOINT | https://abc123.us-east-1.aoss.amazonaws.com | Lambda functions, index script |
| BEDROCK_MODEL_ID | anthropic.claude-3-haiku-20240307-v1:0 | RAG Lambda |

---

## Additional Resources

- [AWS OpenSearch Serverless Documentation](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/latest/dg/)
- [AWS Step Functions Documentation](https://docs.aws.amazon.com/step-functions/latest/dg/)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

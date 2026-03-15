# Design Document: RAG Pipeline Infrastructure

## Overview

This design covers the complete AWS infrastructure for a Retrieval-Augmented Generation (RAG) pipeline. The system has two logical halves:

1. **Ingestion pipeline** — S3 receives uploaded documents, EventBridge detects the upload, triggers a Step Functions state machine, which invokes the Indexer Lambda to write metadata and suggestions into OpenSearch. Bedrock Knowledge Base independently reads from S3, chunks documents, generates Titan embeddings, and stores vectors in the chunk index.

2. **Search/retrieval pipeline** — API Gateway exposes `/search` and `/suggestions`. Each route proxies to a dedicated Lambda. A separate RAG Lambda invokes Bedrock Agent Runtime to produce LLM-generated answers using retrieved context.

All AWS resources are provisioned with Terraform using a modular layout. OpenSearch indexes are created by a Python 3.13 script run as a GitHub Actions step between the OpenSearch and Bedrock Terraform modules. A single `deploy.yml` workflow orchestrates the full deployment in dependency order.

Resource naming prefix: `opensearch-project-dev`. All names are passed via environment variables — nothing is hardcoded.

---

## Architecture

### Deployment Order

```
backend -> s3 -> opensearch -> [python index script] -> bedrock -> eventbridge -> lambda -> apigateway
```

Each step depends on outputs from the previous step(s). The index script runs between `opensearch` and `bedrock` to ensure indexes exist before the Knowledge Base is configured.

### Data Flow

**Ingestion path:**
S3 ObjectCreated event -> EventBridge Rule -> Step Functions state machine -> Indexer Lambda -> OpenSearch (metadata-index, suggestions-index)

Bedrock Knowledge Base (async): S3 -> chunk + embed (Titan) -> OpenSearch chunk-index

**Search path:**
Client -> API Gateway /search -> Search Lambda -> OpenSearch (chunk-index + metadata-index) -> RAG Lambda -> Bedrock Agent Runtime (Claude 3 Haiku) -> response

Client -> API Gateway /suggestions -> Suggestions Lambda -> OpenSearch suggestions-index -> response

---

## Components and Interfaces

### Terraform Modules

| Module | Path | Provisions |
|---|---|---|
| backend | terraform/backend/ | S3 state bucket, DynamoDB lock table |
| s3 | terraform/s3/ | Document storage bucket |
| opensearch | terraform/opensearch/ | OpenSearch Serverless collection, encryption + access policies |
| bedrock | terraform/bedrock/ | Bedrock Knowledge Base (Titan Embeddings), IAM roles |
| eventbridge | terraform/eventbridge/ | EventBridge rule, Step Functions state machine |
| lambda | terraform/lambda/ | search-proxy, suggestions-proxy, rag-proxy, indexer Lambdas |
| apigateway | terraform/apigateway/ | HTTP API with /search and /suggestions routes only |

Each module exposes outputs consumed by downstream modules. No module hardcodes resource names.

### Module Input/Output Contract

```
backend    -> outputs: state_bucket_name, lock_table_name
s3         -> outputs: bucket_name, bucket_arn
opensearch -> outputs: collection_endpoint, collection_arn
bedrock    -> outputs: knowledge_base_id
eventbridge -> outputs: state_machine_arn, rule_arn
lambda     -> outputs: search_lambda_arn, suggestions_lambda_arn,
                       rag_lambda_arn, indexer_lambda_arn
apigateway -> outputs: api_endpoint_url
```

### Lambda Functions

| Function | Trigger | Responsibility |
|---|---|---|
| search-proxy | API Gateway /search | Queries OpenSearch chunk-index + metadata-index; calls RAG Lambda |
| suggestions-proxy | API Gateway /suggestions | Queries OpenSearch suggestions-index |
| rag-proxy | Internal (called by search-proxy) | Invokes Bedrock Agent Runtime (Claude 3 Haiku) with retrieved context |
| indexer | Step Functions Task state | Writes metadata to metadata-index and suggestions to suggestions-index |

### Step Functions State Machine (minimal ASL)

```json
{
  "Comment": "Ingestion pipeline - index document metadata and suggestions",
  "StartAt": "InvokeIndexer",
  "States": {
    "InvokeIndexer": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName.$": "$$.Execution.Input.indexer_function_name",
        "Payload.$": "$"
      },
      "End": true
    }
  }
}
```

### API Gateway Routes

| Method | Route | Lambda Integration |
|---|---|---|
| POST | /search | search-proxy |
| GET | /suggestions | suggestions-proxy |

No /upload or /coach routes are provisioned.

### GitHub Actions Workflow

File: `.github/workflows/deploy.yml`

Trigger: `workflow_dispatch` with two inputs:
- `environment` — target environment name (e.g., dev, prod)
- `branch` — Git branch to deploy from

Steps (in order):
1. Checkout at selected branch
2. terraform apply — backend/
3. terraform apply — s3/
4. terraform apply — opensearch/
5. Setup Python 3.13, pip install -r scripts/requirements.txt, run scripts/create_indexes.py
6. terraform apply — bedrock/
7. terraform apply — eventbridge/
8. terraform apply — lambda/
9. terraform apply — apigateway/

Each step uses `continue-on-error: false` so a failure halts the workflow. Outputs from earlier Terraform steps are captured and exported as environment variables for later steps.

### Index Creation Script

File: `scripts/create_indexes.py` (Python 3.13)

- Reads `OPENSEARCH_ENDPOINT` from environment (or CLI arg)
- Creates chunk-index, metadata-index, suggestions-index via OpenSearch REST API
- If an index already exists (HTTP 400 with `resource_already_exists_exception`), skips silently
- On any other API error, prints a descriptive message and exits with non-zero status
- Dependencies listed in `scripts/requirements.txt` (opensearch-py, boto3, requests-aws4auth)

---

## Data Models

### OpenSearch Indexes

#### chunk-index

Stores vector embeddings produced by Bedrock Knowledge Base (Titan Embeddings, 1536 dimensions).

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

Stores per-document metadata written by the Indexer Lambda.

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

Stores suggestion entries written by the Indexer Lambda.

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

### Environment Variables (naming contract)

All modules and scripts read resource names from environment variables.

| Variable | Example Value |
|---|---|
| TF_VAR_state_bucket_name | opensearch-project-dev-tf-state |
| TF_VAR_lock_table_name | opensearch-project-dev-tf-lock |
| TF_VAR_bucket_name | opensearch-project-dev-bucket |
| TF_VAR_collection_name | opensearch-project-dev-collection |
| TF_VAR_knowledge_base_name | opensearch-project-dev-kb |
| TF_VAR_search_lambda_name | opensearch-project-dev-search |
| TF_VAR_suggestions_lambda_name | opensearch-project-dev-suggestions |
| TF_VAR_rag_lambda_name | opensearch-project-dev-rag |
| TF_VAR_indexer_lambda_name | opensearch-project-dev-indexer |
| TF_VAR_api_name | opensearch-project-dev-api |
| OPENSEARCH_ENDPOINT | (captured from opensearch module output) |
| BEDROCK_MODEL_ID | anthropic.claude-3-haiku-20240307-v1:0 |


---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Index script creates all three indexes with correct mappings

*For any* valid OpenSearch endpoint, when `create_indexes.py` is executed, it must issue PUT requests for exactly three indexes (`chunk-index`, `metadata-index`, `suggestions-index`), and the request body for `chunk-index` must contain a `knn_vector` field mapping with a `dimension` value.

**Validates: Requirements 5.1, 5.6**

### Property 2: Index script error handling is exhaustive

*For any* HTTP response from the OpenSearch API, the script must exit with status 0 if and only if the response indicates success (2xx) or index-already-exists (HTTP 400 with `resource_already_exists_exception`); for all other responses the script must exit with a non-zero status code and print a descriptive error message.

**Validates: Requirements 5.3, 5.4**

### Property 3: API Gateway exposes exactly /search and /suggestions

*For any* deployment of the `apigateway/` Terraform module, the set of configured routes must equal exactly `{POST /search, GET /suggestions}` — no more, no fewer. In particular, `/upload` and `/coach` must not appear.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

### Property 4: Deployment workflow step ordering is correct

*For any* execution of the `deploy.yml` workflow, the sequence of deployment steps must follow the order: `backend` → `s3` → `opensearch` → index script → `bedrock` → `eventbridge` → `lambda` → `apigateway`, and no step may begin before the preceding step has completed successfully.

**Validates: Requirements 9.2, 9.5**

---

## Error Handling

### Terraform Module Errors

- Each Terraform module is applied independently in the workflow. If `terraform apply` exits non-zero, the GitHub Actions step fails and the workflow halts (`continue-on-error: false` on every step).
- Partial state is preserved in the remote backend so a re-run can resume from the failed module.

### Index Script Errors

- HTTP 400 with `resource_already_exists_exception` → log "index already exists, skipping" and continue.
- Any other non-2xx response → print `"ERROR creating <index_name>: <status_code> <response_body>"` and call `sys.exit(1)`.
- Network/connection errors → propagate the exception (Python default), which also results in non-zero exit.

### Lambda Runtime Errors

- **search-proxy**: If OpenSearch returns an error, return HTTP 502 with a structured error body `{"error": "search_failed", "detail": "<message>"}`.
- **suggestions-proxy**: Same pattern — HTTP 502 on OpenSearch error.
- **rag-proxy**: If Bedrock Agent Runtime returns an error or throttles, return HTTP 503 with `{"error": "generation_failed", "detail": "<message>"}`. Retries are handled by the caller (search-proxy) with exponential backoff up to 3 attempts.
- **indexer**: On OpenSearch write failure, raise an exception so Step Functions marks the execution as FAILED and the error is visible in the console.

### API Gateway Errors

- API Gateway returns HTTP 400 for malformed requests (missing required fields).
- Lambda integration timeouts surface as HTTP 504.
- No custom authorizer is in scope; all routes are unauthenticated in this design.

---

## Testing Strategy

### Dual Testing Approach

Both unit tests and property-based tests are required. They are complementary:
- Unit tests verify specific examples, integration points, and edge cases.
- Property tests verify universal behaviors across many generated inputs.

### Unit Tests

Focus areas:
- Index script: verify correct HTTP method, path, and body for each of the three index creation calls (using a mock HTTP client).
- Index script: verify exit code 0 on already-exists response, exit code 1 on generic 500 response.
- Lambda handlers: verify correct OpenSearch query construction for a known input.
- Lambda handlers: verify correct Bedrock invocation payload for a known search result.
- Workflow YAML: parse and assert step names appear in the required order.

### Property-Based Tests

Library: **Hypothesis** (Python) for the index script; **pytest-hypothesis** for Lambda unit tests.

Each property test must run a minimum of 100 iterations.

Tag format for each test: `Feature: rag-pipeline-infrastructure, Property <N>: <property_text>`

| Property | Test Description |
|---|---|
| Property 1 | Generate random valid endpoint strings; assert the script issues PUT calls for all three index names and that the chunk-index body contains `knn_vector` with a numeric `dimension`. |
| Property 2 | Generate random HTTP status codes and response bodies; assert exit code is 0 iff status is 2xx or (400 + already-exists body), non-zero otherwise. |
| Property 3 | Parse the Terraform `apigateway/` HCL; assert the set of route keys equals `{POST /search, GET /suggestions}` for any valid variable substitution. |
| Property 4 | Parse `deploy.yml`; assert the step sequence satisfies the required partial order for any valid workflow_dispatch input combination. |

### Integration Tests (manual, post-deploy)

Described in `docs/README.md`:
1. Upload a test document to the S3 bucket and verify a Step Functions execution completes.
2. Query `GET /suggestions?q=test` and verify a 200 response with a JSON array.
3. Query `POST /search` with a sample payload and verify a 200 response containing a `results` array and a `generated_answer` field.

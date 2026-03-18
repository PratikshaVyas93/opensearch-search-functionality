# Document Search Platform — Architecture Explainer
## For Stakeholders and Technical Team

---

## What This System Does (Plain English)

This platform lets users search through a library of uploaded documents using natural language. When a document is uploaded to cloud storage, the system automatically processes it, converts it into a searchable format using AI, and stores it in a search engine. Users can then search for content or get autocomplete suggestions through a REST API.

There are two main flows:
- **Ingestion flow** — a document is uploaded → automatically processed → indexed for search
- **Search flow** — a user sends a query → Lambda searches OpenSearch → results returned via API

---

## How the Code is Organized

```
project/
├── src/                        # All Lambda function business logic (Python)
│   ├── bootstrap/index.py      # One-time setup: creates OpenSearch indexes
│   ├── search/index.py         # Handles search API requests
│   ├── suggestions/index.py    # Handles autocomplete API requests
│   ├── processor/index.py      # Extracts text from uploaded documents
│   └── embedding/index.py      # Generates AI embeddings, writes to OpenSearch
│
├── infra/                      # All AWS infrastructure as code (Terraform)
│   ├── main.tf                 # Root module — wires everything together
│   ├── variables.tf            # Input variables (env, region, project name)
│   ├── outputs.tf              # Exported values (API URL, Lambda names, etc.)
│   ├── terraform.tfvars        # Actual values: env=dev, region=us-east-1
│   ├── lambda_layers/          # Shared Python dependencies (opensearch-py)
│   └── modules/                # One folder per AWS service
│       ├── s3_documents/       # S3 bucket for document uploads
│       ├── opensearch_collection/  # OpenSearch Serverless collection
│       ├── iam/                # IAM roles and permissions
│       ├── src_bootstrap/      # Bootstrap Lambda deployment
│       ├── src_search/         # Search Lambda deployment
│       ├── src_suggestions/    # Suggestions Lambda deployment
│       ├── src_processor/      # Processor Lambda deployment
│       ├── src_embedding/      # Embedding Lambda deployment
│       ├── step_functions_ingestion/  # Ingestion workflow orchestration
│       └── api_gateway/        # HTTP API endpoints
│
└── .github/workflows/
    └── infra-ci-cd.yml         # GitHub Actions pipeline — deploys everything
```

---

## Architecture Diagram Walkthrough

The diagram shows two separate flows. Here is how each component maps to the code.

---

## FLOW 1: Search Flow (Top of Diagram)

This is what happens when a user searches for something.

```
User → API Gateway → Search Lambda → OpenSearch → Results back to User
                   → Suggestions Lambda → OpenSearch → Suggestions back to User
```

### API Gateway
**File:** `infra/modules/api_gateway/main.tf`

This is the front door of the system. It is an AWS HTTP API (v2) that exposes two public endpoints:

| Route | Method | Purpose |
|---|---|---|
| `/search` | POST | Full document search |
| `/suggestions` | GET | Autocomplete prefix suggestions |

It has CORS enabled so a web browser can call it directly. All requests are logged to CloudWatch. It forwards requests to the correct Lambda function using AWS Proxy integration — meaning the full HTTP request (headers, query params, body) is passed directly to Lambda.

### Search Lambda
**Files:** `src/search/index.py` + `infra/modules/src_search/main.tf`

Receives the HTTP request from API Gateway. Extracts the `query` parameter and runs a `multi_match` search against the OpenSearch `metadata-index`. It searches both the `title` field (boosted 2x) and the `content` field, returns the top 10 ranked results as JSON.

Vector search is also wired in but currently returns empty — it would require generating an embedding for the query first (future enhancement).

Environment variables it uses:
- `OPENSEARCH_ENDPOINT` — the OpenSearch collection URL
- `REGION` — AWS region for signing requests

### Suggestions Lambda
**Files:** `src/suggestions/index.py` + `infra/modules/src_suggestions/main.tf`

Receives the HTTP request from API Gateway. Extracts the `prefix` parameter and runs a `match_phrase_prefix` query against the OpenSearch `suggestions-index`. Results are sorted by `weight` (higher weight = more relevant suggestion) then by relevance score. Returns top 10 suggestions.

---

## FLOW 2: Ingestion Flow (Bottom of Diagram)

This is what happens when a document is uploaded. It is fully automated — no human intervention needed after the upload.

```
Document Upload → S3 Bucket → EventBridge → Step Functions → Processor Lambda
                                                           → Embedding Lambda → OpenSearch
```

### S3 Documents Bucket
**File:** `infra/modules/s3_documents/main.tf`

The entry point for all documents. Key properties:
- Versioning enabled — keeps history of every document version
- All public access blocked — documents are private
- AES-256 server-side encryption — data at rest is encrypted
- EventBridge notifications enabled — every file upload fires an event automatically

When a file lands in this bucket, S3 sends an `Object Created` event to EventBridge. This is the trigger for the entire ingestion pipeline.

### EventBridge Rule (S3 Event Trigger in diagram)
**File:** `infra/modules/step_functions_ingestion/main.tf`

Listens for `Object Created` events from the documents S3 bucket. When it fires, it extracts the `bucket name` and `object key` from the event and passes them as input to the Step Functions state machine. This is the glue between S3 and the pipeline.

IAM role `dev-opensearch-navco-search-eventbridge-role` gives EventBridge permission to start Step Functions executions.

### Step Functions — Ingestion Workflow
**File:** `infra/modules/step_functions_ingestion/main.tf` + `state_machine.json`

Orchestrates the two-step ingestion pipeline. It runs the steps in sequence:

1. Invoke Document Processor Lambda → wait for result
2. Pass result to Embedding Generator Lambda → wait for result

If either step fails, the execution stops and is marked as `Failed` — you can inspect the exact error in the AWS console. This gives you full visibility and retry capability without writing any orchestration code yourself.

### Document Processor Lambda
**Files:** `src/processor/index.py` + `infra/modules/src_processor/main.tf`

First step in the pipeline. Receives the S3 bucket and key from Step Functions. Does two things:
1. Downloads the file from S3 and reads the text content
2. Calls `s3.head_object` to get file metadata (size, upload date, filename)

Returns a structured payload containing the full text content and metadata, which Step Functions passes directly to the Embedding Lambda.

IAM role `dev-opensearch-navco-search-processor-role` gives it read-only access to the S3 bucket — it cannot write or delete.

### Embedding Generator Lambda
**Files:** `src/embedding/index.py` + `infra/modules/src_embedding/main.tf`

Second and final step in the pipeline. This is where the AI happens. It:

1. Calls **Amazon Bedrock** (`amazon.titan-embed-text-v2:0` model) with the document text → gets back a 1024-dimension vector embedding
2. Writes the document metadata to `metadata-index` in OpenSearch
3. Writes the text + embedding vector to `vector-index` in OpenSearch (enables semantic/similarity search)
4. Extracts keywords from the title and content, writes them to `suggestions-index` (powers autocomplete)

Has exponential backoff retry logic for Bedrock throttling (waits 1s, 2s, 4s between retries).

IAM role `dev-opensearch-navco-search-embedding-role` gives it access to OpenSearch, Bedrock, and CloudWatch Logs.

### Amazon Bedrock (in diagram)
Not a Terraform resource — it is a managed AWS service called via API. The embedding Lambda calls `bedrock-runtime` with the Titan Embed model ID. Bedrock converts text into a numerical vector that captures semantic meaning. Two documents about similar topics will have vectors that are mathematically close to each other, enabling similarity search.

---

## OpenSearch Serverless Collection
**File:** `infra/modules/opensearch_collection/main.tf`

The core search engine. It is serverless — no servers to manage, scales automatically. Type is `VECTORSEARCH` which supports both keyword and vector (k-NN) search.

Three indexes live inside it:

| Index | Purpose | Written by | Read by |
|---|---|---|---|
| `metadata-index` | Document title, content, size, upload date | Embedding Lambda | Search Lambda |
| `vector-index` | AI embeddings for semantic similarity search | Embedding Lambda | Search Lambda (future) |
| `suggestions-index` | Keywords and weights for autocomplete | Embedding Lambda | Suggestions Lambda |

Three security policies are attached:
- **Encryption policy** — data encrypted with AWS-managed KMS key
- **Network policy** — allows public HTTPS access (required for Lambda to connect)
- **Data access policy** — lists all 5 Lambda role ARNs that are allowed to read/write indexes

### Index Bootstrap Lambda
**Files:** `src/bootstrap/index.py` + `infra/modules/src_bootstrap/main.tf`

This runs once after every deployment (invoked by the CI/CD pipeline). It creates the three indexes with their correct field mappings if they don't already exist. If they exist, it skips them safely.

The vector index mapping is important — it defines the `embedding` field as `knn_vector` with 1536 dimensions and HNSW algorithm, which is what enables fast approximate nearest-neighbor search.

---

## IAM — Security and Permissions
**File:** `infra/modules/iam/main.tf`

Every Lambda function and service has its own IAM role with only the permissions it needs (least privilege). No role has admin access.

| Role | Can Do |
|---|---|
| `index-bootstrap-role` | Write to OpenSearch, write CloudWatch logs |
| `search-role` | Read from OpenSearch, write CloudWatch logs |
| `suggestions-role` | Read from OpenSearch, write CloudWatch logs |
| `processor-role` | Read from S3 bucket, write CloudWatch logs |
| `embedding-role` | Write to OpenSearch, call Bedrock, write CloudWatch logs |
| `step-functions-role` | Invoke any Lambda function, write CloudWatch logs |
| `eventbridge-role` | Start Step Functions executions |

---

## Lambda Layer — Shared Dependencies
**File:** `infra/main.tf` (layer resource) + `infra/lambda_layers/opensearch/python/requirements.txt`

All Lambda functions that talk to OpenSearch share a single Lambda Layer containing:
- `opensearch-py==2.3.1` — Python client for OpenSearch
- `requests-aws4auth==1.2.3` — Signs HTTP requests with AWS credentials (required for OpenSearch Serverless)

This avoids bundling these libraries into every function zip separately. The layer is built during CI/CD by running `pip install` into the correct directory structure (`python/lib/python3.13/site-packages/`) before Terraform zips and uploads it.

---

## CI/CD Pipeline
**File:** `.github/workflows/infra-ci-cd.yml`

Triggered manually from GitHub Actions. Deploys the entire platform in one run.

### Pipeline Steps in Order

| Step | What it does |
|---|---|
| Checkout code | Pulls the specified branch |
| Configure AWS credentials | Authenticates to AWS using GitHub Secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) |
| Setup Terraform | Installs Terraform 1.5.0, wrapper disabled to avoid output format issues |
| Build Lambda Layer | Runs `pip install` to download `opensearch-py` and `requests-aws4auth` into the layer directory |
| Create Terraform State Bucket | Creates the S3 bucket that stores Terraform state (idempotent — skips if exists) |
| Terraform Init | Initialises providers and connects to the S3 remote state backend |
| Terraform Validate | Checks all `.tf` files for syntax and configuration errors |
| Terraform Plan | Calculates what will be created/changed/destroyed |
| Terraform Apply | Creates all AWS resources |
| Get Outputs | Reads the Lambda function name and OpenSearch endpoint from Terraform outputs using `jq` |
| Invoke Index Bootstrap Lambda | Calls the bootstrap Lambda via AWS CLI to create the OpenSearch indexes |
| Wait 10 seconds | Gives OpenSearch time to finish index creation |
| Terraform Plan (2nd) | Plans any remaining dependent resources |
| Terraform Apply (2nd) | Applies remaining resources |
| Get Final Outputs | Reads API endpoint URLs and state machine ARN |
| Deployment Summary | Writes a summary to the GitHub Actions job summary page with all endpoint URLs |
| Cleanup | Removes local plan files |

### Why Two Terraform Apply Steps?

The bootstrap Lambda must run and create the OpenSearch indexes before the rest of the infrastructure is fully usable. The two-phase apply ensures the indexes exist before any dependent resources try to use them.

### State Management

Terraform state is stored in S3 (`dev-opensearch-navco-search-tfstate`). This means:
- Re-running the pipeline does not re-create existing resources — Terraform compares current state to desired state and only makes changes
- Multiple team members can run the pipeline safely without conflicts
- State is versioned so you can roll back if needed

---

## Environment Configuration
**File:** `infra/terraform.tfvars`

```
env              = "dev"
project_name     = "opensearch-navco-search"
region           = "us-east-1"
bedrock_model_id = "amazon.titan-embed-text-v2:0"
```

All resource names follow the pattern `{env}-{project_name}-{resource}`, e.g. `dev-opensearch-navco-search-search`. Changing `env` to `stg` or `prod` creates a completely separate set of resources with no overlap.

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| OpenSearch Serverless instead of provisioned | No cluster management, auto-scales, pay per use |
| Step Functions for ingestion | Visual debugging, automatic retry, clear failure states |
| Separate IAM role per Lambda | Security — a compromised function can only access what it needs |
| Lambda Layer for opensearch-py | Single source of truth for the library version across all functions |
| S3 remote state for Terraform | Safe for CI/CD — prevents state conflicts between runs |
| EventBridge for S3 trigger | Decoupled — S3 doesn't need to know about Step Functions directly |

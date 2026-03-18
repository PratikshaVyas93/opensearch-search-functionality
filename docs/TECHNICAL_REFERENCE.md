# Technical Reference — opensearch-navco-search

This document covers every Terraform module, Lambda function, and CI/CD pipeline step in the project.
It explains what each piece does, why it exists, and how it connects to the overall architecture.

---

## Architecture Overview

```
User / Client App
      │
      ▼
API Gateway (HTTP API)
      │
      ├──── POST /search      ──► Search Lambda      ──► OpenSearch metadata-index
      │                                               ──► OpenSearch vector-index (semantic)
      │
      └──── GET  /suggestions ──► Suggestions Lambda ──► OpenSearch suggestions-index

S3 Bucket (JSON upload)
      │
      ▼
EventBridge (S3 ObjectCreated event)
      │
      ▼
Step Functions State Machine
      │
      ▼
Indexer Lambda
      ├──► metadata-index   (all JSON fields stored dynamically)
      └──► suggestions-index (phrases + tokens extracted from string fields)

Bedrock Knowledge Base (runs independently, managed by AWS)
      ├── reads S3 bucket
      ├── chunks documents
      ├── calls Titan Embed (1536-dim vectors)
      └──► vector-index in OpenSearch (semantic search)
```

---

## Project Structure

```
infra/
  main.tf                          Root module — wires all modules together
  variables.tf                     Input variables (env, project_name, region, bedrock_model_id)
  terraform.tfvars                 Default values for dev environment
  outputs.tf                       Exposes endpoints, Lambda names, KB ID
  lambda_layers/opensearch/        Python packages (opensearch-py, requests-aws4auth)
  modules/
    s3_documents/                  S3 bucket for JSON uploads
    opensearch_collection/         OpenSearch Serverless collection + policies
    iam/                           All IAM roles and policies
    src_bootstrap/                 Bootstrap Lambda (creates indexes)
    src_search/                    Search Lambda
    src_suggestions/               Suggestions Lambda
    src_indexer/                   Indexer Lambda (metadata + suggestions)
    bedrock_knowledge_base/        Bedrock KB + IAM role + S3 data source
    step_functions_ingestion/      State machine + EventBridge rule
    api_gateway/                   HTTP API Gateway

src/
  bootstrap/index.py               Bootstrap Lambda source
  search/index.py                  Search Lambda source
  suggestions/index.py             Suggestions Lambda source
  indexer/index.py                 Indexer Lambda source

.github/workflows/
  infra-ci-cd.yml                  GitHub Actions deploy/destroy pipeline
```

---

## Terraform Modules

### `infra/main.tf` — Root Module

The root module is the orchestrator. It calls every child module in the correct dependency order and passes outputs from one module as inputs to the next.

Key responsibilities:
- Declares the AWS provider with version `~> 5.31` — this minimum version is required because `aws_bedrockagent_knowledge_base` was only added in provider 5.31. Earlier versions do not have this resource type and will fail validation.
- Configures the S3 remote backend so Terraform state is stored in `dev-opensearch-navco-search-tfstate` and shared across all pipeline runs.
- Builds the Lambda layer zip from `infra/lambda_layers/opensearch/` and publishes it as `aws_lambda_layer_version.opensearch`. All Lambda functions reference this layer so they can import `opensearch-py` and `requests-aws4auth`.
- Passes the OpenSearch collection endpoint and ARN into every Lambda module so they know where to connect.
- Passes IAM role ARNs from the `iam` module into each Lambda module.

Deployment phases (enforced by `depends_on`):
1. S3 + OpenSearch collection (foundation)
2. IAM roles (depend on collection ARN and bucket ARN)
3. Lambda functions (depend on IAM roles)
4. Step Functions + EventBridge (depend on indexer Lambda)
5. Bedrock Knowledge Base (depend on bootstrap Lambda having run — enforced in CI/CD, not Terraform)
6. API Gateway (depends on search + suggestions Lambdas)

---

### `infra/variables.tf` + `infra/terraform.tfvars`

| Variable | Default | Purpose |
|---|---|---|
| `env` | `dev` | Prefixes all resource names. Validated to `dev`, `stg`, `prod` only. |
| `project_name` | `opensearch-navco-search` | Second part of every resource name, e.g. `dev-opensearch-navco-search-search` |
| `region` | `us-east-1` | AWS region for all resources |
| `bedrock_model_id` | `amazon.titan-embed-text-v2:0` | Embedding model used by Bedrock KB |

All resource names follow the pattern `{env}-{project_name}-{resource-type}` to make them easy to identify in the AWS console and to avoid name collisions across environments.

---

### `infra/modules/s3_documents/`

**What it creates:** An S3 bucket named `dev-opensearch-navco-search-documents-bucket`.

**Why it exists:** This is the entry point for all data. Users upload JSON files here. The bucket is the trigger for the entire ingestion pipeline.

Key settings:
- Versioning enabled — keeps history of every uploaded file so you can recover previous versions.
- All public access blocked — documents are private; only IAM roles can read them.
- AES-256 server-side encryption — data at rest is encrypted automatically.
- EventBridge notifications enabled — when any object is created, S3 sends an event to EventBridge. This is what triggers the Step Functions state machine automatically on upload.

---

### `infra/modules/opensearch_collection/`

**What it creates:** An OpenSearch Serverless collection of type `VECTORSEARCH`, plus three required policies.

**Why OpenSearch Serverless instead of a managed cluster?**
Serverless means you pay per request, not per hour. There are no nodes to size, patch, or scale. For a search platform with variable load this is significantly cheaper and simpler to operate.

**Why type `VECTORSEARCH`?**
This collection type enables the `knn_vector` field type and the HNSW approximate nearest-neighbour algorithm. Without this type, you cannot store or query vector embeddings — the Bedrock Knowledge Base would have nowhere to write its vectors.

Three policies are required by OpenSearch Serverless (AWS enforces all three before a collection can be created):

| Policy | Type | Purpose |
|---|---|---|
| `*-enc` | encryption | Specifies KMS key. We use `AWSOwnedKey = true` (AWS manages the key, no cost). |
| `*-net` | network | Controls whether the collection is reachable from the public internet or only via VPC. We use `AllowFromPublic = true` so Lambda functions can reach it without a VPC. |
| `*-data` | data access | Lists which IAM role ARNs can read/write indexes. All Lambda roles and the Bedrock KB role are listed here. |

The collection is named `dev-navco-search` (shorter than the full project name to stay within AWS name length limits).

---

### `infra/modules/iam/`

**What it creates:** Five IAM roles, each with a least-privilege inline policy.

| Role | Used by | Permissions |
|---|---|---|
| `*-index-bootstrap-role` | Bootstrap Lambda | `aoss:APIAccessAll` on the collection + CloudWatch Logs |
| `*-search-role` | Search Lambda | `aoss:APIAccessAll` on the collection + CloudWatch Logs |
| `*-suggestions-role` | Suggestions Lambda | `aoss:APIAccessAll` on the collection + CloudWatch Logs |
| `*-indexer-role` | Indexer Lambda | `s3:GetObject` on the documents bucket + `aoss:APIAccessAll` + CloudWatch Logs |
| `*-step-functions-role` | Step Functions | `lambda:InvokeFunction` (any) + CloudWatch Logs |

**Why separate roles per Lambda?** Least privilege — if one Lambda is compromised, the attacker only has the permissions of that one role. The indexer role is the only one that can read S3; the search role cannot.

**Why is `aoss:APIAccessAll` used instead of granular actions?** OpenSearch Serverless does not support individual action-level permissions like `aoss:CreateIndex`. The only supported action for data plane operations is `aoss:APIAccessAll`. Fine-grained access control is handled by the data access policy in the collection module.

---

### `infra/modules/src_bootstrap/` + `src/bootstrap/index.py`

**What it creates:** A Lambda function named `dev-opensearch-navco-search-index-bootstrap`.

**Why it exists:** OpenSearch Serverless does not auto-create indexes. Before any data can be written or the Bedrock Knowledge Base can connect, the three indexes must exist with the correct mappings. This Lambda creates them on first deploy and is idempotent (checks if each index exists before creating).

**Indexes it creates:**

`metadata-index` — stores all fields from uploaded JSON documents. Fields: `document_id`, `title`, `size`, `upload_date`, `content`, `source`. In practice the indexer writes any fields dynamically, so this mapping is a baseline.

`vector-index` — stores text chunks and their vector embeddings written by Bedrock Knowledge Base. The critical field is `embedding` with type `knn_vector`, dimension 1536, using the HNSW algorithm with cosine similarity. This index must exist before the Bedrock KB is created — that is why the CI/CD pipeline invokes this Lambda before Phase 2 of the Terraform apply.

`suggestions-index` — stores autocomplete suggestion strings with a `weight` field for ranking. Written by the Indexer Lambda, read by the Suggestions Lambda.

**Why this Lambda runs in CI/CD, not as a Terraform resource:** Terraform manages infrastructure (buckets, roles, functions). It does not manage data-plane operations like creating OpenSearch indexes. A Lambda invoked from the pipeline is the correct pattern for one-time setup operations that depend on infrastructure being ready.

---

### `infra/modules/src_search/` + `src/search/index.py`

**What it creates:** A Lambda function named `dev-opensearch-navco-search-search`.

**What it does:** Receives a `POST /search` request from API Gateway with a `query` parameter. Runs a `multi_match` query against `metadata-index` across the `title` (boosted 2x) and `content` fields. Returns up to 10 results with score, ID, and source fields.

The vector search path exists in the code but currently returns empty — it would require calling Bedrock to embed the query string first. The metadata search handles keyword-based queries. Bedrock KB handles semantic queries through its own retrieval API (separate from this Lambda).

**Timeout:** 30 seconds. OpenSearch queries are fast (< 1s) but the timeout provides headroom for cold starts.

---

### `infra/modules/src_suggestions/` + `src/suggestions/index.py`

**What it creates:** A Lambda function named `dev-opensearch-navco-search-suggestions`.

**What it does:** Receives a `GET /suggestions?prefix=te` request. Runs a `match_phrase_prefix` query against `suggestions-index`, sorted by `weight` descending then score descending. Returns up to 10 suggestions.

`match_phrase_prefix` is the standard OpenSearch approach for autocomplete — it matches documents where the `suggestion` field starts with the given prefix, without requiring an exact token match.

**Why weight-based sorting?** Full phrases (e.g. "Technical Specification") are given higher weight than individual tokens (e.g. "technical") by the indexer. This means more complete, meaningful suggestions appear first.

---

### `infra/modules/src_indexer/` + `src/indexer/index.py`

**What it creates:** A Lambda function named `dev-opensearch-navco-search-indexer`.

**What it does:** Triggered by Step Functions when a JSON file is uploaded to S3. Reads the file, dynamically indexes all fields into `metadata-index`, and extracts suggestions into `suggestions-index`.

**Why dynamic / schema-free?** The JSON files uploaded can have any shape — different uploads may have completely different field names. Rather than requiring a fixed schema, the indexer stores whatever fields are present. This means a file with `{title, author, category}` and a file with `{product_name, sku, description}` are both handled correctly without any code changes.

**How suggestions are extracted:**
1. All string and list-of-string fields are walked recursively (max depth 3).
2. Fields like `id`, `url`, `hash` are skipped — they are not useful for autocomplete.
3. Full phrases (entire field values) are stored as suggestions with a weight boost of +5.
4. Multi-word values are also tokenized into individual words (min 3 chars) stored as lower-weight suggestions.
5. Maximum 50 suggestions per document to prevent index bloat.

**Document ID derivation:** Looks for `document_id`, `id`, `doc_id`, or `documentId` fields in the JSON. Falls back to the S3 key (without extension) if none are found.

---

### `infra/modules/bedrock_knowledge_base/`

**What it creates:** A Bedrock Knowledge Base, an IAM role for Bedrock, and an S3 data source pointing at the documents bucket.

**Why Bedrock Knowledge Base instead of a custom embedding Lambda?**
Building a custom embedding pipeline requires: calling Bedrock Titan Embed for each text chunk, managing chunking logic, handling retries, writing vectors to OpenSearch, and keeping it all in sync with S3. Bedrock Knowledge Base does all of this as a managed service. You configure it once and it handles the entire pipeline automatically whenever you trigger a sync.

**Why `amazon.titan-embed-text-v2:0`?**
This is Amazon's second-generation embedding model. It produces 1024-dimensional vectors with improved accuracy over v1. Reasons for choosing it:
- Native to AWS — no cross-region calls, lower latency, no data leaving AWS.
- 1536 dimensions is the standard size for this model class (same as OpenAI Ada-002). It provides a good balance between semantic richness and storage/compute cost.
- Supported natively by Bedrock Knowledge Base — no custom integration needed.
- No per-token pricing complexity — straightforward cost model.

**Why 1536 dimensions specifically?**
The `embedding` field in `vector-index` is defined with `dimension: 1536` to match exactly what Titan Embed outputs. If the dimension in the index does not match the model output, OpenSearch will reject every write. 1024 is not arbitrary — it is the fixed output size of the `amazon.titan-embed-text-v2:0` model. If you switch to a different model (e.g. Titan Embed v1 = 1536 dims, Cohere = 1024 dims), you must recreate the vector index with the matching dimension.

**HNSW algorithm settings:**
- `ef_construction: 256` — controls index build quality. Higher = better recall, slower indexing. 256 is a good production default.
- `m: 16` — number of connections per node in the graph. Higher = better recall, more memory. 16 is standard.
- `space_type: cosinesimil` — cosine similarity measures the angle between vectors, not their magnitude. This is correct for text embeddings where direction (meaning) matters more than length.

**IAM role for Bedrock KB:** Bedrock needs its own role to read from S3, write to OpenSearch, and call the Titan Embed model. This role is separate from the Lambda roles.

---

### `infra/modules/step_functions_ingestion/`

**What it creates:** A Step Functions state machine and an EventBridge rule + target.

**Why Step Functions instead of invoking Lambda directly from EventBridge?**
Step Functions gives you a visual execution history in the AWS console, built-in error handling with `Catch`, and the ability to add more steps later (e.g. a validation step, a notification step) without changing the EventBridge rule. It also retries failed Lambda invocations automatically.

**State machine flow:**
```
S3 ObjectCreated event
        │
        ▼
IndexMetadataAndSuggestions  (calls Indexer Lambda)
        │
   ┌────┴────┐
success    failure
   │           │
Succeed     Fail (logged to CloudWatch)
```

The state machine receives the S3 event detail (bucket name + object key) and passes it directly to the Indexer Lambda as the input payload.

**EventBridge rule:** Listens for `aws.s3` events of type `Object Created` on the documents bucket. The `input_transformer` reshapes the raw S3 event into the format the Indexer Lambda expects (`detail.bucket.name` and `detail.object.key`).

**Why EventBridge instead of S3 Lambda trigger?** EventBridge gives you a decoupled event bus. You can add more targets later (e.g. send a notification, trigger another workflow) without modifying the S3 bucket configuration. S3 Lambda triggers are limited to 1 trigger per event type per bucket.

---

### `infra/modules/api_gateway/`

**What it creates:** An HTTP API Gateway with two routes, a CloudWatch log group, and Lambda permissions.

**Why HTTP API (APIGatewayV2) instead of REST API (APIGatewayV1)?**
HTTP API is the newer, simpler, and cheaper option. It has lower latency, costs ~70% less per million requests, and natively supports Lambda proxy integration with payload format version 2.0. REST API adds features like request validation, usage plans, and API keys — none of which are needed here.

**Routes:**

| Route | Lambda | Purpose |
|---|---|---|
| `POST /search` | Search Lambda | Full-text search with a query body |
| `GET /suggestions` | Suggestions Lambda | Autocomplete with `?prefix=` query param |

**CORS:** Configured with `allow_origins = ["*"]` so any frontend can call the API. In production you would restrict this to your specific domain.

**CloudWatch log group:** Named `/aws/apigateway/dev-opensearch-navco-search-api`. Stores access logs for every request (IP, method, path, status, response size). Retention is 7 days to control cost. The `lifecycle { ignore_changes = all }` block prevents Terraform from failing if the log group already exists from a previous deploy.

**Lambda permissions:** Each Lambda has an `aws_lambda_permission` resource granting API Gateway permission to invoke it. Without this, API Gateway calls would be rejected with a 403 even if the IAM role is correct — Lambda resource-based policies and IAM policies are both required.

---

### `infra/outputs.tf`

Exposes the values you need after deployment:

| Output | Value |
|---|---|
| `api_endpoint` | Base URL of the HTTP API |
| `search_endpoint` | Full URL for `POST /search` |
| `suggestions_endpoint` | Full URL for `GET /suggestions` |
| `opensearch_endpoint` | OpenSearch collection endpoint (for debugging) |
| `knowledge_base_id` | Bedrock KB ID (needed to trigger manual syncs) |
| `index_bootstrap_lambda_name` | Used by CI/CD to invoke the bootstrap Lambda |
| `state_machine_arn` | Step Functions ARN |

---

## Lambda Layer

**Location:** `infra/lambda_layers/opensearch/python/`

**What it contains:** Python packages installed at CI/CD time:
- `opensearch-py` — the official OpenSearch Python client
- `requests-aws4auth` — signs HTTP requests with AWS SigV4 (required for OpenSearch Serverless authentication)

**Why a layer instead of bundling in each Lambda zip?**
All four Lambdas need the same packages. A layer means the packages are uploaded once and shared. It also keeps each Lambda zip small (just the `index.py` file), which speeds up deploys and cold starts.

**Layer structure:** Must follow `python/lib/python3.13/site-packages/` exactly. AWS Lambda unzips the layer into `/opt/` and Python's import system looks in `/opt/python/lib/python3.13/site-packages/`. Any other structure and the import fails with `No module named 'opensearchpy'`.

---

## CI/CD Pipeline — `.github/workflows/infra-ci-cd.yml`

The pipeline runs on `workflow_dispatch` (manual trigger only). You choose environment (`dev`/`stg`/`prod`), action (`deploy`/`destroy`), and branch before running.

### Trigger inputs

| Input | Options | Purpose |
|---|---|---|
| `environment` | dev, stg, prod | Sets the `env` Terraform variable, which prefixes all resource names |
| `action` | deploy, destroy | Selects which path to run |
| `branch` | `15032026_aws_kiro_opensearch` | Which git branch to deploy from |

---

### Deploy path — step by step

**1. Checkout + AWS credentials**
Checks out the selected branch. Configures AWS credentials from GitHub Secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`). These are stored as environment-scoped secrets so `dev` credentials cannot be used to deploy to `prod`.

**2. Setup Terraform**
Installs Terraform 1.5.0 with `terraform_wrapper: false`. The wrapper is disabled because it adds extra output formatting that breaks `terraform output -json | jq` parsing.

**3. Create Terraform State Bucket**
Creates the S3 state bucket if it does not exist, then enables versioning. The `2>/dev/null || echo "Bucket already exists"` pattern makes this step idempotent — it does not fail on re-runs.

**4. Terraform Init**
Downloads the AWS provider (~5.31) and configures the S3 backend. Must run before any other Terraform command.

**5. Build Lambda Layer**
Installs Python packages from `requirements.txt` into the correct layer directory structure (`python/lib/python3.13/site-packages/`). This runs before Terraform so the packages are present when Terraform zips the layer. If `requirements.txt` is missing, the step fails immediately with a clear error message.

**6. Terraform Format + Validate**
`fmt -recursive` reformats all `.tf` files to canonical style. `validate` checks for syntax errors and invalid references without making any AWS API calls. Both run before plan to catch issues early.

**7. Terraform Plan**
Generates an execution plan showing exactly what will be created, modified, or destroyed. The plan is saved to `tfplan` for use in the apply step.

**8. Phase 1 Apply — all resources except Bedrock Knowledge Base**
Applies all modules using `-target` flags:
- `module.s3_documents` — S3 bucket
- `module.opensearch_collection` — OpenSearch collection + policies
- `module.iam` — all IAM roles
- `aws_lambda_layer_version.opensearch` — the shared layer
- `module.src_bootstrap`, `module.src_search`, `module.src_suggestions`, `module.src_indexer` — all Lambdas
- `aws_iam_role.eventbridge_role` + policy — EventBridge role
- `module.step_functions_ingestion` — state machine + EventBridge rule
- `module.api_gateway` — HTTP API

The Bedrock Knowledge Base is intentionally excluded here.

**Why split into two phases?**
Bedrock Knowledge Base requires `vector-index` to already exist in OpenSearch before it can be created. The index is created by the Bootstrap Lambda. If we apply everything in one `terraform apply`, Terraform creates the KB at the same time as the Lambda — before the Lambda has been invoked. The KB creation fails with `no such index [vector-index]`. The two-phase approach guarantees the correct order.

**9. Get Bootstrap Lambda Name**
Reads the Lambda function name from Terraform output using `terraform output -json | jq -r '.'`. The `-json` flag returns a JSON-encoded string; `jq -r '.'` strips the surrounding quotes. This is stored as a GitHub Actions step output for use in the next step.

**10. Invoke Index Bootstrap Lambda**
Calls the bootstrap Lambda via AWS CLI. The response is saved to `/tmp/bootstrap_response.json` and printed. If the response contains `"errorType"` (Lambda runtime error), the pipeline exits with code 1 — preventing Phase 2 from running with broken indexes.

**11. Wait 20 seconds**
OpenSearch Serverless is eventually consistent. After creating indexes, there is a brief propagation delay before they are queryable. 20 seconds is sufficient for the indexes to be visible to the Bedrock KB validation check.

**12. Phase 2 Apply — Bedrock Knowledge Base**
Applies only `module.bedrock_knowledge_base`. At this point `vector-index` exists and is stable, so the KB creation succeeds.

**13. Get Final Outputs + Deployment Summary**
Reads all API endpoints and the KB ID from Terraform outputs. Writes a formatted summary to the GitHub Actions job summary page, including curl commands to test the endpoints.

---

### Destroy path — step by step

**1. Terraform Destroy**
Runs `terraform destroy -auto-approve` with `continue-on-error: true`. The `continue-on-error` is needed because some resources (like a non-empty S3 bucket) will fail to destroy — the next step handles that.

**2. Empty S3 Documents Bucket**
Runs `aws s3 rm s3://... --recursive` to delete all objects. S3 buckets cannot be destroyed by Terraform while they contain objects. This step runs after destroy (which fails on the bucket) to empty it, allowing a re-run to clean up the bucket.

**3. Destroy Summary**
Writes a confirmation to the job summary. Notes that the Terraform state bucket is intentionally kept (destroying it would lose the state file, making future deploys unable to track existing resources).

---

## How the pieces connect end-to-end

**On first deploy:**
1. CI/CD creates all infrastructure (Phase 1)
2. Bootstrap Lambda creates the three OpenSearch indexes
3. CI/CD creates the Bedrock Knowledge Base (Phase 2) — it finds `vector-index` ready

**When a user uploads a JSON file to S3:**
1. S3 sends an `Object Created` event to EventBridge
2. EventBridge triggers the Step Functions state machine
3. State machine invokes the Indexer Lambda with bucket + key
4. Indexer Lambda reads the JSON, writes all fields to `metadata-index`, extracts suggestions to `suggestions-index`
5. Separately (on a schedule or manual trigger), Bedrock KB syncs the S3 bucket — chunks the JSON, generates 1536-dim embeddings via Titan Embed, writes vectors to `vector-index`

**When a user searches:**
- `POST /search?query=...` → API Gateway → Search Lambda → `metadata-index` (keyword match)
- Semantic search via Bedrock KB retrieval API (called separately, not through this API Gateway)

**When a user types in a search box:**
- `GET /suggestions?prefix=te` → API Gateway → Suggestions Lambda → `suggestions-index` → returns matching phrases and tokens

---

## Key design decisions summary

| Decision | Reason |
|---|---|
| OpenSearch Serverless over managed cluster | No nodes to manage, pay-per-request, scales to zero |
| Bedrock Knowledge Base over custom embedding Lambda | Managed chunking + embedding pipeline, no code to maintain |
| Titan Embed v1 (1536 dims) | Native AWS model, matches `vector-index` dimension, no cross-service calls |
| Dynamic JSON indexing (no fixed schema) | JSON files can have any shape; indexer handles all fields automatically |
| Two-phase Terraform apply | Ensures `vector-index` exists before Bedrock KB is created |
| Lambda layer for Python packages | Shared across all Lambdas, keeps zips small, single place to update dependencies |
| HTTP API Gateway over REST API | Simpler, cheaper (~70% less), lower latency, sufficient for these two routes |
| Separate IAM role per Lambda | Least privilege — each function only has the permissions it needs |
| EventBridge + Step Functions over direct S3 trigger | Decoupled, observable, extensible without changing S3 config |

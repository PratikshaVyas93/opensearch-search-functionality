# AWS Console Verification Guide
## Project: opensearch-navco-search (dev environment)
## Region: us-east-1

This guide walks you through verifying every AWS resource created by the CI/CD pipeline, in the order they were deployed. For each resource, it explains what it does and what a healthy state looks like.

---

## 1. S3 — Terraform State Bucket

**What it does:** Stores the Terraform state file so the pipeline can track what's already deployed and avoid re-creating existing resources.

**How to check:**
1. Go to **S3** in the AWS Console
2. Search for `dev-opensearch-navco-search-tfstate`
3. Click the bucket → go to **Properties** tab
4. Confirm **Versioning** is set to `Enabled`
5. Click into the bucket → you should see a folder `infra/` containing `terraform.tfstate`

**Healthy state:** Bucket exists, versioning enabled, `terraform.tfstate` file present inside `infra/` prefix.

---

## 2. S3 — Documents Bucket

**What it does:** Stores the raw documents (PDFs, text files, etc.) that users upload. An S3 event triggers the ingestion pipeline when a new file is uploaded.

**How to check:**
1. Go to **S3** in the AWS Console
2. Search for `dev-opensearch-navco-search-documents-bucket`
3. Click the bucket → go to **Properties** tab
4. Scroll down to **Event notifications** — you should see a rule pointing to EventBridge or Step Functions

**Healthy state:** Bucket exists with correct name and tags (`Environment: dev`, `Project: opensearch-navco-search`).

---

## 3. Amazon OpenSearch Serverless — Collection

**What it does:** The vector/keyword search engine. Stores indexed document embeddings and handles search queries. This is the core of the search platform.

**How to check:**
1. Go to **Amazon OpenSearch Service** in the AWS Console
2. In the left sidebar click **Serverless** → **Collections**
3. Look for `dev-navco-search`
4. Click it — check the **Status** is `Active`
5. Note the **Collection endpoint** URL (used by Lambda functions)
6. Click **Security** tab → verify **Encryption policy** and **Network policy** exist
7. Click **Data access policies** → verify the policy lists all 5 Lambda role ARNs

**Healthy state:** Status is `Active`, endpoint URL is visible, security policies are attached.

---

## 4. IAM — Lambda Execution Roles

**What it does:** Each Lambda function has its own IAM role with least-privilege permissions. These roles allow the functions to access OpenSearch, S3, Bedrock, and CloudWatch Logs.

**How to check:**
1. Go to **IAM** in the AWS Console
2. Click **Roles** in the left sidebar
3. Search for `dev-opensearch-navco-search` — you should see these roles:

| Role Name | Purpose |
|---|---|
| `dev-opensearch-navco-search-index-bootstrap-role` | Allows bootstrap Lambda to create OpenSearch indexes |
| `dev-opensearch-navco-search-search-role` | Allows search Lambda to query OpenSearch |
| `dev-opensearch-navco-search-suggestions-role` | Allows suggestions Lambda to query OpenSearch |
| `dev-opensearch-navco-search-processor-role` | Allows processor Lambda to read from S3 |
| `dev-opensearch-navco-search-embedding-role` | Allows embedding Lambda to call Bedrock + write to OpenSearch |
| `dev-opensearch-navco-search-step-functions-role` | Allows Step Functions to invoke Lambda functions |
| `dev-opensearch-navco-search-eventbridge-role` | Allows EventBridge to start Step Functions executions |

4. Click any role → go to **Permissions** tab → verify inline policies are attached
5. Go to **Trust relationships** tab → verify the correct AWS service is listed as principal (e.g., `lambda.amazonaws.com`)

**Healthy state:** All 7 roles exist, each has at least one inline policy, trust relationship points to the correct service.

---

## 5. Lambda — OpenSearch Layer

**What it does:** A shared Lambda layer containing the `opensearch-py` Python library. All Lambda functions that talk to OpenSearch use this layer instead of bundling the dependency individually.

**How to check:**
1. Go to **Lambda** in the AWS Console
2. In the left sidebar click **Layers**
3. Search for `dev-opensearch-navco-search-opensearch-layer`
4. Click it → verify **Compatible runtimes** shows `python3.13`
5. Check that at least version 1 exists

**Healthy state:** Layer exists, compatible with `python3.13`, has at least one version.

---

## 6. Lambda — Index Bootstrap Function

**What it does:** Runs once after deployment to create the OpenSearch indexes (mappings and settings). Without this, the search and embedding functions have nowhere to write data.

**How to check:**
1. Go to **Lambda** in the AWS Console
2. Search for `dev-opensearch-navco-search-index-bootstrap`
3. Click the function → verify:
   - **Runtime:** `python3.13`
   - **Handler:** `index.handler`
   - **Layers:** shows the opensearch layer attached
4. Click **Configuration** → **Environment variables** → verify `OPENSEARCH_ENDPOINT` is set
5. Click **Monitor** → **View CloudWatch logs** → check the most recent log stream for a successful run (look for `Index created` or similar message)

**Healthy state:** Function exists, environment variables set, CloudWatch logs show a successful execution after deployment.

---

## 7. Lambda — Search Function

**What it does:** Handles search API requests. Receives a query string, runs a keyword/vector search against OpenSearch, and returns ranked results.

**How to check:**
1. Go to **Lambda** → search for `dev-opensearch-navco-search-search`
2. Verify:
   - **Runtime:** `python3.13`
   - **Handler:** `index.handler`
   - **Layers:** opensearch layer attached
3. Click **Configuration** → **Environment variables** → verify `OPENSEARCH_ENDPOINT` is set
4. Click **Configuration** → **Triggers** → verify API Gateway trigger is listed
5. To test: click **Test** tab → create a test event with `{"queryStringParameters": {"query": "test"}}` → click **Test**

**Healthy state:** Function exists, API Gateway trigger attached, test returns a JSON response (even if empty results).

---

## 8. Lambda — Suggestions Function

**What it does:** Handles autocomplete/suggestions API requests. Returns prefix-matched suggestions as the user types in a search box.

**How to check:**
1. Go to **Lambda** → search for `dev-opensearch-navco-search-suggestions`
2. Verify same configuration as Search function above
3. Click **Configuration** → **Triggers** → verify API Gateway trigger is listed
4. To test: click **Test** tab → create a test event with `{"queryStringParameters": {"prefix": "te"}}` → click **Test**

**Healthy state:** Function exists, API Gateway trigger attached, test returns a JSON response.

---

## 9. Lambda — Document Processor Function

**What it does:** First step in the ingestion pipeline. Reads a raw document from S3, extracts and cleans the text content, then passes it to the embedding function.

**How to check:**
1. Go to **Lambda** → search for `dev-opensearch-navco-search-processor`
2. Verify:
   - **Runtime:** `python3.13`
   - **Handler:** `index.handler`
3. Click **Configuration** → **Triggers** → this function is triggered by Step Functions (no direct trigger shown here)
4. Click **Monitor** → **View CloudWatch logs** → check for any execution logs

**Healthy state:** Function exists with correct runtime and handler.

---

## 10. Lambda — Embedding Generator Function

**What it does:** Second step in the ingestion pipeline. Takes the cleaned text from the processor, calls Amazon Bedrock to generate a vector embedding, then writes the document + embedding to OpenSearch.

**How to check:**
1. Go to **Lambda** → search for `dev-opensearch-navco-search-embedding`
2. Verify:
   - **Runtime:** `python3.13`
   - **Handler:** `index.handler`
   - **Layers:** opensearch layer attached
3. Click **Configuration** → **Environment variables** → verify `OPENSEARCH_ENDPOINT` and `BEDROCK_MODEL_ID` are set
4. Click **Monitor** → **View CloudWatch logs** → check for execution logs

**Healthy state:** Function exists, both environment variables set, opensearch layer attached.

---

## 11. Step Functions — Ingestion State Machine

**What it does:** Orchestrates the document ingestion pipeline. When a file is uploaded to S3, EventBridge triggers this state machine which runs: Processor Lambda → Embedding Lambda in sequence. If either step fails, the execution is marked as failed and you can inspect the error.

**How to check:**
1. Go to **Step Functions** in the AWS Console
2. Click **State machines** in the left sidebar
3. Search for `dev-opensearch-navco-search-ingestion`
4. Click it → you'll see the visual workflow diagram showing the two Lambda steps
5. Click **Executions** tab → if any documents have been uploaded, you'll see execution history here
6. Click any execution → see the step-by-step flow with inputs/outputs at each stage

**Healthy state:** State machine exists, visual diagram shows two Lambda task states, any executions show `Succeeded` status.

---

## 12. EventBridge — S3 Upload Rule

**What it does:** Watches the documents S3 bucket for new file uploads (`PutObject` events) and automatically triggers the Step Functions ingestion state machine. This is the glue between S3 and the pipeline.

**How to check:**
1. Go to **Amazon EventBridge** in the AWS Console
2. Click **Rules** in the left sidebar
3. Make sure the event bus is set to **default**
4. Search for `dev-opensearch-navco-search`
5. Click the rule → verify:
   - **Event pattern** matches S3 `PutObject` events on the documents bucket
   - **Target** is the Step Functions state machine ARN

**Healthy state:** Rule exists, is `Enabled`, target points to the correct state machine ARN.

---

## 13. API Gateway — HTTP API

**What it does:** The public-facing HTTP API that exposes the search and suggestions endpoints. Routes incoming HTTP requests to the correct Lambda function.

**How to check:**
1. Go to **API Gateway** in the AWS Console
2. Click **APIs** in the left sidebar
3. Search for `dev-opensearch-navco-search-api`
4. Click it → go to **Routes** in the left sidebar — you should see:
   - `GET /search` → integrated with search Lambda
   - `GET /suggestions` → integrated with suggestions Lambda
5. Click **Stages** → note the **Invoke URL** (this is your API base URL)
6. To test search: open a browser or use curl:
   ```
   curl "https://<invoke-url>/search?query=test"
   ```
7. To test suggestions:
   ```
   curl "https://<invoke-url>/suggestions?prefix=te"
   ```

**Healthy state:** API exists, both routes configured, invoke URL returns a JSON response.

---

## 14. CloudWatch — Lambda Logs

**What it does:** All Lambda function logs are automatically sent to CloudWatch. This is where you go to debug errors or verify successful executions.

**How to check:**
1. Go to **CloudWatch** in the AWS Console
2. Click **Log groups** in the left sidebar
3. You should see one log group per Lambda function:
   - `/aws/lambda/dev-opensearch-navco-search-index-bootstrap`
   - `/aws/lambda/dev-opensearch-navco-search-search`
   - `/aws/lambda/dev-opensearch-navco-search-suggestions`
   - `/aws/lambda/dev-opensearch-navco-search-processor`
   - `/aws/lambda/dev-opensearch-navco-search-embedding`
4. Click any log group → click the most recent log stream → review the log entries

**Healthy state:** All 5 log groups exist. Bootstrap log group has at least one log stream from the deployment run.

---

## Quick Health Check Summary

Run through this checklist after every deployment:

| # | Service | Resource Name | Expected Status |
|---|---|---|---|
| 1 | S3 | `dev-opensearch-navco-search-tfstate` | Exists, versioning on |
| 2 | S3 | `dev-opensearch-navco-search-documents-bucket` | Exists |
| 3 | OpenSearch Serverless | `dev-navco-search` | Active |
| 4 | IAM | 7 roles with `dev-opensearch-navco-search` prefix | All exist |
| 5 | Lambda Layer | `dev-opensearch-navco-search-opensearch-layer` | Exists, python3.13 |
| 6 | Lambda | `dev-opensearch-navco-search-index-bootstrap` | Exists, logs show success |
| 7 | Lambda | `dev-opensearch-navco-search-search` | Exists, API trigger attached |
| 8 | Lambda | `dev-opensearch-navco-search-suggestions` | Exists, API trigger attached |
| 9 | Lambda | `dev-opensearch-navco-search-processor` | Exists |
| 10 | Lambda | `dev-opensearch-navco-search-embedding` | Exists |
| 11 | Step Functions | `dev-opensearch-navco-search-ingestion` | Exists, diagram shows 2 steps |
| 12 | EventBridge | Rule with `dev-opensearch-navco-search` prefix | Enabled, targets state machine |
| 13 | API Gateway | `dev-opensearch-navco-search-api` | Exists, 2 routes, invoke URL works |
| 14 | CloudWatch | 5 log groups under `/aws/lambda/dev-opensearch-navco-search-*` | All exist |

# Tasks: RAG Pipeline Infrastructure

## Overview

This spec covers the full RAG pipeline — an ingestion side (S3 + EventBridge + Step Functions + Indexer Lambda) and a search side (API Gateway with /search and /suggestions only, Search/Suggestions/RAG Lambdas, OpenSearch Serverless, Bedrock Knowledge Base with Titan Embeddings, and Bedrock Agent Runtime with Claude 3 Haiku).

The implementation is broken into 10 task groups following the exact deployment order: backend → s3 → opensearch → python index script → bedrock → eventbridge → lambda → apigateway, then docs. All resource names use the opensearch-project-dev prefix via env vars. The Python 3.13 index script handles the OpenSearch index creation gap that Terraform can't cover, and the GitHub Actions workflow wires everything together with proper dependency ordering.

---

## 1. Backend Module (S3 + DynamoDB)

- [x] 1.1 Create `terraform/backend/` module with S3 bucket and DynamoDB table resources
  - Define `main.tf` with `aws_s3_bucket` (versioning enabled) and `aws_dynamodb_table` (PAY_PER_REQUEST, LockID hash key)
  - Define `variables.tf` with `state_bucket_name` and `lock_table_name` input variables
  - Define `outputs.tf` exporting `state_bucket_name` and `lock_table_name`
  - All names read from variables, no hardcoded strings
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 1.2 Write unit tests for backend module
  - Test that S3 bucket is created with correct name from environment variable
  - Test that DynamoDB table is created with correct name and versioning enabled
  - Test that outputs are correctly exported

- [x] 1.3 Write property-based tests for backend module
  - **Validates: Requirements 1.1, 1.3**
  - Property: For any valid bucket and table name (alphanumeric, hyphens, 3-63 chars), the module must create both resources with those exact names

---

## 2. S3 Bucket Module

- [x] 2.1 Create `terraform/s3/` module with S3 bucket for document storage
  - Define `main.tf` provisioning S3 bucket with versioning and public access blocked
  - Define `variables.tf` with `bucket_name` input variable
  - Define `outputs.tf` exporting `bucket_name` and `bucket_arn`
  - All names read from variables, no hardcoded strings
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 2.2 Write unit tests for S3 module
  - Test that S3 bucket is created with correct name from environment variable
  - Test that versioning is enabled
  - Test that public access is blocked
  - Test that outputs are correctly exported

- [x] 2.3 Write property-based tests for S3 module
  - **Validates: Requirements 2.1, 2.2**
  - Property: For any valid S3 bucket name, the module must create a bucket with that exact name and output both the name and ARN

---

## 3. OpenSearch Serverless Module

- [x] 3.1 Create `terraform/opensearch/` module with OpenSearch Serverless collection
  - Define `main.tf` provisioning OpenSearch Serverless collection with encryption and access policies
  - Define `variables.tf` with `collection_name` input variable
  - Define `outputs.tf` exporting `collection_endpoint` and `collection_arn`
  - All names read from variables, no hardcoded strings
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 3.2 Write unit tests for OpenSearch module
  - Test that OpenSearch Serverless collection is created with correct name
  - Test that encryption policy is configured
  - Test that access policy is configured
  - Test that outputs are correctly exported

- [x] 3.3 Write property-based tests for OpenSearch module
  - **Validates: Requirements 4.1, 4.3**
  - Property: For any valid collection name, the module must create a collection with that exact name and output both the endpoint and ARN

---

## 4. Python Index Creation Script

- [x] 4.1 Create `scripts/create_indexes.py` Python 3.13 script
  - Accept `OPENSEARCH_ENDPOINT` from environment variable or CLI argument
  - Create chunk-index with knn_vector field mapping (1536 dimensions)
  - Create metadata-index with doc_id, s3_key, title, uploaded_at, tags fields
  - Create suggestions-index with suggestion_id, text (completion type), doc_id, weight fields
  - _Requirements: 5.1, 5.2, 5.6_

- [x] 4.2 Implement error handling in index script
  - Skip creation if index already exists (HTTP 400 with resource_already_exists_exception)
  - Exit with non-zero status on other errors with descriptive message
  - _Requirements: 5.3, 5.4_

- [x] 4.3 Create `scripts/requirements.txt` for index script
  - List all Python dependencies (opensearch-py, boto3, requests-aws4auth)
  - _Requirements: 5.5_

- [x] 4.4 Write unit tests for index creation script
  - Test correct HTTP method and path for each index creation call (using mock HTTP client)
  - Test exit code 0 on already-exists response
  - Test exit code 1 on generic 500 response
  - Test correct index mappings for all three indexes

- [x] 4.5 Write property-based tests for index creation script
  - **Validates: Requirements 5.1, 5.3, 5.4, 5.6**
  - Property 1: For any valid OpenSearch endpoint, script must issue PUT requests for exactly three indexes with correct mappings
  - Property 2: For any HTTP response, script must exit with status 0 iff response is 2xx or already-exists, non-zero otherwise

---

## 5. Bedrock Knowledge Base Module

- [x] 5.1 Create `terraform/bedrock/` module with Bedrock Knowledge Base
  - Define `main.tf` provisioning Bedrock Knowledge Base with Titan Embeddings
  - Configure to read from S3 bucket and store embeddings in chunk-index
  - Declare explicit dependency on OpenSearch collection
  - Define `variables.tf` with knowledge_base_name, s3_bucket_arn, opensearch_endpoint
  - Define `outputs.tf` exporting knowledge_base_id
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 5.2 Create IAM roles for Bedrock Knowledge Base
  - Create IAM role allowing Bedrock to read from S3 bucket
  - Create IAM role allowing Bedrock to write to OpenSearch collection
  - _Requirements: 6.1_

- [x] 5.3 Write unit tests for Bedrock module
  - Test that Knowledge Base is created with correct name
  - Test that Titan Embeddings model is configured
  - Test that S3 data source is configured with correct bucket
  - Test that OpenSearch vector store is configured with correct endpoint
  - Test that outputs are correctly exported

- [x] 5.4 Write property-based tests for Bedrock module
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.5**
  - Property: For any valid knowledge base name, S3 bucket ARN, and OpenSearch endpoint, the module must create a Knowledge Base with those exact configurations

---

## 6. EventBridge + Step Functions Module

- [x] 6.1 Create `terraform/eventbridge/` module with EventBridge rule and Step Functions state machine
  - Define `main.tf` provisioning EventBridge rule listening for S3 ObjectCreated events
  - Configure rule to trigger Step Functions state machine
  - Define Step Functions state machine in ASL with InvokeIndexer task
  - Define `variables.tf` with s3_bucket_arn, indexer_lambda_arn
  - Define `outputs.tf` exporting state_machine_arn and rule_arn
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 6.2 Create IAM roles for EventBridge and Step Functions
  - Create IAM role allowing EventBridge to invoke Step Functions
  - Create IAM role allowing Step Functions to invoke Lambda
  - _Requirements: 3.1, 3.2_

- [ ] 6.3 Write unit tests for EventBridge module
  - Test that EventBridge rule is created with correct S3 event pattern
  - Test that Step Functions state machine is created with correct definition
  - Test that IAM roles have correct permissions
  - Test that outputs are correctly exported

- [ ] 6.4 Write property-based tests for EventBridge module
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
  - Property 4: For any deployment, the Step Functions state machine must contain an InvokeIndexer task that references the Indexer Lambda

---

## 7. Lambda Functions Module

- [x] 7.1 Create `terraform/lambda/` module with all four Lambda functions
  - Define `main.tf` provisioning Search, Suggestions, RAG, and Indexer Lambdas
  - Define `variables.tf` with function names, OpenSearch endpoint, Bedrock model ID
  - Define `outputs.tf` exporting ARNs of all four Lambda functions
  - _Requirements: 7.1, 7.6, 7.7_

- [x] 7.2 Implement Search Lambda function (`lambda/search/index.py`)
  - Proxy requests to OpenSearch
  - Query chunk-index and metadata-index for keyword or semantic search
  - Call RAG Lambda with retrieved context
  - _Requirements: 7.2_

- [x] 7.3 Implement Suggestions Lambda function (`lambda/suggestions/index.py`)
  - Proxy requests to OpenSearch
  - Query suggestions-index for autocomplete suggestions
  - _Requirements: 7.3_

- [x] 7.4 Implement RAG Lambda function (`lambda/rag/index.py`)
  - Invoke Bedrock Agent Runtime with Claude 3 Haiku model
  - Accept retrieved context and generate LLM responses
  - Implement retry logic with exponential backoff (up to 3 attempts)
  - _Requirements: 7.4_

- [x] 7.5 Implement Indexer Lambda function (`lambda/indexer/index.py`)
  - Index metadata and suggestions into OpenSearch
  - Write to metadata-index and suggestions-index
  - Raise exception on OpenSearch write failure
  - _Requirements: 7.5_

- [x] 7.6 Create IAM roles for Lambda functions
  - Create role allowing Search Lambda to query OpenSearch and invoke RAG Lambda
  - Create role allowing Suggestions Lambda to query OpenSearch
  - Create role allowing RAG Lambda to invoke Bedrock Agent Runtime
  - Create role allowing Indexer Lambda to write to OpenSearch
  - _Requirements: 7.1_

- [ ] 7.7 Write unit tests for Lambda functions
  - Test Search Lambda: verify correct OpenSearch query construction for known input
  - Test Suggestions Lambda: verify correct OpenSearch query for suggestions
  - Test RAG Lambda: verify correct Bedrock invocation payload for known search result
  - Test Indexer Lambda: verify correct OpenSearch write operations
  - Test error handling: verify HTTP 502/503 responses on OpenSearch/Bedrock errors

- [ ] 7.8 Write property-based tests for Lambda functions
  - **Validates: Requirements 7.2, 7.3, 7.4, 7.5**
  - Property: For any valid search query, Search Lambda must construct a valid OpenSearch query and invoke RAG Lambda with retrieved context

---

## 8. API Gateway Module

- [x] 8.1 Create `terraform/apigateway/` module with HTTP API
  - Define `main.tf` provisioning HTTP API with exactly two routes: POST /search and GET /suggestions
  - Integrate /search with Search Lambda
  - Integrate /suggestions with Suggestions Lambda
  - Ensure /upload and /coach endpoints are NOT provisioned
  - Define `variables.tf` with api_name, search_lambda_arn, suggestions_lambda_arn
  - Define `outputs.tf` exporting api_endpoint_url
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [x] 8.2 Create Lambda permissions for API Gateway
  - Grant API Gateway permission to invoke Search Lambda
  - Grant API Gateway permission to invoke Suggestions Lambda
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 8.3 Write unit tests for API Gateway module
  - Test that HTTP API is created with correct name
  - Test that exactly two routes are configured: POST /search and GET /suggestions
  - Test that /upload and /coach routes do NOT exist
  - Test that Lambda integrations are configured correctly
  - Test that outputs are correctly exported

- [ ] 8.4 Write property-based tests for API Gateway module
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
  - Property 3: For any deployment, the set of configured routes must equal exactly {POST /search, GET /suggestions}

---

## 9. GitHub Actions Deployment Workflow

- [x] 9.1 Create `.github/workflows/deploy.yml` GitHub Actions workflow
  - Trigger: workflow_dispatch with environment and branch inputs
  - Step 1: Checkout at selected branch
  - Step 2: terraform apply — backend/
  - Step 3: terraform apply — s3/
  - Step 4: terraform apply — opensearch/
  - Step 5: Setup Python 3.13, install requirements.txt, run create_indexes.py
  - Step 6: terraform apply — bedrock/
  - Step 7: terraform apply — eventbridge/
  - Step 8: terraform apply — lambda/
  - Step 9: terraform apply — apigateway/
  - _Requirements: 9.1, 9.2_

- [x] 9.2 Implement error handling and environment variable passing in workflow
  - Set continue-on-error: false on every step
  - Capture outputs from earlier Terraform steps
  - Export outputs as environment variables for later steps
  - Pass OPENSEARCH_ENDPOINT to index script
  - Updated to use AWS credentials (access key + secret key) instead of OIDC
  - _Requirements: 9.3, 9.4, 9.5, 9.6_

- [ ] 9.3 Write unit tests for workflow YAML
  - Parse deploy.yml and verify step names appear in required order
  - Verify all steps have continue-on-error: false
  - Verify Python 3.13 is installed before index script runs
  - Verify environment variables are passed between steps

- [ ] 9.4 Write property-based tests for workflow
  - **Validates: Requirements 9.2, 9.5**
  - Property 4: For any workflow_dispatch input combination, the step sequence must follow the required partial order: backend → s3 → opensearch → index script → bedrock → eventbridge → lambda → apigateway

---

## 10. Documentation

- [x] 10.1 Create comprehensive RAG pipeline documentation (`docs/README.md`)
  - Describe all components: S3, EventBridge, Step Functions, Indexer Lambda, OpenSearch, Bedrock Knowledge Base, Bedrock Agent Runtime, API Gateway, Search Lambda, Suggestions Lambda, RAG Lambda
  - Document component interactions and data flow
  - Include step-by-step end-to-end test guide
  - Provide sample request/response examples
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

---

## Summary

All 10 task groups are now defined with specific, actionable tasks. Each task includes:
- Clear implementation details
- Acceptance criteria or specific requirements
- References to relevant requirements from the spec
- Both unit and property-based tests where applicable

The tasks follow the exact deployment order specified in the design: backend → s3 → opensearch → python index script → bedrock → eventbridge → lambda → apigateway → docs.

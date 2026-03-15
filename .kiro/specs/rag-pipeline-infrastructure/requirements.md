# Requirements Document

## Introduction

This feature delivers a complete AWS RAG (Retrieval-Augmented Generation) pipeline infrastructure. The system has two parts: an existing ingestion pipeline (S3, EventBridge, Step Functions, Lambda indexer) for which infrastructure must be created, and a new search/retrieval pipeline (API Gateway, Lambda proxies, OpenSearch Serverless, Bedrock Knowledge Base, Bedrock Agent Runtime) that must be built from scratch. All infrastructure is managed via Terraform with a modular layout, a Python script handles OpenSearch index creation, and a GitHub Actions workflow orchestrates deployment with correct dependency ordering.

## Glossary

- **RAG_Pipeline**: The end-to-end Retrieval-Augmented Generation system combining document ingestion, vector search, and LLM-based response generation.
- **Terraform**: Infrastructure-as-Code tool used to provision all AWS resources.
- **Backend**: Terraform remote state backend consisting of an S3 bucket and DynamoDB table for state locking.
- **S3_Bucket**: AWS S3 bucket that stores raw uploaded files and their sidecar metadata files.
- **EventBridge_Rule**: AWS EventBridge rule that listens for S3 ObjectCreated events and triggers the Step Functions state machine.
- **Step_Functions**: AWS Step Functions state machine that orchestrates the ingestion job when a new object is created in S3.
- **Indexer_Lambda**: AWS Lambda function that indexes metadata and suggestions into OpenSearch.
- **API_Gateway**: AWS API Gateway exposing the `/search` and `/suggestions` endpoints to clients.
- **Search_Lambda**: AWS Lambda function acting as a proxy for the `/search` endpoint.
- **Suggestions_Lambda**: AWS Lambda function acting as a proxy for the `/suggestions` endpoint.
- **RAG_Lambda**: AWS Lambda function that invokes Bedrock Agent Runtime to perform RAG generation.
- **OpenSearch_Collection**: AWS OpenSearch Serverless collection hosting the chunk, metadata, and suggestions indexes.
- **Chunk_Index**: OpenSearch index storing vector embeddings of document chunks for semantic search.
- **Metadata_Index**: OpenSearch index storing document metadata.
- **Suggestions_Index**: OpenSearch index storing suggestion entries.
- **Index_Script**: Python script that creates the three OpenSearch indexes via the OpenSearch REST API.
- **Bedrock_Knowledge_Base**: AWS Bedrock Knowledge Base configured with Titan Embeddings that reads from S3, splits content into chunks, and creates vector embeddings stored in the Chunk_Index.
- **Bedrock_Agent_Runtime**: AWS Bedrock Agent Runtime used to invoke an LLM for RAG-based response generation.
- **GitHub_Actions**: CI/CD platform executing the deployment workflow defined in `.github/workflows/deploy.yml`.
- **Deploy_Workflow**: GitHub Actions workflow triggered via `workflow_dispatch` that deploys all infrastructure in dependency order.

---

## Requirements

### Requirement 1: Terraform Backend Module

**User Story:** As a DevOps engineer, I want a Terraform backend module, so that remote state is stored securely with state locking enabled.

#### Acceptance Criteria

1. THE Terraform SHALL include a `backend/` module that provisions an S3 bucket for remote state storage and a DynamoDB table for state locking.
2. WHEN the backend module is applied, THE Terraform SHALL output the S3 bucket name and DynamoDB table name for use by other modules.
3. THE Terraform SHALL use environment variables (not hardcoded names) for all resource name values in the backend module.

---

### Requirement 2: S3 Bucket Module

**User Story:** As a DevOps engineer, I want an S3 bucket provisioned via Terraform, so that raw files and sidecar metadata files can be stored for ingestion.

#### Acceptance Criteria

1. THE Terraform SHALL include an `s3/` module that provisions an S3 bucket for raw file and sidecar metadata file storage.
2. THE Terraform SHALL use environment variables (not hardcoded names) for the S3 bucket name.
3. WHEN the S3 module is applied, THE Terraform SHALL output the bucket name and bucket ARN for use by dependent modules.

---

### Requirement 3: EventBridge and Step Functions Module

**User Story:** As a DevOps engineer, I want EventBridge and Step Functions provisioned via Terraform, so that every new S3 object upload automatically triggers the ingestion state machine.

#### Acceptance Criteria

1. THE Terraform SHALL include an `eventbridge/` module that provisions an EventBridge rule listening for S3 ObjectCreated events on the S3_Bucket.
2. WHEN an S3 ObjectCreated event is detected, THE EventBridge_Rule SHALL trigger the Step_Functions state machine.
3. THE Terraform SHALL include a Step_Functions state machine definition within the `eventbridge/` module that represents the ingestion job orchestration.
4. THE Terraform SHALL use environment variables (not hardcoded names) for all resource names in the eventbridge module.

---

### Requirement 4: OpenSearch Serverless Module

**User Story:** As a DevOps engineer, I want an OpenSearch Serverless collection provisioned via Terraform, so that vector, metadata, and suggestions indexes can be hosted.

#### Acceptance Criteria

1. THE Terraform SHALL include an `opensearch/` module that provisions an OpenSearch Serverless collection.
2. WHEN the opensearch module is applied, THE Terraform SHALL output the collection endpoint and collection ARN for use by the Index_Script and Bedrock_Knowledge_Base.
3. THE Terraform SHALL use environment variables (not hardcoded names) for the collection name.
4. THE Terraform SHALL configure the necessary access policies and encryption policies for the OpenSearch_Collection.

---

### Requirement 5: OpenSearch Index Creation Script

**User Story:** As a DevOps engineer, I want a Python script to create OpenSearch indexes, so that the Chunk_Index, Metadata_Index, and Suggestions_Index exist before Bedrock Knowledge Base is configured.

#### Acceptance Criteria

1. THE Index_Script SHALL be written in Python 3.13 and create the Chunk_Index, Metadata_Index, and Suggestions_Index in the OpenSearch_Collection via the OpenSearch REST API.
2. THE Index_Script SHALL accept the OpenSearch collection endpoint as an environment variable or CLI argument.
3. WHEN an index already exists, THE Index_Script SHALL skip creation without raising an error.
4. IF the OpenSearch REST API returns an error during index creation, THEN THE Index_Script SHALL exit with a non-zero status code and print a descriptive error message.
5. THE Index_Script SHALL include a `requirements.txt` listing all Python dependencies required for execution.
6. THE Chunk_Index SHALL be configured with a `knn_vector` field mapping to support vector similarity search.

---

### Requirement 6: Bedrock Knowledge Base Module

**User Story:** As a DevOps engineer, I want a Bedrock Knowledge Base provisioned via Terraform after OpenSearch indexes exist, so that documents from S3 are chunked and embedded into the Chunk_Index automatically.

#### Acceptance Criteria

1. THE Terraform SHALL include a `bedrock/` module that provisions a Bedrock_Knowledge_Base configured to use Titan Embeddings.
2. THE Bedrock_Knowledge_Base SHALL be configured to read source documents from the S3_Bucket.
3. THE Bedrock_Knowledge_Base SHALL be configured to store vector embeddings in the Chunk_Index within the OpenSearch_Collection.
4. WHEN the bedrock module is applied, THE Terraform SHALL output the Knowledge Base ID for use by Lambda functions.
5. THE Terraform SHALL use environment variables (not hardcoded names) for all resource names in the bedrock module.
6. THE bedrock module SHALL declare an explicit dependency on the OpenSearch_Collection and Chunk_Index being available before provisioning.

---

### Requirement 7: Lambda Functions Module

**User Story:** As a DevOps engineer, I want all Lambda functions provisioned via Terraform, so that search, suggestions, and RAG generation logic can be executed serverlessly.

#### Acceptance Criteria

1. THE Terraform SHALL include a `lambda/` module that provisions the Search_Lambda, Suggestions_Lambda, RAG_Lambda, and Indexer_Lambda.
2. THE Search_Lambda SHALL be configured to proxy requests to OpenSearch_Collection for keyword or semantic search against the Chunk_Index and Metadata_Index.
3. THE Suggestions_Lambda SHALL be configured to proxy requests to OpenSearch_Collection for lookups against the Suggestions_Index.
4. THE RAG_Lambda SHALL be configured to invoke Bedrock_Agent_Runtime with a retrieved context to generate LLM responses.
5. THE Indexer_Lambda SHALL be configured to index metadata and suggestions into the Metadata_Index and Suggestions_Index.
6. THE Terraform SHALL use environment variables (not hardcoded names) for all Lambda function names and configuration values.
7. WHEN the lambda module is applied, THE Terraform SHALL output the ARNs of all Lambda functions for use by API Gateway and Step Functions.

---

### Requirement 8: API Gateway Module

**User Story:** As a DevOps engineer, I want an API Gateway provisioned via Terraform exposing only `/search` and `/suggestions`, so that clients can query the RAG pipeline without access to upload or coaching endpoints.

#### Acceptance Criteria

1. THE Terraform SHALL include an `apigateway/` module that provisions an API_Gateway with exactly two routes: `/search` and `/suggestions`.
2. THE `/search` route SHALL be integrated with the Search_Lambda.
3. THE `/suggestions` route SHALL be integrated with the Suggestions_Lambda.
4. THE API_Gateway SHALL NOT expose a `/upload` endpoint.
5. THE API_Gateway SHALL NOT expose a `/coach` endpoint.
6. WHEN the apigateway module is applied, THE Terraform SHALL output the API endpoint URL.
7. THE Terraform SHALL use environment variables (not hardcoded names) for all resource names in the apigateway module.

---

### Requirement 9: GitHub Actions Deployment Workflow

**User Story:** As a DevOps engineer, I want a GitHub Actions workflow, so that all infrastructure is deployed in the correct dependency order across environments without manual intervention.

#### Acceptance Criteria

1. THE Deploy_Workflow SHALL be defined at `.github/workflows/deploy.yml` and triggered via `workflow_dispatch` with inputs for selecting the target environment and branch.
2. THE Deploy_Workflow SHALL deploy modules in the following order: `backend` → `s3` → `opensearch` → Index_Script → `bedrock` → `eventbridge` → `lambda` → `apigateway`.
3. WHEN the Index_Script step runs, THE Deploy_Workflow SHALL install Python 3.13 and all dependencies from `requirements.txt` before executing the script.
4. THE Deploy_Workflow SHALL use environment variables (not static hardcoded names) for all AWS resource names throughout the workflow.
5. IF any deployment step fails, THEN THE Deploy_Workflow SHALL stop execution and report the failed step.
6. THE Deploy_Workflow SHALL pass outputs from earlier modules (e.g., OpenSearch endpoint, Knowledge Base ID) as inputs to later modules and scripts.

---

### Requirement 10: Documentation

**User Story:** As a developer or operator, I want a single comprehensive document, so that I can understand every component, how they interact, and how to test the full pipeline end-to-end.

#### Acceptance Criteria

1. THE RAG_Pipeline SHALL be documented in a single document that describes each component, its purpose, and how it interacts with other components.
2. THE documentation SHALL include a step-by-step end-to-end test guide that can be executed against a deployed AWS environment.
3. THE documentation SHALL include a simple end-to-end test example showing a sample request and expected response once all infrastructure is deployed.
4. THE documentation SHALL describe the relationship and data flow between S3_Bucket, EventBridge_Rule, Step_Functions, Indexer_Lambda, OpenSearch_Collection, Bedrock_Knowledge_Base, Bedrock_Agent_Runtime, API_Gateway, Search_Lambda, Suggestions_Lambda, and RAG_Lambda.

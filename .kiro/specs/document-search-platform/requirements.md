# Requirements: Document Ingestion, Search & Suggestions Platform

## Introduction

This specification defines a complete AWS-based document ingestion, search, and suggestions platform. The system enables users to upload documents to S3, automatically processes them through a serverless pipeline, generates embeddings using Amazon Bedrock, stores vectors and metadata in OpenSearch, and exposes search and suggestions APIs via API Gateway.

The platform is fully infrastructure-as-code using Terraform with modular design, environment-aware naming conventions, and automated deployment via GitHub Actions.

## Glossary

- **Document Ingestion Pipeline**: S3 upload → Step Functions → Document Processor Lambda → Embedding Generator Lambda → OpenSearch
- **Search API**: HTTP endpoint that queries OpenSearch metadata and vector indexes
- **Suggestions API**: HTTP endpoint that provides autocomplete suggestions
- **OpenSearch Collection**: Serverless OpenSearch instance hosting three indexes
- **Bedrock Embeddings**: Amazon Bedrock service generating vector embeddings (Titan model)
- **Index Bootstrap Lambda**: Lambda function that creates OpenSearch indexes after collection is provisioned
- **Environment**: Deployment target (dev, stg, prod)
- **Project Name**: Identifier for resource naming (e.g., opensearch-navco-search)

## Requirements

### Requirement 1: IAM Roles and Policies

**User Story**: As a DevOps engineer, I want IAM roles and policies configured, so that all AWS services have appropriate permissions.

**Acceptance Criteria**:
1. IAM module creates roles for:
   - Search Lambda (OpenSearch read access)
   - Suggestions Lambda (OpenSearch read access)
   - Document Processor Lambda (S3 read, Step Functions invoke)
   - Embedding Generator Lambda (Bedrock invoke, OpenSearch write)
   - Index Bootstrap Lambda (OpenSearch full access)
   - Step Functions (Lambda invoke permissions)
2. All policies follow least-privilege principle
3. All role names follow naming convention: `${var.env}-${var.project_name}-{role-name}`

### Requirement 2: S3 Document Bucket

**User Story**: As a user, I want to upload documents to S3, so that they are automatically processed.

**Acceptance Criteria**:
1. S3 module creates bucket for document uploads
2. Bucket name follows convention: `${var.env}-${var.project_name}-documents-bucket`
3. Versioning enabled
4. Public access blocked
5. S3 event configuration triggers Step Functions on ObjectCreated events
6. Module outputs bucket name and ARN

### Requirement 3: OpenSearch Collection

**User Story**: As a DevOps engineer, I want OpenSearch Serverless collection provisioned, so that indexes can be created and data stored.

**Acceptance Criteria**:
1. OpenSearch Serverless collection created
2. Collection name follows convention: `${var.env}-${var.project_name}-collection`
3. Encryption enabled
4. Access policies configured for Lambda access
5. Collection endpoint and ARN exported as outputs
6. No indexes created in this module (done via Lambda)

### Requirement 4: Index Bootstrap Lambda

**User Story**: As a DevOps engineer, I want a Lambda function that creates OpenSearch indexes, so that the collection is ready for data ingestion.

**Acceptance Criteria**:
1. Lambda function created with name: `${var.env}-${var.project_name}-index-bootstrap`
2. Function creates three indexes:
   - `metadata-index`: Stores document metadata (title, source, upload_date, tags)
   - `suggestions-index`: Stores autocomplete suggestions (text, weight, doc_id)
   - `vector-index`: Stores embeddings (vector, text, metadata)
3. Function handles already-existing indexes gracefully
4. Function exits with status 0 on success, non-zero on error
5. Function logs all operations to CloudWatch

### Requirement 5: Search Lambda

**User Story**: As an API user, I want to search documents, so that I can find relevant content.

**Acceptance Criteria**:
1. Lambda function created with name: `${var.env}-${var.project_name}-search`
2. Function accepts query parameter
3. Function searches metadata-index and vector-index
4. Function returns top 10 results with scores
5. Function handles errors gracefully (HTTP 502)
6. Function logs all searches to CloudWatch

### Requirement 6: Suggestions Lambda

**User Story**: As an API user, I want autocomplete suggestions, so that I can discover available content.

**Acceptance Criteria**:
1. Lambda function created with name: `${var.env}-${var.project_name}-suggestions`
2. Function accepts prefix parameter
3. Function queries suggestions-index
4. Function returns top 10 suggestions with weights
5. Function handles errors gracefully (HTTP 502)
6. Function logs all requests to CloudWatch

### Requirement 7: Document Processor Lambda

**User Story**: As a system, I want to extract text and metadata from uploaded documents, so that they can be embedded.

**Acceptance Criteria**:
1. Lambda function created with name: `${var.env}-${var.project_name}-doc-processor`
2. Function reads document from S3
3. Function extracts text content and metadata (title, size, upload_date)
4. Function passes content to Embedding Generator Lambda via Step Functions
5. Function handles errors gracefully
6. Function logs all operations to CloudWatch

### Requirement 8: Embedding Generator Lambda

**User Story**: As a system, I want to generate embeddings for document content, so that semantic search is possible.

**Acceptance Criteria**:
1. Lambda function created with name: `${var.env}-${var.project_name}-embedding-gen`
2. Function calls Bedrock Titan Embeddings model
3. Function writes embeddings to vector-index
4. Function writes metadata to metadata-index
5. Function generates and writes suggestions to suggestions-index
6. Function handles Bedrock throttling with retry logic
7. Function logs all operations to CloudWatch

### Requirement 9: Step Functions Ingestion Workflow

**User Story**: As a system, I want to orchestrate document processing, so that documents are processed in correct order.

**Acceptance Criteria**:
1. State machine created with name: `${var.env}-${var.project_name}-ingestion-workflow`
2. State machine has two steps:
   - Step 1: Invoke Document Processor Lambda
   - Step 2: Invoke Embedding Generator Lambda
3. State machine passes S3 object info between steps
4. State machine handles errors and retries
5. State machine logs execution to CloudWatch

### Requirement 10: API Gateway

**User Story**: As an API user, I want HTTP endpoints for search and suggestions, so that I can query the platform.

**Acceptance Criteria**:
1. HTTP API created with name: `${var.env}-${var.project_name}-api`
2. API has two routes:
   - POST /search → Search Lambda
   - GET /suggestions → Suggestions Lambda
3. API returns JSON responses
4. API handles errors gracefully
5. API endpoint URL exported as output

### Requirement 11: Bedrock Knowledge Base Configuration

**User Story**: As a system, I want Bedrock configured to work with OpenSearch, so that embeddings are generated correctly.

**Acceptance Criteria**:
1. Bedrock Knowledge Base created (or equivalent configuration)
2. Knowledge Base depends on indexes being created
3. Knowledge Base configured to use Titan Embeddings model
4. Knowledge Base configured to read from S3 bucket
5. Knowledge Base configured to store vectors in OpenSearch

### Requirement 12: GitHub Actions Workflow

**User Story**: As a DevOps engineer, I want automated deployment via GitHub Actions, so that infrastructure is provisioned consistently.

**Acceptance Criteria**:
1. Workflow file created at `.github/workflows/infra-ci-cd.yml`
2. Workflow supports workflow_dispatch with inputs:
   - environment (dev, stg, prod)
   - branch (git branch to deploy)
3. Workflow uses AWS credentials from GitHub secrets
4. Workflow follows strict resource creation sequence:
   - IAM roles and policies
   - S3 bucket
   - OpenSearch collection
   - Index Bootstrap Lambda
   - Invoke Index Bootstrap Lambda
   - Bedrock Knowledge Base
   - Ingestion Lambdas
   - Step Functions
   - Search & Suggestions Lambdas
   - API Gateway
5. Workflow logs all steps and outputs

### Requirement 13: Documentation

**User Story**: As a developer, I want comprehensive documentation, so that I understand the system architecture and deployment process.

**Acceptance Criteria**:
1. Single README.md file that explains:
   - System architecture
   - Terraform module structure
   - Naming conventions
   - Resource dependencies
   - GitHub Actions workflow
   - How to set GitHub secrets
   - How to run the workflow
   - How to test the system
2. README includes ASCII architecture diagram
3. README includes example API requests/responses
4. README includes troubleshooting section

## Non-Functional Requirements

### Performance
- Search Lambda response time: < 2 seconds
- Suggestions Lambda response time: < 500ms
- Document processing: < 5 minutes per document

### Scalability
- Support concurrent document uploads
- Support concurrent API requests
- Auto-scale Lambda functions

### Security
- AWS credentials via GitHub secrets (not hardcoded)
- IAM roles with least-privilege permissions
- Encrypted OpenSearch collection
- No sensitive data in logs

### Reliability
- Retry logic for Bedrock throttling
- Error handling for all Lambda functions
- CloudWatch logging for all operations
- State machine error handling

## Acceptance Criteria Summary

All requirements must be met for the platform to be considered complete:
- ✓ All Terraform modules created with correct naming conventions
- ✓ All Lambda functions implemented with error handling
- ✓ GitHub Actions workflow with correct resource creation sequence
- ✓ Single comprehensive README.md documentation
- ✓ All resources deployed successfully via GitHub Actions
- ✓ API endpoints functional and tested

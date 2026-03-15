# Tasks: Document Ingestion, Search & Suggestions Platform

## Overview

This task list covers the complete implementation of a document ingestion, search, and suggestions platform on AWS. The system is built with Terraform modules, Lambda functions, OpenSearch, and GitHub Actions CI/CD.

Tasks are organized by component and follow the strict resource creation sequence defined in the design document.

---

## Phase 1: Infrastructure Foundation

### 1.1 IAM Module
- [x] 1.1.1 Create `infra/modules/iam/main.tf`
  - Define IAM roles for all Lambda functions
  - Define IAM policies for OpenSearch, S3, Bedrock, Step Functions access
  - Ensure least-privilege permissions
  
- [x] 1.1.2 Create `infra/modules/iam/variables.tf`
  - Define input variables for role names
  
- [x] 1.1.3 Create `infra/modules/iam/outputs.tf`
  - Export all role ARNs

### 1.2 S3 Documents Module
- [x] 1.2.1 Create `infra/modules/s3_documents/main.tf`
  - Create S3 bucket with versioning
  - Block public access
  - Configure S3 event to trigger Step Functions
  
- [x] 1.2.2 Create `infra/modules/s3_documents/variables.tf`
  - Define bucket name variable
  
- [x] 1.2.3 Create `infra/modules/s3_documents/outputs.tf`
  - Export bucket name and ARN

### 1.3 OpenSearch Collection Module
- [x] 1.3.1 Create `infra/modules/opensearch_collection/main.tf`
  - Create OpenSearch Serverless collection
  - Configure encryption
  - Configure access policies
  
- [x] 1.3.2 Create `infra/modules/opensearch_collection/variables.tf`
  - Define collection name variable
  
- [x] 1.3.3 Create `infra/modules/opensearch_collection/outputs.tf`
  - Export collection endpoint and ARN

---

## Phase 2: Index Bootstrap

### 2.1 Index Bootstrap Lambda
- [x] 2.1.1 Create `infra/modules/opensearch_index_bootstrap_lambda/lambda_function.py`
  - Connect to OpenSearch
  - Create metadata-index
  - Create vector-index
  - Create suggestions-index
  - Handle already-existing indexes
  - Log all operations
  
- [x] 2.1.2 Create `infra/modules/opensearch_index_bootstrap_lambda/main.tf`
  - Create Lambda function
  - Attach IAM role
  - Configure environment variables
  
- [x] 2.1.3 Create `infra/modules/opensearch_index_bootstrap_lambda/variables.tf`
  - Define function name variable
  
- [x] 2.1.4 Create `infra/modules/opensearch_index_bootstrap_lambda/outputs.tf`
  - Export Lambda ARN

---

## Phase 3: Search & Query APIs

### 3.1 Search Lambda
- [x] 3.1.1 Create `infra/modules/lambda_search/lambda_function.py`
  - Accept query parameter
  - Search metadata-index and vector-index
  - Return top 10 results with scores
  - Handle errors (HTTP 502)
  - Log all searches
  
- [x] 3.1.2 Create `infra/modules/lambda_search/main.tf`
  - Create Lambda function
  - Attach IAM role
  - Configure environment variables
  
- [x] 3.1.3 Create `infra/modules/lambda_search/variables.tf`
  - Define function name variable
  
- [x] 3.1.4 Create `infra/modules/lambda_search/outputs.tf`
  - Export Lambda ARN

### 3.2 Suggestions Lambda
- [x] 3.2.1 Create `infra/modules/lambda_suggestions/lambda_function.py`
  - Accept prefix parameter
  - Query suggestions-index
  - Return top 10 suggestions with weights
  - Handle errors (HTTP 502)
  - Log all requests
  
- [x] 3.2.2 Create `infra/modules/lambda_suggestions/main.tf`
  - Create Lambda function
  - Attach IAM role
  - Configure environment variables
  
- [x] 3.2.3 Create `infra/modules/lambda_suggestions/variables.tf`
  - Define function name variable
  
- [x] 3.2.4 Create `infra/modules/lambda_suggestions/outputs.tf`
  - Export Lambda ARN

---

## Phase 4: Ingestion Pipeline

### 4.1 Document Processor Lambda
- [x] 4.1.1 Create `infra/modules/lambda_ingestion_processor/lambda_function.py`
  - Read document from S3
  - Extract text content
  - Extract metadata (title, size, upload_date)
  - Pass to Embedding Generator via Step Functions
  - Handle errors
  - Log all operations
  
- [x] 4.1.2 Create `infra/modules/lambda_ingestion_processor/main.tf`
  - Create Lambda function
  - Attach IAM role
  - Configure environment variables
  
- [x] 4.1.3 Create `infra/modules/lambda_ingestion_processor/variables.tf`
  - Define function name variable
  
- [x] 4.1.4 Create `infra/modules/lambda_ingestion_processor/outputs.tf`
  - Export Lambda ARN

### 4.2 Embedding Generator Lambda
- [x] 4.2.1 Create `infra/modules/lambda_embedding_generator/lambda_function.py`
  - Call Bedrock Titan Embeddings model
  - Write embeddings to vector-index
  - Write metadata to metadata-index
  - Generate and write suggestions to suggestions-index
  - Implement retry logic for Bedrock throttling
  - Log all operations
  
- [x] 4.2.2 Create `infra/modules/lambda_embedding_generator/main.tf`
  - Create Lambda function
  - Attach IAM role
  - Configure environment variables
  
- [x] 4.2.3 Create `infra/modules/lambda_embedding_generator/variables.tf`
  - Define function name variable
  
- [x] 4.2.4 Create `infra/modules/lambda_embedding_generator/outputs.tf`
  - Export Lambda ARN

### 4.3 Step Functions Ingestion Workflow
- [x] 4.3.1 Create `infra/modules/step_functions_ingestion/state_machine.json`
  - Define ASL state machine
  - Step 1: Invoke Document Processor Lambda
  - Step 2: Invoke Embedding Generator Lambda
  - Pass S3 object info between steps
  - Handle errors and retries
  
- [x] 4.3.2 Create `infra/modules/step_functions_ingestion/main.tf`
  - Create state machine
  - Attach IAM role
  - Configure S3 event trigger
  
- [x] 4.3.3 Create `infra/modules/step_functions_ingestion/variables.tf`
  - Define state machine name variable
  
- [x] 4.3.4 Create `infra/modules/step_functions_ingestion/outputs.tf`
  - Export state machine ARN

---

## Phase 5: API & Bedrock

### 5.1 API Gateway
- [x] 5.1.1 Create `infra/modules/api_gateway/main.tf`
  - Create HTTP API
  - Create POST /search route → Search Lambda
  - Create GET /suggestions route → Suggestions Lambda
  - Configure CORS if needed
  
- [x] 5.1.2 Create `infra/modules/api_gateway/variables.tf`
  - Define API name variable
  
- [x] 5.1.3 Create `infra/modules/api_gateway/outputs.tf`
  - Export API endpoint URL

### 5.2 Bedrock Knowledge Base
- [x] 5.2.1 Create `infra/modules/bedrock_knowledge_base/main.tf`
  - Create Bedrock Knowledge Base
  - Configure Titan Embeddings model
  - Configure S3 data source
  - Configure OpenSearch vector store
  - Add depends_on for indexes
  
- [x] 5.2.2 Create `infra/modules/bedrock_knowledge_base/variables.tf`
  - Define knowledge base name variable
  
- [x] 5.2.3 Create `infra/modules/bedrock_knowledge_base/outputs.tf`
  - Export Knowledge Base ID

---

## Phase 6: Root Module & CI/CD

### 6.1 Root Terraform Module
- [x] 6.1.1 Create `infra/main.tf`
  - Call all modules in correct order
  - Pass variables between modules
  - Define module dependencies
  
- [x] 6.1.2 Create `infra/variables.tf`
  - Define env variable (dev, stg, prod)
  - Define project_name variable
  - Define region variable
  
- [x] 6.1.3 Create `infra/outputs.tf`
  - Export all important outputs
  
- [x] 6.1.4 Create `infra/terraform.tfvars`
  - Set default values

### 6.2 GitHub Actions Workflow
- [x] 6.2.1 Create `.github/workflows/infra-ci-cd.yml`
  - Trigger: workflow_dispatch with environment and branch inputs
  - Checkout code
  - Setup Terraform
  - Terraform init, plan, apply (core infrastructure)
  - Invoke Index Bootstrap Lambda
  - Terraform apply (dependent infrastructure)
  - Output deployment summary
  - Use AWS credentials from GitHub secrets
  - Follow strict resource creation sequence

---

## Phase 7: Documentation

### 7.1 README Documentation
- [x] 7.1.1 Create `README.md`
  - System architecture with ASCII diagram
  - Terraform module structure explanation
  - Naming conventions
  - Resource dependencies and creation sequence
  - GitHub Actions workflow explanation
  - How to set GitHub secrets
  - How to run the workflow
  - How to test the system
  - Example API requests/responses
  - Troubleshooting section

---

## Summary

Total tasks: 40+ implementation tasks across 7 phases

**Execution Order**:
1. Phase 1: Infrastructure Foundation (IAM, S3, OpenSearch)
2. Phase 2: Index Bootstrap Lambda
3. Phase 3: Search & Query APIs (Search, Suggestions Lambdas)
4. Phase 4: Ingestion Pipeline (Processor, Embedding Generator, Step Functions)
5. Phase 5: API & Bedrock (API Gateway, Bedrock Knowledge Base)
6. Phase 6: Root Module & CI/CD (Terraform root, GitHub Actions)
7. Phase 7: Documentation (README)

**Key Constraints**:
- All resource names follow `${var.env}-${var.project_name}-{resource-type}` pattern
- Strict resource creation sequence must be maintained
- GitHub Actions workflow must invoke Index Bootstrap Lambda between core and dependent infrastructure
- No pytest or automated tests (keep it simple)
- Single README.md documentation file
- AWS credentials via GitHub secrets only

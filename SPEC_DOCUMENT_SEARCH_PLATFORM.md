# Document Ingestion, Search & Suggestions Platform - NEW SPEC

## Status: ✅ SPEC CREATED - READY FOR IMPLEMENTATION

A new, comprehensive specification has been created for a document ingestion, search, and suggestions platform on AWS.

---

## Spec Location

`.kiro/specs/document-search-platform/`

### Files Created

1. **requirements.md** - 13 detailed requirements covering all system components
2. **design.md** - Complete architecture design with ASCII diagrams, module structure, data models
3. **tasks.md** - 40+ implementation tasks organized in 7 phases
4. **.config.kiro** - Spec configuration

---

## Key Differences from Previous RAG Pipeline

| Aspect | Previous RAG Pipeline | New Document Search Platform |
|--------|----------------------|------------------------------|
| **Structure** | Monolithic Terraform | Modular Terraform under `infra/` |
| **Naming** | `opensearch-project-{env}` | `{env}-{project_name}-{resource}` |
| **Lambdas** | Search, Suggestions, RAG, Indexer | Search, Suggestions, Processor, Embedding Gen, Bootstrap |
| **Index Creation** | Python script | Lambda function (Index Bootstrap) |
| **Workflow** | EventBridge + Step Functions | Step Functions only |
| **Documentation** | Multiple guides | Single README.md |
| **Bedrock** | Knowledge Base | Knowledge Base + Embeddings config |
| **Resource Sequence** | Linear | Strict 2-phase (core → bootstrap → dependent) |

---

## Architecture Summary

### User-Facing APIs
- **POST /search** - Search documents by query
- **GET /suggestions** - Get autocomplete suggestions

### Ingestion Pipeline
```
S3 Upload → Step Functions → Document Processor Lambda → Embedding Generator Lambda → OpenSearch
```

### Data Storage
- **metadata-index** - Document metadata (title, source, upload_date, tags)
- **vector-index** - Embeddings (1536-dim Titan vectors)
- **suggestions-index** - Autocomplete suggestions

### Key Components
- **5 Lambda Functions**: Search, Suggestions, Document Processor, Embedding Generator, Index Bootstrap
- **1 Step Functions Workflow**: Orchestrates document processing
- **1 OpenSearch Collection**: Serverless with 3 indexes
- **1 API Gateway**: HTTP API with 2 routes
- **1 Bedrock Knowledge Base**: For embeddings
- **Modular Terraform**: 10 modules with clear dependencies

---

## Terraform Module Structure

```
infra/
├── modules/
│   ├── iam/                                    # IAM roles & policies
│   ├── s3_documents/                           # S3 bucket + events
│   ├── opensearch_collection/                  # OpenSearch collection
│   ├── opensearch_index_bootstrap_lambda/      # Index creation Lambda
│   ├── lambda_search/                          # Search API Lambda
│   ├── lambda_suggestions/                     # Suggestions API Lambda
│   ├── lambda_ingestion_processor/             # Document processor
│   ├── lambda_embedding_generator/             # Embedding generator
│   ├── step_functions_ingestion/               # Ingestion workflow
│   ├── api_gateway/                            # HTTP API
│   └── bedrock_knowledge_base/                 # Bedrock config
├── main.tf                                     # Root module
├── variables.tf                                # Root variables
├── outputs.tf                                  # Root outputs
└── terraform.tfvars                            # Default values
```

---

## Resource Creation Sequence

### Phase 1: Core Infrastructure
1. IAM roles and policies
2. S3 bucket
3. OpenSearch collection
4. Index Bootstrap Lambda

### Phase 2: Invoke Bootstrap
- GitHub Actions invokes Index Bootstrap Lambda
- Creates 3 OpenSearch indexes
- Waits for completion

### Phase 3: Dependent Infrastructure
5. Bedrock Knowledge Base
6. Ingestion Lambdas (Processor, Embedding Generator)
7. Step Functions workflow
8. Search & Suggestions Lambdas
9. API Gateway

---

## Naming Convention

All resources follow this pattern:

```
${var.env}-${var.project_name}-{resource-type}
```

**Example** (env=dev, project_name=opensearch-navco-search):
- S3 bucket: `dev-opensearch-navco-search-documents-bucket`
- OpenSearch: `dev-opensearch-navco-search-collection`
- Search Lambda: `dev-opensearch-navco-search-search`
- Suggestions Lambda: `dev-opensearch-navco-search-suggestions`
- Document Processor: `dev-opensearch-navco-search-doc-processor`
- Embedding Generator: `dev-opensearch-navco-search-embedding-gen`
- Index Bootstrap: `dev-opensearch-navco-search-index-bootstrap`
- Step Functions: `dev-opensearch-navco-search-ingestion-workflow`
- API Gateway: `dev-opensearch-navco-search-api`

---

## GitHub Actions Workflow

**File**: `.github/workflows/infra-ci-cd.yml`

**Trigger**: `workflow_dispatch` with inputs:
- `environment` (dev, stg, prod)
- `branch` (git branch to deploy)

**Stages**:
1. Checkout code
2. Setup Terraform
3. Terraform init/plan
4. Terraform apply (core infrastructure)
5. Invoke Index Bootstrap Lambda
6. Terraform apply (dependent infrastructure)
7. Output deployment summary

**Credentials**: AWS access key & secret key from GitHub secrets

---

## Implementation Phases

### Phase 1: Infrastructure Foundation
- IAM module (roles & policies)
- S3 documents module
- OpenSearch collection module

### Phase 2: Index Bootstrap
- Index Bootstrap Lambda (creates 3 indexes)

### Phase 3: Search & Query APIs
- Search Lambda
- Suggestions Lambda

### Phase 4: Ingestion Pipeline
- Document Processor Lambda
- Embedding Generator Lambda
- Step Functions workflow

### Phase 5: API & Bedrock
- API Gateway
- Bedrock Knowledge Base

### Phase 6: Root Module & CI/CD
- Root Terraform module
- GitHub Actions workflow

### Phase 7: Documentation
- Single comprehensive README.md

---

## Key Features

✅ **Modular Terraform Design**
- 10 independent modules
- Clear dependencies
- Environment-aware naming

✅ **Strict Resource Sequence**
- 2-phase deployment (core → bootstrap → dependent)
- GitHub Actions enforces ordering
- Index Bootstrap Lambda invoked between phases

✅ **Production-Ready**
- Error handling in all Lambdas
- Retry logic for Bedrock throttling
- CloudWatch logging
- IAM least-privilege permissions

✅ **Simple & Readable**
- No pytest or test scaffolding
- Well-commented code
- Single README.md documentation
- ASCII architecture diagrams

✅ **AWS Credentials**
- GitHub secrets for access key & secret key
- No CLI profiles required
- Environment variables for Terraform

---

## Next Steps

To implement this spec:

1. **Review the spec documents**:
   - `.kiro/specs/document-search-platform/requirements.md`
   - `.kiro/specs/document-search-platform/design.md`
   - `.kiro/specs/document-search-platform/tasks.md`

2. **Start implementation** (when ready):
   - Execute tasks in order (Phase 1 → Phase 7)
   - Follow resource creation sequence
   - Use naming conventions consistently

3. **Deploy via GitHub Actions**:
   - Set GitHub secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
   - Trigger workflow with environment and branch
   - Monitor deployment

---

## Comparison: Old vs New

### Old RAG Pipeline (opensearch-project-dev)
- Monolithic structure
- EventBridge + Step Functions
- Python index creation script
- Multiple documentation files
- Terraform backend module

### New Document Search Platform (opensearch-navco-search)
- Modular structure (10 modules)
- Step Functions only
- Lambda index bootstrap
- Single README.md
- No backend module (simpler)

**Both can coexist** - they are separate projects in different spec directories.

---

## Status

✅ **Specification Complete**
- Requirements: 13 detailed requirements
- Design: Complete architecture with diagrams
- Tasks: 40+ implementation tasks
- Ready for implementation

**Next**: Execute tasks to implement the platform

---

**Spec Created**: March 15, 2026  
**Spec ID**: doc-search-platform-v1  
**Status**: Ready for Implementation

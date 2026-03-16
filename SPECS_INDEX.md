# Kiro Specs Index

This repository contains multiple AWS infrastructure specifications. Each spec is independent and can be implemented separately.

---

## Spec 1: RAG Pipeline Infrastructure (COMPLETED)

**Location**: `.kiro/specs/rag-pipeline-infrastructure/`

**Status**: ✅ Implementation Complete

**Description**: Complete AWS Retrieval-Augmented Generation (RAG) pipeline with:
- S3 document storage
- EventBridge + Step Functions ingestion
- OpenSearch Serverless with 3 indexes
- Bedrock Knowledge Base with Titan Embeddings
- Lambda functions for search, suggestions, RAG, and indexing
- API Gateway with /search and /suggestions endpoints
- GitHub Actions deployment workflow

**Key Files**:
- `requirements.md` - 10 requirements
- `design.md` - Complete architecture
- `tasks.md` - 10 task groups (all completed)

**Deliverables**:
- ✅ 4 Lambda functions implemented
- ✅ GitHub Actions workflow (AWS credentials)
- ✅ Comprehensive documentation (5 guides)
- ✅ Deployment checklist
- ✅ Quick start guide

**Documentation**:
- `IMPLEMENTATION_GUIDE.md` - Complete reference
- `QUICK_START.md` - 5-minute setup
- `GITHUB_SECRETS_SETUP.md` - Secrets configuration
- `DEPLOYMENT_CHECKLIST.md` - Verification procedures
- `IMPLEMENTATION_COMPLETE.md` - Project summary

---

## Spec 2: Document Ingestion, Search & Suggestions Platform (NEW)

**Location**: `.kiro/specs/document-search-platform/`

**Status**: ✅ Spec Created - Ready for Implementation

**Description**: Modular document ingestion, search, and suggestions platform on AWS with:
- Modular Terraform structure (10 modules)
- Environment-aware naming conventions
- Strict resource creation sequence
- 5 Lambda functions (Search, Suggestions, Processor, Embedding Gen, Bootstrap)
- Step Functions ingestion workflow
- OpenSearch with 3 indexes
- Bedrock embeddings integration
- API Gateway with /search and /suggestions
- GitHub Actions CI/CD with 2-phase deployment

**Key Files**:
- `requirements.md` - 13 detailed requirements
- `design.md` - Complete architecture with ASCII diagrams
- `tasks.md` - 40+ implementation tasks (7 phases)

**Terraform Modules** (10 total):
1. `iam/` - IAM roles and policies
2. `s3_documents/` - S3 bucket + events
3. `opensearch_collection/` - OpenSearch collection
4. `opensearch_index_bootstrap_lambda/` - Index creation Lambda
5. `lambda_search/` - Search API Lambda
6. `lambda_suggestions/` - Suggestions API Lambda
7. `lambda_ingestion_processor/` - Document processor
8. `lambda_embedding_generator/` - Embedding generator
9. `step_functions_ingestion/` - Ingestion workflow
10. `api_gateway/` - HTTP API
11. `bedrock_knowledge_base/` - Bedrock config

**Key Features**:
- ✅ Modular Terraform design
- ✅ Strict resource creation sequence
- ✅ 2-phase deployment (core → bootstrap → dependent)
- ✅ Environment-aware naming
- ✅ Production-ready error handling
- ✅ Single README.md documentation

**Next Steps**:
- Review spec documents
- Execute tasks in order (Phase 1 → Phase 7)
- Deploy via GitHub Actions

**Summary Document**: `SPEC_DOCUMENT_SEARCH_PLATFORM.md`

---

## Comparison

| Aspect | RAG Pipeline | Search Platform |
|--------|--------------|-----------------|
| **Status** | ✅ Complete | ✅ Spec Ready |
| **Structure** | Monolithic | Modular (10 modules) |
| **Naming** | `opensearch-project-{env}` | `{env}-{project_name}-{resource}` |
| **Lambdas** | 4 (Search, Suggestions, RAG, Indexer) | 5 (+ Bootstrap) |
| **Index Creation** | Python script | Lambda function |
| **Workflow** | EventBridge + Step Functions | Step Functions only |
| **Documentation** | Multiple guides | Single README.md |
| **Deployment** | Single phase | 2-phase (core → bootstrap → dependent) |
| **Bedrock** | Knowledge Base | KB + Embeddings config |

---

## How to Use

### For RAG Pipeline (Already Implemented)

1. Read: `QUICK_START.md`
2. Setup: `GITHUB_SECRETS_SETUP.md`
3. Deploy: Trigger GitHub Actions workflow
4. Reference: `IMPLEMENTATION_GUIDE.md`

### For Document Search Platform (Ready to Implement)

1. Review: `.kiro/specs/document-search-platform/requirements.md`
2. Understand: `.kiro/specs/document-search-platform/design.md`
3. Execute: `.kiro/specs/document-search-platform/tasks.md` (Phase 1 → Phase 7)
4. Deploy: GitHub Actions workflow (when ready)

---

## File Structure

```
.
├── .kiro/specs/
│   ├── rag-pipeline-infrastructure/          (COMPLETED)
│   │   ├── requirements.md
│   │   ├── design.md
│   │   ├── tasks.md
│   │   └── .config.kiro
│   │
│   └── document-search-platform/             (NEW - SPEC READY)
│       ├── requirements.md
│       ├── design.md
│       ├── tasks.md
│       └── .config.kiro
│
├── SPECS_INDEX.md                            (This file)
├── SPEC_DOCUMENT_SEARCH_PLATFORM.md          (New spec summary)
├── IMPLEMENTATION_GUIDE.md                   (RAG Pipeline)
├── QUICK_START.md                            (RAG Pipeline)
├── GITHUB_SECRETS_SETUP.md                   (RAG Pipeline)
├── DEPLOYMENT_CHECKLIST.md                   (RAG Pipeline)
├── IMPLEMENTATION_COMPLETE.md                (RAG Pipeline)
└── README_IMPLEMENTATION.md                  (RAG Pipeline)
```

---

## Key Differences

### RAG Pipeline
- **Focus**: Complete RAG system with LLM integration
- **Approach**: Monolithic Terraform structure
- **Status**: Fully implemented and documented
- **Use Case**: Document ingestion + semantic search + LLM answers

### Document Search Platform
- **Focus**: Modular, scalable search platform
- **Approach**: Modular Terraform with strict dependencies
- **Status**: Specification complete, ready for implementation
- **Use Case**: Document ingestion + search + suggestions

---

## Next Steps

### If You Want to Deploy RAG Pipeline
→ Start with `QUICK_START.md`

### If You Want to Implement Document Search Platform
→ Start with `.kiro/specs/document-search-platform/requirements.md`

### If You Want to Understand Both
→ Read `SPECS_INDEX.md` (this file) then choose one

---

## Support

- **RAG Pipeline Questions**: See `IMPLEMENTATION_GUIDE.md`
- **Document Search Platform Questions**: See `.kiro/specs/document-search-platform/design.md`
- **General Architecture**: See ASCII diagrams in design documents
- **Deployment Issues**: See troubleshooting sections in documentation

---

**Last Updated**: March 15, 2026  
**Total Specs**: 2 (1 completed, 1 ready for implementation)  
**Total Modules**: 17 (7 for RAG Pipeline, 10 for Search Platform)

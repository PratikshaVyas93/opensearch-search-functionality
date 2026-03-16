# How Terraform Manages Resource Creation Order

## Overview

Terraform uses **explicit dependencies** (`depends_on`) and **implicit dependencies** (resource references) to determine the correct order of resource creation. This ensures that OpenSearch collection is created before indexes, and indexes are created before Bedrock Knowledge Base.

---

## Two Types of Dependencies

### 1. **Implicit Dependencies** (Automatic)

When you reference an output from one resource in another resource, Terraform automatically creates a dependency.

**Example**:
```hcl
module "opensearch_collection" {
  source = "./modules/opensearch_collection"
  # ... configuration
}

module "index_bootstrap_lambda" {
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  # ↑ This reference creates an implicit dependency
  # Terraform knows: index_bootstrap_lambda depends on opensearch_collection
}
```

**How it works**:
- Terraform sees that `index_bootstrap_lambda` needs `opensearch_collection.collection_endpoint`
- Terraform automatically waits for `opensearch_collection` to be created first
- Then it creates `index_bootstrap_lambda`

### 2. **Explicit Dependencies** (Manual)

You explicitly tell Terraform which resources must be created first using `depends_on`.

**Example**:
```hcl
module "bedrock_knowledge_base" {
  # ... configuration

  depends_on = [
    module.opensearch_collection,
    module.s3_documents,
    module.index_bootstrap_lambda
  ]
}
```

**How it works**:
- Terraform sees the `depends_on` block
- It waits for all listed resources to be created first
- Then it creates the current resource

---

## Resource Creation Order in Our Project

### Phase 1: Infrastructure Foundation

```
1. S3 Documents Bucket
   └─ No dependencies (created first)

2. OpenSearch Collection
   └─ Depends on: IAM roles (for access policies)

3. IAM Roles
   └─ Depends on: S3 bucket ARN, OpenSearch collection ARN
```

**Terraform Code**:
```hcl
module "s3_documents" {
  source = "./modules/s3_documents"
  # No dependencies - created immediately
}

module "opensearch_collection" {
  source = "./modules/opensearch_collection"
  access_principal_arns = [
    module.iam.index_bootstrap_lambda_role_arn,  # ← Implicit dependency
    # ... other roles
  ]
}

module "iam" {
  source = "./modules/iam"
  opensearch_collection_arn = module.opensearch_collection.collection_arn  # ← Implicit dependency
  s3_bucket_arn = module.s3_documents.bucket_arn  # ← Implicit dependency
}
```

**Execution Order**:
```
S3 Bucket → OpenSearch Collection → IAM Roles
```

---

### Phase 2: Index Bootstrap Lambda

```
Index Bootstrap Lambda
├─ Implicit dependency: opensearch_collection.collection_endpoint
└─ Explicit dependency: depends_on = [module.opensearch_collection, module.iam]
```

**Terraform Code**:
```hcl
module "index_bootstrap_lambda" {
  source = "./modules/opensearch_index_bootstrap_lambda"
  
  opensearch_endpoint = module.opensearch_collection.collection_endpoint  # ← Implicit
  lambda_role_arn = module.iam.index_bootstrap_lambda_role_arn  # ← Implicit
  
  depends_on = [
    module.opensearch_collection,  # ← Explicit
    module.iam
  ]
}
```

**Execution Order**:
```
OpenSearch Collection + IAM → Index Bootstrap Lambda
```

**What happens**:
1. OpenSearch collection is created
2. IAM roles are created
3. Index Bootstrap Lambda is created (with access to OpenSearch endpoint)

---

### Phase 3: Search & Suggestions Lambdas

```
Search Lambda
├─ Implicit dependency: opensearch_collection.collection_endpoint
├─ Implicit dependency: iam.search_lambda_role_arn
└─ Explicit dependency: depends_on = [module.opensearch_collection, module.iam]

Suggestions Lambda
├─ Implicit dependency: opensearch_collection.collection_endpoint
├─ Implicit dependency: iam.suggestions_lambda_role_arn
└─ Explicit dependency: depends_on = [module.opensearch_collection, module.iam]
```

**Terraform Code**:
```hcl
module "search_lambda" {
  source = "./modules/lambda_search"
  
  opensearch_endpoint = module.opensearch_collection.collection_endpoint  # ← Implicit
  lambda_role_arn = module.iam.search_lambda_role_arn  # ← Implicit
  
  depends_on = [
    module.opensearch_collection,  # ← Explicit
    module.iam
  ]
}
```

**Execution Order**:
```
OpenSearch Collection + IAM → Search Lambda
OpenSearch Collection + IAM → Suggestions Lambda
```

---

### Phase 4: Ingestion Pipeline

```
Document Processor Lambda
└─ Explicit dependency: depends_on = [module.iam]

Embedding Generator Lambda
├─ Implicit dependency: opensearch_collection.collection_endpoint
├─ Implicit dependency: iam.embedding_generator_lambda_role_arn
└─ Explicit dependency: depends_on = [module.opensearch_collection, module.iam]

Step Functions
├─ Implicit dependency: document_processor_lambda.lambda_arn
├─ Implicit dependency: embedding_generator_lambda.lambda_arn
└─ Explicit dependency: depends_on = [module.document_processor_lambda, module.embedding_generator_lambda, module.iam]
```

**Terraform Code**:
```hcl
module "document_processor_lambda" {
  source = "./modules/lambda_ingestion_processor"
  lambda_role_arn = module.iam.document_processor_lambda_role_arn  # ← Implicit
  depends_on = [module.iam]  # ← Explicit
}

module "embedding_generator_lambda" {
  source = "./modules/lambda_embedding_generator"
  opensearch_endpoint = module.opensearch_collection.collection_endpoint  # ← Implicit
  lambda_role_arn = module.iam.embedding_generator_lambda_role_arn  # ← Implicit
  depends_on = [module.opensearch_collection, module.iam]  # ← Explicit
}

module "step_functions_ingestion" {
  source = "./modules/step_functions_ingestion"
  document_processor_lambda_arn = module.document_processor_lambda.lambda_arn  # ← Implicit
  embedding_generator_lambda_arn = module.embedding_generator_lambda.lambda_arn  # ← Implicit
  depends_on = [
    module.document_processor_lambda,  # ← Explicit
    module.embedding_generator_lambda,
    module.iam
  ]
}
```

**Execution Order**:
```
IAM → Document Processor Lambda
OpenSearch Collection + IAM → Embedding Generator Lambda
Document Processor Lambda + Embedding Generator Lambda + IAM → Step Functions
```

---

### Phase 5: API & Bedrock

```
API Gateway
├─ Implicit dependency: search_lambda.lambda_invoke_arn
├─ Implicit dependency: suggestions_lambda.lambda_invoke_arn
└─ Explicit dependency: depends_on = [module.search_lambda, module.suggestions_lambda]

Bedrock Knowledge Base
├─ Implicit dependency: opensearch_collection.collection_arn
├─ Implicit dependency: s3_documents.bucket_arn
└─ Explicit dependency: depends_on = [
     module.opensearch_collection,
     module.s3_documents,
     module.index_bootstrap_lambda  ← KEY: Waits for indexes to be created
   ]
```

**Terraform Code**:
```hcl
module "api_gateway" {
  source = "./modules/api_gateway"
  search_lambda_invoke_arn = module.search_lambda.lambda_invoke_arn  # ← Implicit
  suggestions_lambda_invoke_arn = module.suggestions_lambda.lambda_invoke_arn  # ← Implicit
  depends_on = [
    module.search_lambda,  # ← Explicit
    module.suggestions_lambda
  ]
}

module "bedrock_knowledge_base" {
  source = "./modules/bedrock_knowledge_base"
  opensearch_collection_arn = module.opensearch_collection.collection_arn  # ← Implicit
  s3_bucket_arn = module.s3_documents.bucket_arn  # ← Implicit
  
  depends_on = [
    module.opensearch_collection,  # ← Explicit
    module.s3_documents,
    module.index_bootstrap_lambda  # ← KEY: Ensures indexes are created first
  ]
}
```

**Execution Order**:
```
Search Lambda + Suggestions Lambda → API Gateway
OpenSearch Collection + S3 + Index Bootstrap Lambda → Bedrock Knowledge Base
```

---

## Complete Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                    TERRAFORM DEPENDENCY GRAPH                   │
└─────────────────────────────────────────────────────────────────┘

                          S3 Bucket
                              ↓
                    OpenSearch Collection
                              ↓
                          IAM Roles
                         ↙    ↓    ↘
                        /     |     \
                       /      |      \
            Index Bootstrap   |    Search Lambda
                 Lambda       |    Suggestions Lambda
                       \      |      /
                        \     |     /
                         ↘    ↓    ↙
                    Document Processor
                    Embedding Generator
                              ↓
                        Step Functions
                              ↓
                        API Gateway
                              ↓
                    Bedrock Knowledge Base
```

---

## How GitHub Actions Enforces Additional Ordering

While Terraform handles most dependencies, GitHub Actions adds an extra layer of control:

### GitHub Actions Workflow (2-Phase Deployment)

**Phase 1: Core Infrastructure**
```yaml
- Terraform Apply (Core Infrastructure)
  - Creates: S3, OpenSearch, IAM, Lambdas
  
- Invoke Index Bootstrap Lambda
  - Manually calls the Lambda to create indexes
  - Waits for completion
```

**Phase 2: Dependent Infrastructure**
```yaml
- Terraform Apply (Dependent Infrastructure)
  - Creates: API Gateway, Bedrock Knowledge Base
  - These depend on indexes being created in Phase 1
```

**Why this matters**:
- Terraform can't directly invoke Lambda functions
- GitHub Actions manually invokes the Index Bootstrap Lambda
- This ensures indexes are created before Bedrock Knowledge Base is created
- Bedrock Knowledge Base needs the indexes to exist

---

## Key Takeaways

### 1. **Implicit Dependencies** (Automatic)
```hcl
opensearch_endpoint = module.opensearch_collection.collection_endpoint
# Terraform automatically knows: this resource depends on opensearch_collection
```

### 2. **Explicit Dependencies** (Manual)
```hcl
depends_on = [
  module.opensearch_collection,
  module.index_bootstrap_lambda
]
# Terraform explicitly waits for these resources first
```

### 3. **Resource References Create Dependencies**
```hcl
# This creates an implicit dependency:
lambda_role_arn = module.iam.search_lambda_role_arn
# Terraform knows: search_lambda depends on iam module
```

### 4. **Terraform Builds a Dependency Graph**
- Terraform analyzes all resources and their dependencies
- Creates a directed acyclic graph (DAG)
- Executes resources in the correct order
- Can parallelize independent resources

### 5. **GitHub Actions Adds Manual Control**
- Phase 1: Create core infrastructure
- Invoke Index Bootstrap Lambda manually
- Phase 2: Create dependent infrastructure
- Ensures indexes exist before Bedrock Knowledge Base

---

## Example: Why Bedrock Depends on Index Bootstrap Lambda

```hcl
module "bedrock_knowledge_base" {
  source = "./modules/bedrock_knowledge_base"
  
  opensearch_collection_arn = module.opensearch_collection.collection_arn
  s3_bucket_arn = module.s3_documents.bucket_arn
  
  depends_on = [
    module.opensearch_collection,      # Collection must exist
    module.s3_documents,               # S3 bucket must exist
    module.index_bootstrap_lambda      # ← KEY: Indexes must be created
  ]
}
```

**Why**:
1. Bedrock Knowledge Base needs to connect to OpenSearch
2. OpenSearch collection must exist (implicit dependency)
3. OpenSearch indexes must exist (explicit dependency on bootstrap Lambda)
4. Without this dependency, Bedrock would try to connect to empty OpenSearch
5. Bedrock would fail because it can't find the indexes

---

## Verification

You can see the dependency graph with:

```bash
cd infra
terraform graph | dot -Tsvg > graph.svg
```

This generates a visual representation of all dependencies.

---

## Summary

Terraform ensures correct resource creation order through:

1. **Implicit Dependencies** - Automatic when you reference resource outputs
2. **Explicit Dependencies** - Manual `depends_on` blocks
3. **Dependency Graph** - Terraform builds and executes in correct order
4. **GitHub Actions** - Adds manual control for Lambda invocation
5. **Parallel Execution** - Independent resources created simultaneously

This ensures:
- ✅ OpenSearch collection created first
- ✅ Indexes created via Lambda (Phase 1)
- ✅ Bedrock Knowledge Base created after indexes (Phase 2)
- ✅ All resources in correct order
- ✅ No failures due to missing dependencies


# Terraform Dependency Flow Diagram

## Visual Representation of Resource Creation Order

### Phase 1: Infrastructure Foundation

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: FOUNDATION                          │
└─────────────────────────────────────────────────────────────────┘

Step 1: Create S3 Bucket (No dependencies)
┌──────────────────────┐
│   S3 Documents       │
│   Bucket             │
└──────────────────────┘
         ↓
Step 2: Create OpenSearch Collection (Depends on IAM roles)
┌──────────────────────┐
│  OpenSearch          │
│  Collection          │
└──────────────────────┘
         ↓
Step 3: Create IAM Roles (Depends on S3 & OpenSearch ARNs)
┌──────────────────────┐
│   IAM Roles          │
│   - Search           │
│   - Suggestions      │
│   - Processor        │
│   - Embedding        │
│   - Bootstrap        │
└──────────────────────┘
```

**Terraform Code**:
```hcl
# Step 1: S3 (no dependencies)
module "s3_documents" {
  source = "./modules/s3_documents"
}

# Step 2: OpenSearch (references IAM roles)
module "opensearch_collection" {
  access_principal_arns = [
    module.iam.index_bootstrap_lambda_role_arn,  # ← Implicit dependency
    # ... other roles
  ]
}

# Step 3: IAM (references S3 & OpenSearch)
module "iam" {
  opensearch_collection_arn = module.opensearch_collection.collection_arn  # ← Implicit
  s3_bucket_arn = module.s3_documents.bucket_arn  # ← Implicit
}
```

---

### Phase 2: Index Bootstrap Lambda

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2: INDEX BOOTSTRAP                     │
└─────────────────────────────────────────────────────────────────┘

Prerequisites Met:
✓ OpenSearch Collection exists
✓ IAM Roles exist

Create Index Bootstrap Lambda
┌──────────────────────────────────────┐
│  Index Bootstrap Lambda              │
│  ├─ Implicit: opensearch_endpoint    │
│  ├─ Implicit: lambda_role_arn        │
│  └─ Explicit: depends_on [           │
│      opensearch_collection,          │
│      iam                             │
│    ]                                 │
└──────────────────────────────────────┘
         ↓
Lambda Creates 3 Indexes:
┌──────────────────────────────────────┐
│  OpenSearch Indexes                  │
│  ├─ metadata-index                   │
│  ├─ vector-index                     │
│  └─ suggestions-index                │
└──────────────────────────────────────┘
```

**Terraform Code**:
```hcl
module "index_bootstrap_lambda" {
  source = "./modules/opensearch_index_bootstrap_lambda"
  
  # Implicit dependencies (references)
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  lambda_role_arn = module.iam.index_bootstrap_lambda_role_arn
  
  # Explicit dependencies
  depends_on = [
    module.opensearch_collection,
    module.iam
  ]
}
```

---

### Phase 3: Search & Query APIs

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 3: SEARCH & QUERY                      │
└─────────────────────────────────────────────────────────────────┘

Prerequisites Met:
✓ OpenSearch Collection exists
✓ IAM Roles exist

Create Search Lambda                Create Suggestions Lambda
┌──────────────────────┐            ┌──────────────────────┐
│  Search Lambda       │            │ Suggestions Lambda   │
│  ├─ Implicit: OS EP  │            │ ├─ Implicit: OS EP   │
│  ├─ Implicit: IAM    │            │ ├─ Implicit: IAM     │
│  └─ Explicit: deps   │            │ └─ Explicit: deps    │
└──────────────────────┘            └──────────────────────┘
         ↓                                    ↓
    Can query                          Can provide
    OpenSearch                         suggestions
```

**Terraform Code**:
```hcl
module "search_lambda" {
  opensearch_endpoint = module.opensearch_collection.collection_endpoint  # Implicit
  lambda_role_arn = module.iam.search_lambda_role_arn  # Implicit
  depends_on = [module.opensearch_collection, module.iam]  # Explicit
}

module "suggestions_lambda" {
  opensearch_endpoint = module.opensearch_collection.collection_endpoint  # Implicit
  lambda_role_arn = module.iam.suggestions_lambda_role_arn  # Implicit
  depends_on = [module.opensearch_collection, module.iam]  # Explicit
}
```

---

### Phase 4: Ingestion Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 4: INGESTION PIPELINE                  │
└─────────────────────────────────────────────────────────────────┘

Prerequisites Met:
✓ IAM Roles exist
✓ OpenSearch Collection exists

Create Document Processor Lambda
┌──────────────────────────────────────┐
│  Document Processor Lambda           │
│  ├─ Implicit: lambda_role_arn        │
│  └─ Explicit: depends_on [iam]       │
└──────────────────────────────────────┘
         ↓
Create Embedding Generator Lambda
┌──────────────────────────────────────┐
│  Embedding Generator Lambda          │
│  ├─ Implicit: opensearch_endpoint    │
│  ├─ Implicit: lambda_role_arn        │
│  └─ Explicit: depends_on [           │
│      opensearch_collection,          │
│      iam                             │
│    ]                                 │
└──────────────────────────────────────┘
         ↓
Create Step Functions State Machine
┌──────────────────────────────────────┐
│  Step Functions Ingestion Workflow   │
│  ├─ Implicit: processor_lambda_arn   │
│  ├─ Implicit: embedding_lambda_arn   │
│  └─ Explicit: depends_on [           │
│      document_processor_lambda,      │
│      embedding_generator_lambda,     │
│      iam                             │
│    ]                                 │
└──────────────────────────────────────┘
         ↓
    Orchestrates:
    S3 → Processor → Embedding → OpenSearch
```

**Terraform Code**:
```hcl
module "document_processor_lambda" {
  lambda_role_arn = module.iam.document_processor_lambda_role_arn  # Implicit
  depends_on = [module.iam]  # Explicit
}

module "embedding_generator_lambda" {
  opensearch_endpoint = module.opensearch_collection.collection_endpoint  # Implicit
  lambda_role_arn = module.iam.embedding_generator_lambda_role_arn  # Implicit
  depends_on = [module.opensearch_collection, module.iam]  # Explicit
}

module "step_functions_ingestion" {
  document_processor_lambda_arn = module.document_processor_lambda.lambda_arn  # Implicit
  embedding_generator_lambda_arn = module.embedding_generator_lambda.lambda_arn  # Implicit
  depends_on = [
    module.document_processor_lambda,  # Explicit
    module.embedding_generator_lambda,
    module.iam
  ]
}
```

---

### Phase 5: API & Bedrock (THE CRITICAL PART)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 5: API & BEDROCK                       │
└─────────────────────────────────────────────────────────────────┘

Prerequisites Met:
✓ Search Lambda exists
✓ Suggestions Lambda exists
✓ OpenSearch Collection exists
✓ OpenSearch Indexes exist (created by Index Bootstrap Lambda)
✓ S3 Bucket exists

Create API Gateway
┌──────────────────────────────────────┐
│  API Gateway                         │
│  ├─ Implicit: search_lambda_arn      │
│  ├─ Implicit: suggestions_lambda_arn │
│  └─ Explicit: depends_on [           │
│      search_lambda,                  │
│      suggestions_lambda              │
│    ]                                 │
└──────────────────────────────────────┘
         ↓
    Exposes:
    POST /search
    GET /suggestions

Create Bedrock Knowledge Base
┌──────────────────────────────────────┐
│  Bedrock Knowledge Base              │
│  ├─ Implicit: OS collection_arn      │
│  ├─ Implicit: S3 bucket_arn          │
│  └─ Explicit: depends_on [           │
│      opensearch_collection,          │
│      s3_documents,                   │
│      index_bootstrap_lambda  ← KEY!  │
│    ]                                 │
└──────────────────────────────────────┘
         ↓
    Connects to:
    ✓ OpenSearch Collection
    ✓ OpenSearch Indexes (metadata, vector, suggestions)
    ✓ S3 Bucket
```

**Terraform Code**:
```hcl
module "api_gateway" {
  search_lambda_invoke_arn = module.search_lambda.lambda_invoke_arn  # Implicit
  suggestions_lambda_invoke_arn = module.suggestions_lambda.lambda_invoke_arn  # Implicit
  depends_on = [
    module.search_lambda,  # Explicit
    module.suggestions_lambda
  ]
}

module "bedrock_knowledge_base" {
  opensearch_collection_arn = module.opensearch_collection.collection_arn  # Implicit
  s3_bucket_arn = module.s3_documents.bucket_arn  # Implicit
  
  depends_on = [
    module.opensearch_collection,      # Explicit: Collection must exist
    module.s3_documents,               # Explicit: S3 must exist
    module.index_bootstrap_lambda      # Explicit: Indexes must be created!
  ]
}
```

---

## Complete Dependency Chain

```
S3 Bucket
    ↓
OpenSearch Collection ← IAM Roles
    ↓
Index Bootstrap Lambda
    ↓
Indexes Created (metadata, vector, suggestions)
    ↓
Search Lambda ← IAM Roles
Suggestions Lambda ← IAM Roles
Document Processor Lambda ← IAM Roles
Embedding Generator Lambda ← IAM Roles
    ↓
Step Functions
    ↓
API Gateway
    ↓
Bedrock Knowledge Base ← Depends on Index Bootstrap Lambda
```

---

## Why Bedrock Depends on Index Bootstrap Lambda

### ❌ WITHOUT the dependency:

```
Terraform would try to:
1. Create OpenSearch Collection
2. Create Bedrock Knowledge Base immediately
3. Bedrock tries to connect to OpenSearch
4. ❌ FAILS: No indexes exist yet!
```

### ✅ WITH the dependency:

```
Terraform ensures:
1. Create OpenSearch Collection
2. Create Index Bootstrap Lambda
3. Lambda creates indexes (metadata, vector, suggestions)
4. Create Bedrock Knowledge Base
5. ✅ SUCCESS: Indexes exist, Bedrock connects successfully
```

---

## How Terraform Knows the Order

### 1. **Implicit Dependencies** (Automatic)
```hcl
opensearch_endpoint = module.opensearch_collection.collection_endpoint
# Terraform sees: "This resource needs opensearch_collection"
# Terraform automatically waits for opensearch_collection first
```

### 2. **Explicit Dependencies** (Manual)
```hcl
depends_on = [
  module.opensearch_collection,
  module.index_bootstrap_lambda
]
# Terraform sees: "Wait for these resources first"
# Terraform waits for all listed resources before creating this one
```

### 3. **Terraform Builds a Graph**
```
Terraform analyzes all resources and creates a directed graph:

S3 → OpenSearch → IAM → Index Bootstrap → Bedrock
                  ↓
            Search Lambda
            Suggestions Lambda
            Processor Lambda
            Embedding Lambda
                  ↓
            Step Functions
                  ↓
            API Gateway
```

### 4. **Terraform Executes in Order**
```
Terraform walks the graph and executes:
1. Resources with no dependencies (S3)
2. Resources whose dependencies are met (OpenSearch)
3. Resources whose dependencies are met (IAM)
4. And so on...
```

---

## GitHub Actions Adds Extra Control

```
GitHub Actions Workflow:

Phase 1: Terraform Apply (Core Infrastructure)
├─ Creates: S3, OpenSearch, IAM, Lambdas
└─ Terraform handles all dependencies

Phase 1.5: Invoke Index Bootstrap Lambda (Manual)
├─ GitHub Actions manually calls the Lambda
├─ Lambda creates indexes
└─ Waits for completion

Phase 2: Terraform Apply (Dependent Infrastructure)
├─ Creates: API Gateway, Bedrock Knowledge Base
├─ Bedrock depends on indexes being created
└─ Terraform handles all dependencies
```

**Why this matters**:
- Terraform can't directly invoke Lambda functions
- GitHub Actions provides the manual invocation
- This ensures indexes are created before Bedrock
- Bedrock Knowledge Base needs the indexes to exist

---

## Summary

### Terraform Ensures Correct Order Through:

1. **Implicit Dependencies** - Automatic when you reference outputs
2. **Explicit Dependencies** - Manual `depends_on` blocks
3. **Dependency Graph** - Terraform builds and executes in correct order
4. **GitHub Actions** - Adds manual control for Lambda invocation

### Result:

✅ OpenSearch collection created first  
✅ Indexes created via Lambda (Phase 1)  
✅ Bedrock Knowledge Base created after indexes (Phase 2)  
✅ All resources in correct order  
✅ No failures due to missing dependencies  


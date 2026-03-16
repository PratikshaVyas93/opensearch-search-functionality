# Terraform Dependency Code Examples

## How Terraform Knows the Creation Order

### Example 1: Implicit Dependency (Automatic)

When you reference an output from one resource in another, Terraform automatically creates a dependency.

```hcl
# Module 1: OpenSearch Collection
module "opensearch_collection" {
  source = "./modules/opensearch_collection"
  collection_name = "${var.env}-${var.project_name}-collection"
  # ... other configuration
}

# Module 2: Index Bootstrap Lambda
module "index_bootstrap_lambda" {
  source = "./modules/opensearch_index_bootstrap_lambda"
  
  # This line creates an IMPLICIT dependency
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  #                     ↑
  #                     Terraform sees: "This needs opensearch_collection"
  #                     Terraform automatically waits for opensearch_collection first
  
  lambda_role_arn = module.iam.index_bootstrap_lambda_role_arn
  # ... other configuration
}
```

**What Terraform does**:
1. Sees that `index_bootstrap_lambda` references `opensearch_collection.collection_endpoint`
2. Automatically creates a dependency: `index_bootstrap_lambda` depends on `opensearch_collection`
3. Creates `opensearch_collection` first
4. Then creates `index_bootstrap_lambda`

---

### Example 2: Explicit Dependency (Manual)

You explicitly tell Terraform which resources must be created first using `depends_on`.

```hcl
# Module: Bedrock Knowledge Base
module "bedrock_knowledge_base" {
  source = "./modules/bedrock_knowledge_base"
  
  knowledge_base_name = "${var.env}-${var.project_name}-kb"
  
  # Implicit dependencies (references)
  opensearch_collection_arn = module.opensearch_collection.collection_arn
  s3_bucket_arn = module.s3_documents.bucket_arn
  
  # Explicit dependencies (manual)
  depends_on = [
    module.opensearch_collection,      # Wait for this first
    module.s3_documents,               # Wait for this first
    module.index_bootstrap_lambda      # Wait for this first (KEY!)
  ]
  #
  # Terraform sees: "Don't create this until these are done"
  # Terraform waits for all three modules to be created first
}
```

**What Terraform does**:
1. Sees the `depends_on` block
2. Waits for `opensearch_collection` to be created
3. Waits for `s3_documents` to be created
4. Waits for `index_bootstrap_lambda` to be created
5. Then creates `bedrock_knowledge_base`

---

## Real-World Example: Complete Dependency Chain

### Step 1: Create S3 Bucket (No Dependencies)

```hcl
module "s3_documents" {
  source = "./modules/s3_documents"
  
  bucket_name = "${var.env}-${var.project_name}-documents-bucket"
  env = var.env
  project_name = var.project_name
  
  # No dependencies - created immediately
}
```

**Terraform execution**:
```
✓ S3 Bucket created (no dependencies)
```

---

### Step 2: Create OpenSearch Collection (Depends on IAM)

```hcl
module "opensearch_collection" {
  source = "./modules/opensearch_collection"
  
  collection_name = "${var.env}-${var.project_name}-collection"
  env = var.env
  project_name = var.project_name
  
  # Implicit dependency: references IAM roles
  access_principal_arns = [
    module.iam.index_bootstrap_lambda_role_arn,
    module.iam.search_lambda_role_arn,
    module.iam.suggestions_lambda_role_arn,
    module.iam.document_processor_lambda_role_arn,
    module.iam.embedding_generator_lambda_role_arn
  ]
  # ↑ Terraform sees: "This needs module.iam"
  # ↑ Terraform automatically waits for IAM first
}
```

**Terraform execution**:
```
✓ S3 Bucket created
✓ IAM Roles created (because OpenSearch references them)
✓ OpenSearch Collection created (after IAM)
```

---

### Step 3: Create IAM Roles (Depends on S3 & OpenSearch)

```hcl
module "iam" {
  source = "./modules/iam"
  
  env = var.env
  project_name = var.project_name
  region = var.region
  
  # Implicit dependencies: references S3 and OpenSearch
  opensearch_collection_arn = module.opensearch_collection.collection_arn
  #                           ↑ Terraform sees: "This needs opensearch_collection"
  
  s3_bucket_arn = module.s3_documents.bucket_arn
  #               ↑ Terraform sees: "This needs s3_documents"
  
  document_processor_lambda_arn = ""
  embedding_generator_lambda_arn = ""
}
```

**Terraform execution**:
```
✓ S3 Bucket created
✓ OpenSearch Collection created
✓ IAM Roles created (after S3 and OpenSearch)
```

---

### Step 4: Create Index Bootstrap Lambda (Depends on OpenSearch & IAM)

```hcl
module "index_bootstrap_lambda" {
  source = "./modules/opensearch_index_bootstrap_lambda"
  
  function_name = "${var.env}-${var.project_name}-index-bootstrap"
  
  # Implicit dependencies
  lambda_role_arn = module.iam.index_bootstrap_lambda_role_arn
  #                 ↑ Terraform sees: "This needs module.iam"
  
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  #                     ↑ Terraform sees: "This needs module.opensearch_collection"
  
  region = var.region
  env = var.env
  project_name = var.project_name
  opensearch_layer_arn = aws_lambda_layer_version.opensearch.arn
  
  # Explicit dependencies (redundant but clear)
  depends_on = [
    module.opensearch_collection,
    module.iam
  ]
}
```

**Terraform execution**:
```
✓ S3 Bucket created
✓ OpenSearch Collection created
✓ IAM Roles created
✓ Index Bootstrap Lambda created (after OpenSearch & IAM)
```

---

### Step 5: Create Search Lambda (Depends on OpenSearch & IAM)

```hcl
module "search_lambda" {
  source = "./modules/lambda_search"
  
  function_name = "${var.env}-${var.project_name}-search"
  
  # Implicit dependencies
  lambda_role_arn = module.iam.search_lambda_role_arn
  #                 ↑ Terraform sees: "This needs module.iam"
  
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  #                     ↑ Terraform sees: "This needs module.opensearch_collection"
  
  region = var.region
  env = var.env
  project_name = var.project_name
  opensearch_layer_arn = aws_lambda_layer_version.opensearch.arn
  
  # Explicit dependencies
  depends_on = [
    module.opensearch_collection,
    module.iam
  ]
}
```

**Terraform execution**:
```
✓ S3 Bucket created
✓ OpenSearch Collection created
✓ IAM Roles created
✓ Index Bootstrap Lambda created
✓ Search Lambda created (can run in parallel with Index Bootstrap Lambda)
```

---

### Step 6: Create Bedrock Knowledge Base (Depends on OpenSearch, S3, and Index Bootstrap Lambda)

```hcl
module "bedrock_knowledge_base" {
  source = "./modules/bedrock_knowledge_base"
  
  knowledge_base_name = "${var.env}-${var.project_name}-kb"
  env = var.env
  project_name = var.project_name
  
  # Implicit dependencies
  opensearch_collection_arn = module.opensearch_collection.collection_arn
  #                           ↑ Terraform sees: "This needs module.opensearch_collection"
  
  s3_bucket_arn = module.s3_documents.bucket_arn
  #               ↑ Terraform sees: "This needs module.s3_documents"
  
  # Explicit dependencies (KEY!)
  depends_on = [
    module.opensearch_collection,      # Collection must exist
    module.s3_documents,               # S3 must exist
    module.index_bootstrap_lambda      # Indexes must be created!
  ]
  # ↑ This is the critical dependency!
  # ↑ Without this, Bedrock would be created before indexes exist
  # ↑ Bedrock would fail because it can't find the indexes
}
```

**Terraform execution**:
```
✓ S3 Bucket created
✓ OpenSearch Collection created
✓ IAM Roles created
✓ Index Bootstrap Lambda created
✓ Search Lambda created
✓ Suggestions Lambda created
✓ Document Processor Lambda created
✓ Embedding Generator Lambda created
✓ Step Functions created
✓ API Gateway created
✓ Bedrock Knowledge Base created (LAST - after all dependencies)
```

---

## Why the Bedrock Dependency is Critical

### ❌ WITHOUT `depends_on = [module.index_bootstrap_lambda]`:

```hcl
module "bedrock_knowledge_base" {
  source = "./modules/bedrock_knowledge_base"
  
  opensearch_collection_arn = module.opensearch_collection.collection_arn
  s3_bucket_arn = module.s3_documents.bucket_arn
  
  depends_on = [
    module.opensearch_collection,
    module.s3_documents
    # ❌ Missing: module.index_bootstrap_lambda
  ]
}
```

**What happens**:
1. Terraform creates OpenSearch Collection
2. Terraform creates S3 Bucket
3. Terraform creates Bedrock Knowledge Base immediately
4. Bedrock tries to connect to OpenSearch
5. ❌ **FAILS**: No indexes exist yet!
6. Bedrock can't find metadata-index, vector-index, suggestions-index
7. Deployment fails

---

### ✅ WITH `depends_on = [module.index_bootstrap_lambda]`:

```hcl
module "bedrock_knowledge_base" {
  source = "./modules/bedrock_knowledge_base"
  
  opensearch_collection_arn = module.opensearch_collection.collection_arn
  s3_bucket_arn = module.s3_documents.bucket_arn
  
  depends_on = [
    module.opensearch_collection,
    module.s3_documents,
    module.index_bootstrap_lambda  # ✅ Ensures indexes are created first
  ]
}
```

**What happens**:
1. Terraform creates OpenSearch Collection
2. Terraform creates S3 Bucket
3. Terraform creates Index Bootstrap Lambda
4. Index Bootstrap Lambda creates indexes (metadata, vector, suggestions)
5. Terraform creates Bedrock Knowledge Base
6. Bedrock connects to OpenSearch
7. ✅ **SUCCESS**: All indexes exist!
8. Bedrock finds metadata-index, vector-index, suggestions-index
9. Deployment succeeds

---

## How Terraform Builds the Dependency Graph

### Step 1: Parse all resources and their dependencies

```hcl
# Terraform reads all modules and identifies:
# - Implicit dependencies (references)
# - Explicit dependencies (depends_on)

module "opensearch_collection" {
  access_principal_arns = [module.iam.index_bootstrap_lambda_role_arn]
  # ↑ Implicit dependency: opensearch_collection → iam
}

module "index_bootstrap_lambda" {
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  # ↑ Implicit dependency: index_bootstrap_lambda → opensearch_collection
  
  depends_on = [module.opensearch_collection, module.iam]
  # ↑ Explicit dependencies
}

module "bedrock_knowledge_base" {
  depends_on = [
    module.opensearch_collection,
    module.s3_documents,
    module.index_bootstrap_lambda
  ]
  # ↑ Explicit dependencies
}
```

### Step 2: Build a directed graph

```
S3 ← (no dependencies)
  ↓
OpenSearch ← (depends on IAM)
  ↓
IAM ← (depends on S3, OpenSearch)
  ↓
Index Bootstrap Lambda ← (depends on OpenSearch, IAM)
  ↓
Search Lambda ← (depends on OpenSearch, IAM)
Suggestions Lambda ← (depends on OpenSearch, IAM)
Processor Lambda ← (depends on IAM)
Embedding Lambda ← (depends on OpenSearch, IAM)
  ↓
Step Functions ← (depends on Processor, Embedding, IAM)
  ↓
API Gateway ← (depends on Search, Suggestions)
  ↓
Bedrock Knowledge Base ← (depends on OpenSearch, S3, Index Bootstrap Lambda)
```

### Step 3: Execute in order

```
Terraform walks the graph and executes:
1. Resources with no dependencies (S3)
2. Resources whose dependencies are met (OpenSearch, IAM)
3. Resources whose dependencies are met (Index Bootstrap Lambda)
4. Resources whose dependencies are met (Search, Suggestions, Processor, Embedding)
5. Resources whose dependencies are met (Step Functions)
6. Resources whose dependencies are met (API Gateway)
7. Resources whose dependencies are met (Bedrock Knowledge Base)
```

---

## Summary

### Implicit Dependencies (Automatic)
```hcl
opensearch_endpoint = module.opensearch_collection.collection_endpoint
# Terraform automatically knows: this resource depends on opensearch_collection
```

### Explicit Dependencies (Manual)
```hcl
depends_on = [
  module.opensearch_collection,
  module.index_bootstrap_lambda
]
# Terraform explicitly waits for these resources first
```

### Result
✅ OpenSearch collection created first  
✅ Indexes created via Lambda  
✅ Bedrock Knowledge Base created after indexes  
✅ All resources in correct order  
✅ No failures due to missing dependencies  


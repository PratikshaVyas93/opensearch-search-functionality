# Terraform Dependency Management - Quick Summary

## The Question

**How does Terraform know to create OpenSearch collection first, then create indexes, then create Bedrock Knowledge Base?**

## The Answer

Terraform uses **two types of dependencies** to determine the correct creation order:

### 1. **Implicit Dependencies** (Automatic)

When you reference an output from one resource in another, Terraform automatically creates a dependency.

```hcl
# This creates an implicit dependency
opensearch_endpoint = module.opensearch_collection.collection_endpoint
# Terraform knows: "This resource needs opensearch_collection"
# Terraform automatically waits for opensearch_collection first
```

### 2. **Explicit Dependencies** (Manual)

You explicitly tell Terraform which resources must be created first using `depends_on`.

```hcl
depends_on = [
  module.opensearch_collection,
  module.index_bootstrap_lambda
]
# Terraform knows: "Wait for these resources first"
# Terraform waits for all listed resources before creating this one
```

---

## How It Works in Our Project

### Phase 1: Create OpenSearch Collection

```hcl
module "opensearch_collection" {
  source = "./modules/opensearch_collection"
  
  # References IAM roles (implicit dependency)
  access_principal_arns = [
    module.iam.index_bootstrap_lambda_role_arn,
    # ... other roles
  ]
}
```

**Terraform does**:
1. Sees that `opensearch_collection` references `module.iam`
2. Creates `module.iam` first
3. Then creates `opensearch_collection`

---

### Phase 2: Create Index Bootstrap Lambda

```hcl
module "index_bootstrap_lambda" {
  source = "./modules/opensearch_index_bootstrap_lambda"
  
  # Implicit dependency
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  lambda_role_arn = module.iam.index_bootstrap_lambda_role_arn
  
  # Explicit dependency
  depends_on = [
    module.opensearch_collection,
    module.iam
  ]
}
```

**Terraform does**:
1. Sees implicit dependencies (references to opensearch_collection and iam)
2. Sees explicit dependencies (depends_on block)
3. Waits for `opensearch_collection` and `iam` to be created
4. Then creates `index_bootstrap_lambda`
5. Lambda creates indexes (metadata, vector, suggestions)

---

### Phase 3: Create Bedrock Knowledge Base (THE CRITICAL PART)

```hcl
module "bedrock_knowledge_base" {
  source = "./modules/bedrock_knowledge_base"
  
  # Implicit dependencies
  opensearch_collection_arn = module.opensearch_collection.collection_arn
  s3_bucket_arn = module.s3_documents.bucket_arn
  
  # Explicit dependencies (KEY!)
  depends_on = [
    module.opensearch_collection,      # Collection must exist
    module.s3_documents,               # S3 must exist
    module.index_bootstrap_lambda      # Indexes must be created!
  ]
}
```

**Terraform does**:
1. Sees implicit dependencies (references to opensearch_collection and s3_documents)
2. Sees explicit dependencies (depends_on block)
3. **Waits for `index_bootstrap_lambda` to be created**
4. This ensures indexes are created before Bedrock
5. Then creates `bedrock_knowledge_base`
6. Bedrock connects to OpenSearch with existing indexes

---

## Why This Matters

### Without the dependency:
```
❌ Bedrock created before indexes exist
❌ Bedrock tries to connect to empty OpenSearch
❌ Deployment FAILS
```

### With the dependency:
```
✅ Indexes created first
✅ Bedrock created after indexes
✅ Bedrock connects successfully
✅ Deployment SUCCEEDS
```

---

## The Complete Dependency Chain

```
S3 Bucket
    ↓
OpenSearch Collection ← IAM Roles
    ↓
Index Bootstrap Lambda
    ↓
Indexes Created (metadata, vector, suggestions)
    ↓
Search Lambda
Suggestions Lambda
Document Processor Lambda
Embedding Generator Lambda
    ↓
Step Functions
    ↓
API Gateway
    ↓
Bedrock Knowledge Base ← Depends on Index Bootstrap Lambda
```

---

## Key Concepts

### 1. Terraform Builds a Dependency Graph
- Analyzes all resources and their dependencies
- Creates a directed acyclic graph (DAG)
- Executes resources in the correct order

### 2. Implicit Dependencies are Automatic
```hcl
opensearch_endpoint = module.opensearch_collection.collection_endpoint
# Terraform automatically knows: this depends on opensearch_collection
```

### 3. Explicit Dependencies are Manual
```hcl
depends_on = [module.opensearch_collection, module.index_bootstrap_lambda]
# Terraform explicitly waits for these resources first
```

### 4. GitHub Actions Adds Manual Control
- Phase 1: Create core infrastructure
- Invoke Index Bootstrap Lambda manually
- Phase 2: Create dependent infrastructure
- Ensures indexes exist before Bedrock

---

## How to Verify

### View the dependency graph:
```bash
cd infra
terraform graph | dot -Tsvg > graph.svg
```

### Check the plan:
```bash
terraform plan -var="env=dev"
# Shows the order resources will be created
```

### Check the state:
```bash
terraform state list
# Shows all created resources
```

---

## Summary

**Terraform knows the creation order through**:

1. ✅ **Implicit Dependencies** - Automatic when you reference resource outputs
2. ✅ **Explicit Dependencies** - Manual `depends_on` blocks
3. ✅ **Dependency Graph** - Terraform builds and executes in correct order
4. ✅ **GitHub Actions** - Adds manual control for Lambda invocation

**Result**:
- ✅ OpenSearch collection created first
- ✅ Indexes created via Lambda
- ✅ Bedrock Knowledge Base created after indexes
- ✅ All resources in correct order
- ✅ No failures due to missing dependencies

---

## Real-World Example

```hcl
# Step 1: Create OpenSearch Collection
module "opensearch_collection" {
  source = "./modules/opensearch_collection"
  # ... configuration
}

# Step 2: Create Index Bootstrap Lambda
module "index_bootstrap_lambda" {
  source = "./modules/opensearch_index_bootstrap_lambda"
  
  # Implicit dependency: references opensearch_collection
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  
  # Explicit dependency: explicitly waits for opensearch_collection
  depends_on = [module.opensearch_collection]
}

# Step 3: Create Bedrock Knowledge Base
module "bedrock_knowledge_base" {
  source = "./modules/bedrock_knowledge_base"
  
  # Implicit dependency: references opensearch_collection
  opensearch_collection_arn = module.opensearch_collection.collection_arn
  
  # Explicit dependency: explicitly waits for index_bootstrap_lambda
  depends_on = [
    module.opensearch_collection,
    module.index_bootstrap_lambda  # ← KEY: Ensures indexes are created first
  ]
}
```

**Terraform execution order**:
1. Create OpenSearch Collection
2. Create Index Bootstrap Lambda (waits for OpenSearch)
3. Lambda creates indexes
4. Create Bedrock Knowledge Base (waits for Index Bootstrap Lambda)

---

## Files for More Details

- `TERRAFORM_DEPENDENCY_EXPLANATION.md` - Detailed explanation
- `DEPENDENCY_FLOW_DIAGRAM.md` - Visual diagrams
- `DEPENDENCY_CODE_EXAMPLES.md` - Code examples
- `infra/main.tf` - Actual Terraform code


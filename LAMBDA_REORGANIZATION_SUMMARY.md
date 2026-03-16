# Lambda Functions Reorganization Summary

## Overview

All Lambda functions have been moved from `infra/modules/*/lambda_function.py` to a centralized `lambda/` folder at the root level of the project.

## New Structure

```
project-root/
├── lambda/                          # NEW: Centralized Lambda functions
│   ├── search/
│   │   └── index.py                # Search API Lambda
│   ├── suggestions/
│   │   └── index.py                # Suggestions API Lambda
│   ├── processor/
│   │   └── index.py                # Document Processor Lambda
│   ├── embedding/
│   │   └── index.py                # Embedding Generator Lambda
│   └── bootstrap/
│       └── index.py                # Index Bootstrap Lambda
│
├── infra/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars
│   ├── lambda_layers/
│   │   └── opensearch/
│   │       └── python/
│   │           └── requirements.txt
│   └── modules/
│       ├── lambda_search/
│       │   ├── main.tf             # Updated to reference lambda/search/index.py
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── lambda_suggestions/
│       │   ├── main.tf             # Updated to reference lambda/suggestions/index.py
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── lambda_ingestion_processor/
│       │   ├── main.tf             # Updated to reference lambda/processor/index.py
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── lambda_embedding_generator/
│       │   ├── main.tf             # Updated to reference lambda/embedding/index.py
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── opensearch_index_bootstrap_lambda/
│       │   ├── main.tf             # Updated to reference lambda/bootstrap/index.py
│       │   ├── variables.tf
│       │   └── outputs.tf
│       └── ... (other modules)
```

## Changes Made

### 1. Lambda Functions Moved

| Old Location | New Location | Handler |
|---|---|---|
| `infra/modules/lambda_search/lambda_function.py` | `lambda/search/index.py` | `index.handler` |
| `infra/modules/lambda_suggestions/lambda_function.py` | `lambda/suggestions/index.py` | `index.handler` |
| `infra/modules/lambda_ingestion_processor/lambda_function.py` | `lambda/processor/index.py` | `index.handler` |
| `infra/modules/lambda_embedding_generator/lambda_function.py` | `lambda/embedding/index.py` | `index.handler` |
| `infra/modules/opensearch_index_bootstrap_lambda/lambda_function.py` | `lambda/bootstrap/index.py` | `index.handler` |

### 2. Terraform Modules Updated

All Lambda module `main.tf` files have been updated to:

1. **Reference new Lambda location**:
   ```hcl
   # OLD
   source_file = "${path.module}/lambda_function.py"
   
   # NEW
   source_file = "${path.module}/../../lambda/{function-name}/index.py"
   ```

2. **Update handler reference**:
   ```hcl
   # OLD
   handler = "lambda_function.handler"
   
   # NEW
   handler = "index.handler"
   ```

### 3. Updated Terraform Modules

- ✅ `infra/modules/lambda_search/main.tf`
- ✅ `infra/modules/lambda_suggestions/main.tf`
- ✅ `infra/modules/lambda_ingestion_processor/main.tf`
- ✅ `infra/modules/lambda_embedding_generator/main.tf`
- ✅ `infra/modules/opensearch_index_bootstrap_lambda/main.tf`

## Benefits

1. **Centralized Lambda Management**: All Lambda functions in one place for easier maintenance
2. **Cleaner Module Structure**: Terraform modules focus on infrastructure, not code
3. **Better Organization**: Separate concerns between code and infrastructure
4. **Easier Updates**: Modify Lambda code without touching Terraform modules
5. **Reusability**: Lambda functions can be referenced by multiple modules if needed

## File Paths in Terraform

The Terraform modules use relative paths to reference the Lambda functions:

```
infra/modules/lambda_search/main.tf
    ↓
${path.module}/../../lambda/search/index.py
    ↓
lambda/search/index.py
```

This relative path structure ensures the Terraform configuration works regardless of where the project is deployed.

## Deployment

No changes to deployment process. Run Terraform as usual:

```bash
cd infra
terraform init
terraform plan -var="env=dev"
terraform apply -var="env=dev"
```

Terraform will automatically:
1. Archive the Lambda functions from the new `lambda/` folder
2. Create the Lambda functions with the correct handler (`index.handler`)
3. Deploy everything as before

## Verification

After deployment, verify the Lambda functions are created correctly:

```bash
# List Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `opensearch-navco-search`)].FunctionName'

# Check a specific Lambda
aws lambda get-function --function-name dev-opensearch-navco-search-search
```

## Old Lambda Files

All old Lambda function files in `infra/modules/*/lambda_function.py` have been **deleted** to eliminate code redundancy:

- ✅ Deleted: `infra/modules/lambda_search/lambda_function.py`
- ✅ Deleted: `infra/modules/lambda_suggestions/lambda_function.py`
- ✅ Deleted: `infra/modules/lambda_ingestion_processor/lambda_function.py`
- ✅ Deleted: `infra/modules/lambda_embedding_generator/lambda_function.py`
- ✅ Deleted: `infra/modules/opensearch_index_bootstrap_lambda/lambda_function.py`

## Summary

✅ All Lambda functions reorganized to `lambda/` folder
✅ All Terraform modules updated to reference new locations
✅ Handler names updated to `index.handler`
✅ Relative paths configured correctly
✅ Ready for deployment


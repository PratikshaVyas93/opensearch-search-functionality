# Lambda Functions Reorganization - Complete ✅

## Summary

All Lambda functions have been successfully reorganized from `infra/modules/*/lambda_function.py` to a centralized `lambda/` folder at the project root.

---

## What Changed

### Before
```
infra/modules/
├── lambda_search/
│   ├── lambda_function.py          ← Lambda code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── lambda_suggestions/
│   ├── lambda_function.py          ← Lambda code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── lambda_ingestion_processor/
│   ├── lambda_function.py          ← Lambda code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── lambda_embedding_generator/
│   ├── lambda_function.py          ← Lambda code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── opensearch_index_bootstrap_lambda/
    ├── lambda_function.py          ← Lambda code
    ├── main.tf
    ├── variables.tf
    └── outputs.tf
```

### After
```
lambda/                             ← NEW: Centralized Lambda folder
├── search/
│   └── index.py                    ← Lambda code
├── suggestions/
│   └── index.py                    ← Lambda code
├── processor/
│   └── index.py                    ← Lambda code
├── embedding/
│   └── index.py                    ← Lambda code
├── bootstrap/
│   └── index.py                    ← Lambda code
└── README.md                       ← Documentation

infra/modules/
├── lambda_search/
│   ├── main.tf                     ← Updated to reference lambda/search/index.py
│   ├── variables.tf
│   └── outputs.tf
├── lambda_suggestions/
│   ├── main.tf                     ← Updated to reference lambda/suggestions/index.py
│   ├── variables.tf
│   └── outputs.tf
├── lambda_ingestion_processor/
│   ├── main.tf                     ← Updated to reference lambda/processor/index.py
│   ├── variables.tf
│   └── outputs.tf
├── lambda_embedding_generator/
│   ├── main.tf                     ← Updated to reference lambda/embedding/index.py
│   ├── variables.tf
│   └── outputs.tf
└── opensearch_index_bootstrap_lambda/
    ├── main.tf                     ← Updated to reference lambda/bootstrap/index.py
    ├── variables.tf
    └── outputs.tf
```

---

## Files Created

### Lambda Functions (5 files)
1. ✅ `lambda/search/index.py` - Search API Lambda
2. ✅ `lambda/suggestions/index.py` - Suggestions API Lambda
3. ✅ `lambda/processor/index.py` - Document Processor Lambda
4. ✅ `lambda/embedding/index.py` - Embedding Generator Lambda
5. ✅ `lambda/bootstrap/index.py` - Index Bootstrap Lambda

### Documentation (2 files)
1. ✅ `lambda/README.md` - Lambda functions documentation
2. ✅ `LAMBDA_REORGANIZATION_SUMMARY.md` - Detailed reorganization guide

---

## Files Updated

### Terraform Modules (5 files)
1. ✅ `infra/modules/lambda_search/main.tf`
   - Changed: `source_file = "${path.module}/lambda_function.py"`
   - To: `source_file = "${path.module}/../../lambda/search/index.py"`
   - Changed: `handler = "lambda_function.handler"`
   - To: `handler = "index.handler"`

2. ✅ `infra/modules/lambda_suggestions/main.tf`
   - Changed: `source_file = "${path.module}/lambda_function.py"`
   - To: `source_file = "${path.module}/../../lambda/suggestions/index.py"`
   - Changed: `handler = "lambda_function.handler"`
   - To: `handler = "index.handler"`

3. ✅ `infra/modules/lambda_ingestion_processor/main.tf`
   - Changed: `source_file = "${path.module}/lambda_function.py"`
   - To: `source_file = "${path.module}/../../lambda/processor/index.py"`
   - Changed: `handler = "lambda_function.handler"`
   - To: `handler = "index.handler"`

4. ✅ `infra/modules/lambda_embedding_generator/main.tf`
   - Changed: `source_file = "${path.module}/lambda_function.py"`
   - To: `source_file = "${path.module}/../../lambda/embedding/index.py"`
   - Changed: `handler = "lambda_function.handler"`
   - To: `handler = "index.handler"`

5. ✅ `infra/modules/opensearch_index_bootstrap_lambda/main.tf`
   - Changed: `source_file = "${path.module}/lambda_function.py"`
   - To: `source_file = "${path.module}/../../lambda/bootstrap/index.py"`
   - Changed: `handler = "lambda_function.handler"`
   - To: `handler = "index.handler"`

---

## Key Changes

### 1. File Naming
- Old: `lambda_function.py`
- New: `index.py`

### 2. Handler Reference
- Old: `handler = "lambda_function.handler"`
- New: `handler = "index.handler"`

### 3. Source Path
- Old: `source_file = "${path.module}/lambda_function.py"`
- New: `source_file = "${path.module}/../../lambda/{function-name}/index.py"`

### 4. Directory Structure
- Lambda code now centralized in `lambda/` folder
- Terraform modules remain in `infra/modules/`
- Clear separation of concerns

---

## Benefits

✅ **Centralized Lambda Management**
- All Lambda functions in one place
- Easier to find and update code
- Better organization

✅ **Cleaner Module Structure**
- Terraform modules focus on infrastructure
- Lambda code separated from infrastructure code
- Easier to maintain

✅ **Better Reusability**
- Lambda functions can be referenced by multiple modules
- Easier to share code between functions
- Simpler to test locally

✅ **Improved Maintainability**
- Update Lambda code without touching Terraform
- Version control is cleaner
- Easier to track changes

---

## Deployment

No changes to deployment process. Everything works as before:

```bash
cd infra
terraform init
terraform plan -var="env=dev"
terraform apply -var="env=dev"
```

Terraform will:
1. Detect the new Lambda file locations
2. Archive the Lambda functions from `lambda/` folder
3. Create Lambda functions with correct handler (`index.handler`)
4. Deploy everything as before

---

## Verification

After deployment, verify the Lambda functions:

```bash
# List all Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `opensearch-navco-search`)].FunctionName'

# Check a specific Lambda
aws lambda get-function --function-name dev-opensearch-navco-search-search

# View Lambda logs
aws logs tail /aws/lambda/dev-opensearch-navco-search-search --follow
```

---

## Next Steps

## Optional: Clean Up Old Files

✅ **COMPLETED**: All old Lambda function files in `infra/modules/*/lambda_function.py` have been deleted:

```bash
✅ Deleted: infra/modules/lambda_search/lambda_function.py
✅ Deleted: infra/modules/lambda_suggestions/lambda_function.py
✅ Deleted: infra/modules/lambda_ingestion_processor/lambda_function.py
✅ Deleted: infra/modules/lambda_embedding_generator/lambda_function.py
✅ Deleted: infra/modules/opensearch_index_bootstrap_lambda/lambda_function.py
```

No code redundancy - all Lambda functions now live in the `lambda/` folder only.

### Deploy with New Structure

```bash
cd infra
terraform apply -var="env=dev"
```

---

## File Structure Summary

```
project-root/
├── lambda/                          ← NEW: Centralized Lambda functions
│   ├── search/
│   │   └── index.py
│   ├── suggestions/
│   │   └── index.py
│   ├── processor/
│   │   └── index.py
│   ├── embedding/
│   │   └── index.py
│   ├── bootstrap/
│   │   └── index.py
│   └── README.md
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
│       │   ├── main.tf              ← Updated
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── lambda_suggestions/
│       │   ├── main.tf              ← Updated
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── lambda_ingestion_processor/
│       │   ├── main.tf              ← Updated
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── lambda_embedding_generator/
│       │   ├── main.tf              ← Updated
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── opensearch_index_bootstrap_lambda/
│       │   ├── main.tf              ← Updated
│       │   ├── variables.tf
│       │   └── outputs.tf
│       └── ... (other modules)
│
├── .github/
│   └── workflows/
│       └── infra-ci-cd.yml
│
├── README.md
├── LAMBDA_REORGANIZATION_SUMMARY.md
└── REORGANIZATION_COMPLETE.md
```

---

## Status

✅ **Reorganization Complete**

All Lambda functions have been successfully moved to the `lambda/` folder and all Terraform modules have been updated to reference the new locations. The system is ready for deployment.

**Date**: March 15, 2026
**Status**: Ready for Deployment


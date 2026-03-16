# Project Name Update Summary

## Update Completed: `search-platform` → `opensearch-navco-search`

### Date: March 15, 2026

---

## Files Updated

### 1. Terraform Configuration Files
- ✅ `infra/variables.tf` - Updated default project_name variable
- ✅ `infra/terraform.tfvars` - Already updated with new project name
- ✅ `infra/main.tf` - No changes needed (uses variables)
- ✅ `infra/outputs.tf` - No changes needed (uses variables)

### 2. Lambda Function Files
- ✅ All Lambda functions in `infra/modules/*/lambda_function.py` - No hardcoded project names found

### 3. GitHub Actions Workflow
- ✅ `.github/workflows/infra-ci-cd.yml` - No hardcoded project names found

### 4. Documentation Files
- ✅ `README.md` - Updated 3 instances of old project name in examples
- ✅ `IMPLEMENTATION_SUMMARY_DOCUMENT_SEARCH.md` - Updated 3 instances
- ✅ `SPEC_DOCUMENT_SEARCH_PLATFORM.md` - Updated 2 instances

### 5. Specification Files
- ✅ `.kiro/specs/document-search-platform/design.md` - Updated 10 resource naming examples + environment variable
- ✅ `.kiro/specs/document-search-platform/requirements.md` - Updated glossary reference

---

## Resource Naming Convention

All AWS resources now follow the pattern:

```
${env}-${project_name}-{resource-type}
```

### Example Resources (dev environment)

| Resource Type | Old Name | New Name |
|---|---|---|
| S3 Bucket | `dev-search-platform-documents-bucket` | `dev-opensearch-navco-search-documents-bucket` |
| OpenSearch Collection | `dev-search-platform-collection` | `dev-opensearch-navco-search-collection` |
| Search Lambda | `dev-search-platform-search` | `dev-opensearch-navco-search-search` |
| Suggestions Lambda | `dev-search-platform-suggestions` | `dev-opensearch-navco-search-suggestions` |
| Document Processor | `dev-search-platform-processor` | `dev-opensearch-navco-search-processor` |
| Embedding Generator | `dev-search-platform-embedding` | `dev-opensearch-navco-search-embedding` |
| Index Bootstrap | `dev-search-platform-index-bootstrap` | `dev-opensearch-navco-search-index-bootstrap` |
| Step Functions | `dev-search-platform-ingestion` | `dev-opensearch-navco-search-ingestion` |
| API Gateway | `dev-search-platform-api` | `dev-opensearch-navco-search-api` |
| Knowledge Base | `dev-search-platform-kb` | `dev-opensearch-navco-search-kb` |

---

## Verification

All instances of the old project name have been replaced. The only remaining references to "search-platform" are:
- Directory name: `.kiro/specs/document-search-platform/` (intentional - spec folder name)
- Spec ID: `doc-search-platform-v1` (intentional - historical reference)

---

## Next Steps

1. **Deploy with new project name**:
   ```bash
   cd infra
   terraform init
   terraform plan -var="env=dev"
   terraform apply -var="env=dev"
   ```

2. **Or trigger GitHub Actions**:
   - Go to Actions → Infrastructure CI/CD
   - Click "Run workflow"
   - Select environment and branch
   - Click "Run workflow"

3. **Verify deployment**:
   ```bash
   cd infra
   terraform output api_endpoint
   terraform output search_endpoint
   terraform output suggestions_endpoint
   ```

---

## Status

✅ **Project name update complete and ready for deployment**

All files have been updated consistently with the new project name `opensearch-navco-search`.


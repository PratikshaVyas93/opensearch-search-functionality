# RAG Pipeline Documentation Index

## 🚀 Quick Links

### Getting Started
- **[QUICK_START_SECURITY.md](QUICK_START_SECURITY.md)** - 3-step security setup (START HERE)
- **[README.md](README.md)** - Complete RAG pipeline documentation

### Security & Authentication
- **[AWS_AUTHENTICATION_AND_IAM_SETUP.md](AWS_AUTHENTICATION_AND_IAM_SETUP.md)** - Detailed OIDC setup guide
- **[SECURITY_FIXES_SUMMARY.md](SECURITY_FIXES_SUMMARY.md)** - Summary of all security fixes

### Infrastructure
- **[../SECURITY_IMPLEMENTATION_COMPLETE.md](../SECURITY_IMPLEMENTATION_COMPLETE.md)** - Complete implementation summary

---

## 📚 Documentation by Topic

### Authentication & Security

| Document | Purpose | Audience |
|----------|---------|----------|
| QUICK_START_SECURITY.md | 3-step setup guide | Everyone |
| AWS_AUTHENTICATION_AND_IAM_SETUP.md | Detailed OIDC setup | DevOps/Security |
| SECURITY_FIXES_SUMMARY.md | What was fixed | Developers |

### Infrastructure & Architecture

| Document | Purpose | Audience |
|----------|---------|----------|
| README.md | Complete system overview | Everyone |
| ../SECURITY_IMPLEMENTATION_COMPLETE.md | Implementation details | DevOps |

---

## 🔐 Security Setup

### For First-Time Setup

1. **Read**: [QUICK_START_SECURITY.md](QUICK_START_SECURITY.md)
2. **Run**: `bash scripts/setup-github-oidc.sh`
3. **Verify**: Follow verification steps in QUICK_START_SECURITY.md

### For Detailed Understanding

1. **Read**: [AWS_AUTHENTICATION_AND_IAM_SETUP.md](AWS_AUTHENTICATION_AND_IAM_SETUP.md)
2. **Review**: [SECURITY_FIXES_SUMMARY.md](SECURITY_FIXES_SUMMARY.md)
3. **Deploy**: Follow deployment instructions

---

## 🏗️ Infrastructure Overview

### Components

The RAG pipeline consists of 11 AWS components:

1. **S3 Bucket** - Document storage
2. **EventBridge Rule** - S3 event detection
3. **Step Functions** - Ingestion orchestration
4. **Indexer Lambda** - Metadata indexing
5. **OpenSearch Serverless** - Vector search
6. **Bedrock Knowledge Base** - Document chunking & embeddings
7. **API Gateway** - HTTP endpoints
8. **Search Lambda** - Search proxy
9. **Suggestions Lambda** - Autocomplete
10. **RAG Lambda** - LLM answer generation
11. **Bedrock Agent Runtime** - Claude 3 Haiku

See [README.md](README.md) for detailed component descriptions.

---

## 🔧 Deployment

### Prerequisites

- AWS account with appropriate permissions
- GitHub repository
- Terraform installed
- AWS CLI installed

### Deployment Steps

1. **Setup OIDC Authentication**
   ```bash
   bash scripts/setup-github-oidc.sh
   ```

2. **Deploy Infrastructure**
   ```bash
   cd terraform/lambda && terraform apply
   git push origin main
   ```

3. **Verify Deployment**
   - Check GitHub Actions workflow logs
   - Verify resources in AWS Console
   - Check CloudWatch Logs

See [QUICK_START_SECURITY.md](QUICK_START_SECURITY.md) for detailed steps.

---

## 🧪 Testing

### End-to-End Tests

See [README.md](README.md) for complete end-to-end test guide:

1. **Test 1**: Document upload and ingestion
2. **Test 2**: Suggestions endpoint
3. **Test 3**: Search endpoint with answer generation

### Sample Requests

See [README.md](README.md) for sample requests and responses:

- POST /search request and response
- GET /suggestions request and response

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| OIDC authentication fails | See AWS_AUTHENTICATION_AND_IAM_SETUP.md |
| Lambda logs not appearing | Lambda now has CloudWatch Logs permissions |
| Indexer Lambda can't read S3 | Lambda now has S3 read permissions |
| RAG Lambda can't invoke Bedrock | Lambda now has bedrock:InvokeModel permission |

See [QUICK_START_SECURITY.md](QUICK_START_SECURITY.md) for more troubleshooting.

---

## 📋 Checklists

### Pre-Deployment Checklist

- [ ] AWS account ready
- [ ] GitHub repository created
- [ ] Terraform installed
- [ ] AWS CLI installed and configured

### Setup Checklist

- [ ] OIDC provider created
- [ ] GitHub Actions IAM role created
- [ ] Role ARN in GitHub secrets
- [ ] Lambda module updated
- [ ] S3 bucket ARN variable added

### Post-Deployment Checklist

- [ ] Workflow runs successfully
- [ ] Resources created in AWS
- [ ] CloudWatch Logs available
- [ ] End-to-end tests pass

---

## 🔒 Security Features

### Authentication
- ✅ GitHub OIDC (no credentials stored)
- ✅ Temporary credentials (1-hour expiry)
- ✅ Automatic credential rotation
- ✅ Full audit trail

### Permissions
- ✅ Least privilege access
- ✅ All Lambda functions have complete permissions
- ✅ CloudWatch Logs enabled
- ✅ S3 read access for Indexer Lambda
- ✅ Bedrock model invocation for RAG Lambda

---

## 📞 Support

### Documentation

- **Quick answers**: [QUICK_START_SECURITY.md](QUICK_START_SECURITY.md)
- **Detailed setup**: [AWS_AUTHENTICATION_AND_IAM_SETUP.md](AWS_AUTHENTICATION_AND_IAM_SETUP.md)
- **What was fixed**: [SECURITY_FIXES_SUMMARY.md](SECURITY_FIXES_SUMMARY.md)
- **System overview**: [README.md](README.md)

### External Resources

- [GitHub OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [AWS IAM OIDC Providers](https://docs.aws.amazon.com/IAM/latest/userguide/id_roles_providers_oidc.html)
- [AWS Lambda Execution Roles](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)

---

## 📊 File Structure

```
docs/
├── INDEX.md (this file)
├── README.md (complete system documentation)
├── QUICK_START_SECURITY.md (3-step setup)
├── AWS_AUTHENTICATION_AND_IAM_SETUP.md (detailed OIDC setup)
└── SECURITY_FIXES_SUMMARY.md (what was fixed)

terraform/
├── backend/ (state management)
├── s3/ (document storage)
├── opensearch/ (vector search)
├── bedrock/ (knowledge base)
├── eventbridge/ (ingestion orchestration)
├── lambda/ (Lambda functions with updated permissions)
├── apigateway/ (HTTP API)
└── github-oidc/ (GitHub Actions authentication)

scripts/
├── create_indexes.py (OpenSearch index creation)
├── requirements.txt (Python dependencies)
└── setup-github-oidc.sh (automated OIDC setup)

.github/workflows/
└── deploy.yml (GitHub Actions deployment workflow)
```

---

## ✅ Status

- **Infrastructure**: ✅ Complete
- **Security**: ✅ Complete
- **Documentation**: ✅ Complete
- **Testing**: ✅ Ready
- **Deployment**: ✅ Ready

---

## 🎯 Next Steps

1. **Read** [QUICK_START_SECURITY.md](QUICK_START_SECURITY.md)
2. **Run** `bash scripts/setup-github-oidc.sh`
3. **Deploy** infrastructure
4. **Test** end-to-end
5. **Monitor** CloudWatch Logs

---

**Last Updated**: 2026-03-14
**Status**: ✅ Production-Ready
**Security Level**: 🔒 Enterprise-Grade

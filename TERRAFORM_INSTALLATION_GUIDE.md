# Terraform Installation Guide

## Overview

Terraform is not required to understand how the infrastructure works. However, if you want to deploy the infrastructure locally or view the dependency graph, you'll need to install it.

---

## Installation Options

### Option 1: Using Homebrew (Recommended for macOS)

```bash
# Install Terraform
brew install terraform

# Verify installation
terraform version
```

### Option 2: Using tfenv (Terraform Version Manager)

```bash
# Install tfenv
brew install tfenv

# Install Terraform
tfenv install latest

# Set as default
tfenv use latest

# Verify installation
terraform version
```

### Option 3: Manual Installation

1. Download from: https://www.terraform.io/downloads.html
2. Extract the binary
3. Add to PATH

```bash
# Example for macOS
cd ~/Downloads
unzip terraform_*.zip
sudo mv terraform /usr/local/bin/
terraform version
```

---

## Verify Installation

```bash
terraform version
# Output: Terraform v1.5.0 (or similar)
```

---

## AWS CLI Installation (Optional)

If you want to deploy to AWS, you'll also need AWS CLI:

```bash
# Install AWS CLI
brew install awscli

# Verify installation
aws --version

# Configure AWS credentials
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region (us-east-1)
# Enter default output format (json)
```

---

## Graphviz Installation (Optional)

If you want to visualize the dependency graph:

```bash
# Install Graphviz
brew install graphviz

# Verify installation
dot -V
```

---

## Using Terraform Locally

### Step 1: Initialize Terraform

```bash
cd infra
terraform init
```

### Step 2: View the Plan

```bash
terraform plan -var="env=dev"
```

### Step 3: View the Dependency Graph

```bash
# Generate graph
terraform graph | dot -Tsvg > graph.svg

# Open in browser
open graph.svg
```

### Step 4: Apply the Configuration

```bash
terraform apply -var="env=dev"
```

---

## Important Notes

### You Don't Need Terraform Installed To:
- ✅ Understand how the infrastructure works
- ✅ Read the Terraform code
- ✅ Understand dependencies
- ✅ Deploy via GitHub Actions

### You Need Terraform Installed To:
- ✅ Deploy locally
- ✅ Test the configuration
- ✅ View the dependency graph
- ✅ Manage the infrastructure locally

---

## Recommended Workflow

### For Development:
1. Install Terraform locally
2. Make changes to Terraform code
3. Run `terraform plan` to preview changes
4. Commit and push to GitHub
5. GitHub Actions deploys to AWS

### For Production:
1. Use GitHub Actions for deployment
2. No need to install Terraform locally
3. GitHub Actions handles all deployment

---

## Troubleshooting

### Command not found: terraform

```bash
# Check if Terraform is in PATH
which terraform

# If not found, reinstall:
brew install terraform

# Or add to PATH manually:
export PATH="/usr/local/bin:$PATH"
```

### Command not found: dot

```bash
# Install Graphviz
brew install graphviz

# Verify
dot -V
```

### AWS credentials not configured

```bash
# Configure AWS
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

---

## Next Steps

### If You Want to Deploy Locally:
1. Install Terraform: `brew install terraform`
2. Install AWS CLI: `brew install awscli`
3. Configure AWS: `aws configure`
4. Deploy: `cd infra && terraform apply -var="env=dev"`

### If You Want to Use GitHub Actions:
1. No installation needed
2. Push code to GitHub
3. GitHub Actions handles deployment
4. Check GitHub Actions logs for status

---

## Summary

- **Terraform**: Not required to understand the infrastructure, but useful for local deployment
- **AWS CLI**: Not required if using GitHub Actions
- **Graphviz**: Optional, only needed to visualize dependency graph
- **GitHub Actions**: Recommended for production deployment (no local installation needed)


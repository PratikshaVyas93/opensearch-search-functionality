#!/bin/bash
# Setup GitHub OIDC provider for AWS authentication
# This script creates the OIDC provider and IAM role for GitHub Actions

set -e

echo "🔐 Setting up GitHub OIDC for AWS authentication..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install it first."
    exit 1
fi

# Get GitHub organization and repository
read -p "Enter GitHub organization name: " GITHUB_ORG
read -p "Enter GitHub repository name: " GITHUB_REPO
read -p "Enter environment (dev/staging/prod) [dev]: " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-dev}

echo ""
echo "📋 Configuration:"
echo "  GitHub Org: $GITHUB_ORG"
echo "  GitHub Repo: $GITHUB_REPO"
echo "  Environment: $ENVIRONMENT"
echo ""

# Step 1: Create OIDC provider
echo "Step 1️⃣  Creating OIDC provider..."
PROVIDER_ARN=$(aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?contains(OpenIDConnectProviderArn, 'token.actions.githubusercontent.com')].OpenIDConnectProviderArn" --output text)

if [ -z "$PROVIDER_ARN" ]; then
    echo "  Creating new OIDC provider..."
    PROVIDER_ARN=$(aws iam create-open-id-connect-provider \
        --url https://token.actions.githubusercontent.com \
        --client-id-list sts.amazonaws.com \
        --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
        --query 'OpenIDConnectProviderArn' \
        --output text)
    echo "  ✅ OIDC provider created: $PROVIDER_ARN"
else
    echo "  ✅ OIDC provider already exists: $PROVIDER_ARN"
fi

echo ""
echo "Step 2️⃣  Creating GitHub Actions IAM role..."

# Step 2: Deploy Terraform module
cd terraform/github-oidc

terraform init

terraform apply -auto-approve \
    -var="github_org=$GITHUB_ORG" \
    -var="github_repo=$GITHUB_REPO" \
    -var="environment=$ENVIRONMENT"

ROLE_ARN=$(terraform output -raw github_actions_role_arn)
ROLE_NAME=$(terraform output -raw github_actions_role_name)

echo "  ✅ IAM role created: $ROLE_NAME"
echo "  ✅ Role ARN: $ROLE_ARN"

cd ../..

echo ""
echo "Step 3️⃣  Adding role ARN to GitHub secrets..."
echo ""
echo "📝 Please add the following to your GitHub repository secrets:"
echo ""
echo "  Secret Name: AWS_ROLE_ARN"
echo "  Secret Value: $ROLE_ARN"
echo ""
echo "Steps:"
echo "  1. Go to: https://github.com/$GITHUB_ORG/$GITHUB_REPO/settings/secrets/actions"
echo "  2. Click 'New repository secret'"
echo "  3. Name: AWS_ROLE_ARN"
echo "  4. Value: $ROLE_ARN"
echo "  5. Click 'Add secret'"
echo ""

echo "✅ GitHub OIDC setup complete!"
echo ""
echo "🚀 Next steps:"
echo "  1. Add the AWS_ROLE_ARN secret to GitHub"
echo "  2. Push your code to trigger the workflow"
echo "  3. The workflow will authenticate using OIDC without storing credentials"
echo ""
echo "📚 For more information, see: docs/AWS_AUTHENTICATION_AND_IAM_SETUP.md"

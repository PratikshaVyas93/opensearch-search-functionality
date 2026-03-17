# Terraform Variables - Document Search Platform
# Default values for development environment

env              = "dev"
project_name     = "opensearch-navco-search"
region           = "us-east-1"
bedrock_model_id = "amazon.titan-embed-text-v1"

# Your AWS console IAM user ARN for OpenSearch dashboard access
# Go to AWS Console → top-right corner → click your username → copy ARN
# OR go to IAM → Users → your username → copy ARN
# Example: "arn:aws:iam::123456789012:user/your-username"
dashboard_user_arns = [
  "arn:aws:iam::YOUR_ACCOUNT_ID:user/YOUR_USERNAME"
]

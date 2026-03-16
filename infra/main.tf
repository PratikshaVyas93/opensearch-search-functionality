# Root Terraform Module - Document Search Platform
# Orchestrates all infrastructure components in correct dependency order

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "dev-opensearch-navco-search-tfstate"
    key            = "infra/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region
}

# ============================================================================
# Lambda Layer for OpenSearch Dependencies (Optional)
# ============================================================================

# Check if layer directory exists and has content
data "archive_file" "opensearch_layer" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_layers/opensearch"
  output_path = "${path.module}/.terraform/opensearch_layer.zip"
}

resource "aws_lambda_layer_version" "opensearch" {
  filename            = data.archive_file.opensearch_layer.output_path
  layer_name          = "${var.env}-${var.project_name}-opensearch-layer"
  compatible_runtimes = ["python3.13"]
  source_code_hash    = data.archive_file.opensearch_layer.output_base64sha256
}

# ============================================================================
# Phase 1: Infrastructure Foundation
# ============================================================================

module "s3_documents" {
  source = "./modules/s3_documents"

  bucket_name  = "${var.env}-${var.project_name}-documents-bucket"
  env          = var.env
  project_name = var.project_name
}

module "opensearch_collection" {
  source = "./modules/opensearch_collection"

  collection_name = "${var.env}-navco-search"
  env             = var.env
  project_name    = var.project_name

  # Placeholder ARNs - will be updated after IAM module creation
  access_principal_arns = [
    "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.env}-${var.project_name}-index-bootstrap-role",
    "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.env}-${var.project_name}-search-role",
    "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.env}-${var.project_name}-suggestions-role",
    "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.env}-${var.project_name}-processor-role",
    "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.env}-${var.project_name}-embedding-role"
  ]
}

data "aws_caller_identity" "current" {}

# ============================================================================
# Phase 2: IAM Roles and Policies
# ============================================================================

module "iam" {
  source = "./modules/iam"

  env                            = var.env
  project_name                   = var.project_name
  region                         = var.region
  opensearch_collection_arn      = module.opensearch_collection.collection_arn
  s3_bucket_arn                  = module.s3_documents.bucket_arn
  document_processor_lambda_arn  = ""
  embedding_generator_lambda_arn = ""

  depends_on = [
    module.opensearch_collection,
    module.s3_documents
  ]
}

# ============================================================================
# Phase 3: Lambda Functions
# ============================================================================

module "src_bootstrap" {
  source = "./modules/src_bootstrap"

  function_name        = "${var.env}-${var.project_name}-index-bootstrap"
  lambda_role_arn      = module.iam.index_bootstrap_lambda_role_arn
  opensearch_endpoint  = module.opensearch_collection.collection_endpoint
  region               = var.region
  env                  = var.env
  project_name         = var.project_name
  opensearch_layer_arn = aws_lambda_layer_version.opensearch.arn

  depends_on = [
    module.iam,
    module.opensearch_collection
  ]
}

module "src_search" {
  source = "./modules/src_search"

  function_name        = "${var.env}-${var.project_name}-search"
  lambda_role_arn      = module.iam.search_lambda_role_arn
  opensearch_endpoint  = module.opensearch_collection.collection_endpoint
  region               = var.region
  env                  = var.env
  project_name         = var.project_name
  opensearch_layer_arn = aws_lambda_layer_version.opensearch.arn

  depends_on = [
    module.iam,
    module.opensearch_collection
  ]
}

module "src_suggestions" {
  source = "./modules/src_suggestions"

  function_name        = "${var.env}-${var.project_name}-suggestions"
  lambda_role_arn      = module.iam.suggestions_lambda_role_arn
  opensearch_endpoint  = module.opensearch_collection.collection_endpoint
  region               = var.region
  env                  = var.env
  project_name         = var.project_name
  opensearch_layer_arn = aws_lambda_layer_version.opensearch.arn

  depends_on = [
    module.iam,
    module.opensearch_collection
  ]
}

module "src_processor" {
  source = "./modules/src_processor"

  function_name   = "${var.env}-${var.project_name}-processor"
  lambda_role_arn = module.iam.document_processor_lambda_role_arn
  env             = var.env
  project_name    = var.project_name

  depends_on = [
    module.iam
  ]
}

module "src_embedding" {
  source = "./modules/src_embedding"

  function_name        = "${var.env}-${var.project_name}-embedding"
  lambda_role_arn      = module.iam.embedding_generator_lambda_role_arn
  opensearch_endpoint  = module.opensearch_collection.collection_endpoint
  region               = var.region
  env                  = var.env
  project_name         = var.project_name
  opensearch_layer_arn = aws_lambda_layer_version.opensearch.arn
  bedrock_model_id     = var.bedrock_model_id

  depends_on = [
    module.iam,
    module.opensearch_collection
  ]
}

# ============================================================================
# Phase 4: Step Functions & EventBridge
# ============================================================================

resource "aws_iam_role" "eventbridge_role" {
  name = "${var.env}-${var.project_name}-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "${var.env}-${var.project_name}-eventbridge-role"
    Environment = var.env
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy" "eventbridge_policy" {
  name   = "${var.env}-${var.project_name}-eventbridge-policy"
  role   = aws_iam_role.eventbridge_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["states:StartExecution"]
        Resource = "*"
      }
    ]
  })
}

module "step_functions_ingestion" {
  source = "./modules/step_functions_ingestion"

  state_machine_name             = "${var.env}-${var.project_name}-ingestion"
  step_functions_role_arn        = module.iam.step_functions_ingestion_role_arn
  document_processor_lambda_arn  = module.src_processor.lambda_arn
  embedding_generator_lambda_arn = module.src_embedding.lambda_arn
  s3_bucket_name                 = module.s3_documents.bucket_name
  eventbridge_role_arn           = aws_iam_role.eventbridge_role.arn
  env                            = var.env
  project_name                   = var.project_name

  depends_on = [
    module.src_processor,
    module.src_embedding,
    module.iam
  ]
}

# ============================================================================
# Phase 5: API Gateway
# ============================================================================

module "api_gateway" {
  source = "./modules/api_gateway"

  api_name                         = "${var.env}-${var.project_name}-api"
  env                              = var.env
  project_name                     = var.project_name
  search_lambda_invoke_arn         = module.src_search.lambda_invoke_arn
  search_lambda_function_name      = module.src_search.lambda_function_name
  suggestions_lambda_invoke_arn    = module.src_suggestions.lambda_invoke_arn
  suggestions_lambda_function_name = module.src_suggestions.lambda_function_name

  depends_on = [
    module.src_search,
    module.src_suggestions
  ]
}

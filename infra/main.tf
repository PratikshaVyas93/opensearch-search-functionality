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
}

provider "aws" {
  region = var.region
}

# ============================================================================
# Lambda Layer for OpenSearch Dependencies
# ============================================================================

# Create a Lambda layer with opensearchpy and requests-aws4auth
data "archive_file" "opensearch_layer" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_layers/opensearch"
  output_path = "${path.module}/.terraform/opensearch_layer.zip"
}

resource "aws_lambda_layer_version" "opensearch" {
  filename            = data.archive_file.opensearch_layer.output_path
  layer_name          = "${var.env}-${var.project_name}-opensearch-layer"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = data.archive_file.opensearch_layer.output_base64sha256
}

# ============================================================================
# Phase 1: Infrastructure Foundation
# ============================================================================

# S3 Documents Bucket
module "s3_documents" {
  source = "./modules/s3_documents"

  bucket_name = "${var.env}-${var.project_name}-documents-bucket"
  env         = var.env
  project_name = var.project_name
}

# OpenSearch Collection
module "opensearch_collection" {
  source = "./modules/opensearch_collection"

  collection_name = "${var.env}-${var.project_name}-collection"
  env             = var.env
  project_name    = var.project_name

  # Allow all Lambda roles to access the collection
  access_principal_arns = [
    module.iam.index_bootstrap_lambda_role_arn,
    module.iam.search_lambda_role_arn,
    module.iam.suggestions_lambda_role_arn,
    module.iam.document_processor_lambda_role_arn,
    module.iam.embedding_generator_lambda_role_arn
  ]
}

# IAM Roles and Policies
module "iam" {
  source = "./modules/iam"

  env                              = var.env
  project_name                     = var.project_name
  region                           = var.region
  opensearch_collection_arn        = module.opensearch_collection.collection_arn
  s3_bucket_arn                    = module.s3_documents.bucket_arn
  document_processor_lambda_arn    = ""  # Will be set after Lambda creation
  embedding_generator_lambda_arn   = ""  # Will be set after Lambda creation
}

# ============================================================================
# Phase 2: Index Bootstrap Lambda
# ============================================================================

module "src_bootstrap" {
  source = "./modules/src_bootstrap"

  function_name       = "${var.env}-${var.project_name}-index-bootstrap"
  lambda_role_arn     = module.iam.index_bootstrap_lambda_role_arn
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  region              = var.region
  env                 = var.env
  project_name        = var.project_name
  opensearch_layer_arn = aws_lambda_layer_version.opensearch.arn

  depends_on = [
    module.opensearch_collection,
    module.iam
  ]
}

  function_name       = "${var.env}-${var.project_name}-search"
  lambda_role_arn     = module.iam.search_lambda_role_arn
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  region              = var.region
  env                 = var.env
  project_name        = var.project_name
  opensearch_layer_arn = aws_lambda_layer_version.opensearch.arn

  depends_on = [
    module.opensearch_collection,
    module.iam
  ]
}

module "suggestions_lambda" {
  source = "./modules/lambda_suggestions"

  function_name       = "${var.env}-${var.project_name}-suggestions"
  lambda_role_arn     = module.iam.suggestions_lambda_role_arn
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  region              = var.region
  env                 = var.env
  project_name        = var.project_name
  opensearch_layer_arn = aws_lambda_layer_version.opensearch.arn

  depends_on = [
    module.opensearch_collection,
    module.iam
  ]
}

# ============================================================================
# Phase 4: Ingestion Pipeline
# ============================================================================

module "document_processor_lambda" {
  source = "./modules/lambda_ingestion_processor"

  function_name   = "${var.env}-${var.project_name}-processor"
  lambda_role_arn = module.iam.document_processor_lambda_role_arn
  env             = var.env
  project_name    = var.project_name

  depends_on = [
    module.iam
  ]
}

module "embedding_generator_lambda" {
  source = "./modules/lambda_embedding_generator"

  function_name       = "${var.env}-${var.project_name}-embedding"
  lambda_role_arn     = module.iam.embedding_generator_lambda_role_arn
  opensearch_endpoint = module.opensearch_collection.collection_endpoint
  region              = var.region
  env                 = var.env
  project_name        = var.project_name
  opensearch_layer_arn = aws_lambda_layer_version.opensearch.arn
  bedrock_model_id    = var.bedrock_model_id

  depends_on = [
    module.opensearch_collection,
    module.iam
  ]
}

# EventBridge role for Step Functions
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
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = "*"
      }
    ]
  })
}

module "step_functions_ingestion" {
  source = "./modules/step_functions_ingestion"

  state_machine_name                = "${var.env}-${var.project_name}-ingestion"
  step_functions_role_arn           = module.iam.step_functions_ingestion_role_arn
  document_processor_lambda_arn     = module.document_processor_lambda.lambda_arn
  embedding_generator_lambda_arn    = module.embedding_generator_lambda.lambda_arn
  s3_bucket_name                    = module.s3_documents.bucket_name
  eventbridge_role_arn              = aws_iam_role.eventbridge_role.arn
  env                               = var.env
  project_name                      = var.project_name

  depends_on = [
    module.document_processor_lambda,
    module.embedding_generator_lambda,
    module.iam
  ]
}

# ============================================================================
# Phase 5: API & Bedrock
# ============================================================================

module "api_gateway" {
  source = "./modules/api_gateway"

  api_name                          = "${var.env}-${var.project_name}-api"
  env                               = var.env
  project_name                      = var.project_name
  search_lambda_invoke_arn          = module.search_lambda.lambda_invoke_arn
  search_lambda_function_name       = module.search_lambda.lambda_function_name
  suggestions_lambda_invoke_arn     = module.suggestions_lambda.lambda_invoke_arn
  suggestions_lambda_function_name  = module.suggestions_lambda.lambda_function_name

  depends_on = [
    module.search_lambda,
    module.suggestions_lambda
  ]
}

module "bedrock_knowledge_base" {
  source = "./modules/bedrock_knowledge_base"

  knowledge_base_name       = "${var.env}-${var.project_name}-kb"
  env                       = var.env
  project_name              = var.project_name
  opensearch_collection_arn = module.opensearch_collection.collection_arn
  s3_bucket_arn             = module.s3_documents.bucket_arn

  depends_on = [
    module.opensearch_collection,
    module.s3_documents,
    module.index_bootstrap_lambda
  ]
}

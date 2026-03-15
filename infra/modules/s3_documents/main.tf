# S3 Documents Module - Bucket for document storage and ingestion
# Provides S3 bucket with versioning, public access blocking, and event notifications

resource "aws_s3_bucket" "documents" {
  bucket = var.bucket_name

  tags = {
    Name        = var.bucket_name
    Environment = var.env
    Project     = var.project_name
  }
}

# Enable versioning for document history tracking
resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Block all public access to the bucket
resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Configure S3 event notification to trigger Step Functions
# This sends S3:ObjectCreated events to EventBridge
resource "aws_s3_bucket_notification" "documents" {
  bucket      = aws_s3_bucket.documents.id
  eventbridge = true
}

output "bucket_name" {
  description = "Name of the S3 document storage bucket"
  value       = aws_s3_bucket.documents.id
}

output "bucket_arn" {
  description = "ARN of the S3 document storage bucket"
  value       = aws_s3_bucket.documents.arn
}

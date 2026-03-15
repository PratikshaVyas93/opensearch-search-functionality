"""
Document Processor Lambda Function
Reads documents from S3, extracts text and metadata
"""

import json
import logging
import os
import boto3
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3_client = boto3.client('s3')


def extract_text_from_document(bucket, key):
    """
    Extract text content from document
    Supports plain text files
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        logger.info(f"Extracted text from {key}, length: {len(content)}")
        return content
        
    except Exception as e:
        logger.error(f"Error extracting text from {key}: {str(e)}")
        raise


def extract_metadata(bucket, key, content):
    """
    Extract metadata from document
    Returns title, size, upload_date
    """
    try:
        # Get object metadata
        response = s3_client.head_object(Bucket=bucket, Key=key)
        
        # Extract metadata
        metadata = {
            'document_id': key,
            'title': key.split('/')[-1],  # Use filename as title
            'size': response['ContentLength'],
            'upload_date': response['LastModified'].isoformat(),
            'content_length': len(content),
            'source': f"s3://{bucket}/{key}"
        }
        
        logger.info(f"Extracted metadata for {key}: {json.dumps(metadata)}")
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting metadata for {key}: {str(e)}")
        raise


def handler(event, context):
    """
    Lambda handler for document processing
    Receives S3 object information from Step Functions
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract S3 information from event
        bucket = event.get('bucket')
        key = event.get('key')
        
        if not bucket or not key:
            logger.error("Missing bucket or key in event")
            return {
                'statusCode': 400,
                'error': 'Missing bucket or key'
            }
        
        logger.info(f"Processing document: s3://{bucket}/{key}")
        
        # Extract text content
        content = extract_text_from_document(bucket, key)
        
        # Extract metadata
        metadata = extract_metadata(bucket, key, content)
        
        # Prepare output for next step (Embedding Generator)
        result = {
            'bucket': bucket,
            'key': key,
            'content': content,
            'metadata': metadata,
            'processed_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Document processing completed for {key}")
        
        return {
            'statusCode': 200,
            'body': result
        }
        
    except Exception as e:
        logger.error(f"Error in document processor: {str(e)}")
        return {
            'statusCode': 503,
            'error': 'Document processing failed',
            'details': str(e)
        }

import json
import os
import boto3
import logging
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
s3_client = boto3.client('s3')
region = os.environ.get('AWS_REGION', 'us-east-1')

# AWS credentials for OpenSearch
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'aoss', session_token=credentials.token)

# Initialize OpenSearch client
opensearch_client = OpenSearch(
    hosts=[{'host': opensearch_endpoint, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=30
)


def extract_metadata_from_s3(bucket, key):
    """
    Extract metadata from S3 object.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
    
    Returns:
        Dictionary with metadata
    """
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        
        metadata = {
            'doc_id': key.replace('/', '-'),
            's3_key': key,
            'title': key.split('/')[-1],
            'uploaded_at': response['LastModified'].isoformat(),
            'tags': response.get('Metadata', {}).get('tags', '').split(',') if response.get('Metadata', {}).get('tags') else []
        }
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting metadata from S3: {str(e)}")
        raise


def index_metadata(metadata):
    """
    Index document metadata into metadata-index.
    
    Args:
        metadata: Dictionary with document metadata
    
    Returns:
        OpenSearch response
    """
    try:
        doc_id = metadata['doc_id']
        response = opensearch_client.index(
            index='metadata-index',
            id=doc_id,
            body=metadata
        )
        logger.info(f"Indexed metadata for {doc_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error indexing metadata: {str(e)}")
        raise


def index_suggestions(metadata):
    """
    Index suggestions based on document metadata.
    
    Args:
        metadata: Dictionary with document metadata
    
    Returns:
        OpenSearch response
    """
    try:
        suggestions = []
        
        # Create suggestions from title
        title = metadata.get('title', '')
        if title:
            suggestions.append({
                'suggestion_id': f"{metadata['doc_id']}-title",
                'text': title,
                'doc_id': metadata['doc_id'],
                'weight': 10
            })
        
        # Create suggestions from tags
        tags = metadata.get('tags', [])
        for tag in tags:
            if tag.strip():
                suggestions.append({
                    'suggestion_id': f"{metadata['doc_id']}-tag-{tag}",
                    'text': tag.strip(),
                    'doc_id': metadata['doc_id'],
                    'weight': 5
                })
        
        # Index all suggestions
        for suggestion in suggestions:
            response = opensearch_client.index(
                index='suggestions-index',
                id=suggestion['suggestion_id'],
                body=suggestion
            )
            logger.info(f"Indexed suggestion: {suggestion['suggestion_id']}")
        
        return {'indexed_suggestions': len(suggestions)}
        
    except Exception as e:
        logger.error(f"Error indexing suggestions: {str(e)}")
        raise


def lambda_handler(event, context):
    """
    Main Lambda handler for document indexing.
    
    Expected event format (from Step Functions):
    {
        "detail": {
            "bucket": {
                "name": "bucket-name"
            },
            "object": {
                "key": "document-key"
            }
        }
    }
    """
    try:
        # Parse S3 event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Handle both direct S3 events and Step Functions events
        if 'detail' in event:
            # Step Functions event
            bucket = event['detail']['bucket']['name']
            key = event['detail']['object']['key']
        elif 'Records' in event:
            # Direct S3 event
            record = event['Records'][0]
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
        else:
            raise ValueError("Invalid event format")
        
        logger.info(f"Processing document: s3://{bucket}/{key}")
        
        # Extract metadata
        metadata = extract_metadata_from_s3(bucket, key)
        logger.info(f"Extracted metadata: {json.dumps(metadata)}")
        
        # Index metadata
        metadata_response = index_metadata(metadata)
        logger.info(f"Metadata indexing response: {json.dumps(metadata_response, default=str)}")
        
        # Index suggestions
        suggestions_response = index_suggestions(metadata)
        logger.info(f"Suggestions indexing response: {json.dumps(suggestions_response)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document indexed successfully',
                'doc_id': metadata['doc_id'],
                'metadata_response': metadata_response,
                'suggestions_response': suggestions_response
            }, default=str)
        }
        
    except Exception as e:
        logger.error(f"Indexer Lambda error: {str(e)}")
        raise Exception(f"Failed to index document: {str(e)}")

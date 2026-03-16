"""
Embedding Generator Lambda Function
Generates embeddings using Bedrock Titan model and indexes documents
"""

import json
import logging
import os
import time
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'amazon.titan-embed-text-v1')

# Use boto3 session for region - Lambda sets AWS_REGION automatically
session = boto3.Session()
AWS_REGION = session.region_name or 'us-east-1'

# Initialize AWS clients
bedrock_client = boto3.client('bedrock-runtime', region_name=AWS_REGION)

# Initialize AWS credentials for OpenSearch
credentials = session.get_credentials()
auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    AWS_REGION,
    'aoss',
    session_token=credentials.token
)

# Initialize OpenSearch client
opensearch_client = OpenSearch(
    hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=30
)


def get_embedding_with_retry(text, max_retries=3):
    """
    Get embedding from Bedrock with retry logic for throttling
    """
    for attempt in range(max_retries):
        try:
            response = bedrock_client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'inputText': text
                })
            )
            
            result = json.loads(response['body'].read())
            embedding = result.get('embedding', [])
            logger.info(f"Generated embedding of dimension {len(embedding)}")
            return embedding
            
        except bedrock_client.exceptions.ThrottlingException as e:
            wait_time = 2 ** attempt  # Exponential backoff
            logger.warning(f"Bedrock throttled, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to get embedding after {max_retries} retries")
                raise
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise


def index_metadata(metadata):
    """Index document metadata in metadata-index"""
    try:
        doc_id = metadata['document_id']
        opensearch_client.index(
            index='metadata-index',
            id=doc_id,
            body=metadata
        )
        logger.info(f"Indexed metadata for {doc_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error indexing metadata: {str(e)}")
        raise


def index_vector(document_id, text, embedding):
    """Index document vector in vector-index"""
    try:
        doc_body = {
            'document_id': document_id,
            'chunk_id': f"{document_id}_chunk_0",
            'text': text,
            'embedding': embedding
        }
        
        opensearch_client.index(
            index='vector-index',
            id=f"{document_id}_0",
            body=doc_body
        )
        logger.info(f"Indexed vector for {document_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error indexing vector: {str(e)}")
        raise


def generate_suggestions(title, content):
    """Generate suggestions from document title and content"""
    suggestions = []
    
    # Add title as suggestion
    if title:
        suggestions.append({
            'suggestion': title,
            'weight': 10
        })
    
    # Add first few words as suggestions
    words = content.split()[:20]
    for i, word in enumerate(words):
        if len(word) > 3:  # Only words longer than 3 chars
            suggestions.append({
                'suggestion': word,
                'weight': max(1, 10 - i)
            })
    
    return suggestions


def index_suggestions(document_id, suggestions):
    """Index suggestions in suggestions-index"""
    try:
        for i, suggestion in enumerate(suggestions):
            doc_body = {
                'suggestion': suggestion['suggestion'],
                'weight': suggestion['weight'],
                'document_id': document_id
            }
            
            opensearch_client.index(
                index='suggestions-index',
                id=f"{document_id}_suggestion_{i}",
                body=doc_body
            )
        
        logger.info(f"Indexed {len(suggestions)} suggestions for {document_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error indexing suggestions: {str(e)}")
        raise


def handler(event, context):
    """
    Lambda handler for embedding generation
    Receives processed document from Document Processor Lambda
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract data from event
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        content = body.get('content', '')
        metadata = body.get('metadata', {})
        
        if not content or not metadata:
            logger.error("Missing content or metadata in event")
            return {
                'statusCode': 400,
                'error': 'Missing content or metadata'
            }
        
        document_id = metadata.get('document_id')
        logger.info(f"Generating embeddings for {document_id}")
        
        # Generate embedding
        embedding = get_embedding_with_retry(content)
        
        # Index metadata
        index_metadata(metadata)
        
        # Index vector
        index_vector(document_id, content, embedding)
        
        # Generate and index suggestions
        title = metadata.get('title', '')
        suggestions = generate_suggestions(title, content)
        index_suggestions(document_id, suggestions)
        
        logger.info(f"Embedding generation completed for {document_id}")
        
        return {
            'statusCode': 200,
            'body': {
                'document_id': document_id,
                'embedding_dimension': len(embedding),
                'suggestions_count': len(suggestions),
                'indexed': True
            }
        }
        
    except Exception as e:
        logger.error(f"Error in embedding generator: {str(e)}")
        return {
            'statusCode': 503,
            'error': 'Embedding generation failed',
            'details': str(e)
        }

"""
Index Bootstrap Lambda Function
Creates OpenSearch indexes for metadata, vectors, and suggestions
"""

import json
import logging
import os
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT', '')

# Strip https:// prefix if present — the OpenSearch client constructs the URL itself
if OPENSEARCH_ENDPOINT.startswith('https://'):
    OPENSEARCH_ENDPOINT = OPENSEARCH_ENDPOINT[len('https://'):]
elif OPENSEARCH_ENDPOINT.startswith('http://'):
    OPENSEARCH_ENDPOINT = OPENSEARCH_ENDPOINT[len('http://'):]

# Use boto3 session for region - Lambda sets AWS_REGION automatically
session = boto3.Session()
AWS_REGION = session.region_name or 'us-east-1'

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
client = OpenSearch(
    hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=30
)


def create_metadata_index():
    """Create metadata index for document information"""
    index_name = 'metadata-index'
    
    try:
        # Check if index already exists
        if client.indices.exists(index=index_name):
            logger.info(f"Index {index_name} already exists")
            return True
        
        # Create metadata index
        index_body = {
            'settings': {
                'index': {
                    'number_of_shards': 1,
                    'number_of_replicas': 0
                }
            },
            'mappings': {
                'properties': {
                    'document_id': {'type': 'keyword'},
                    'title': {'type': 'text'},
                    'size': {'type': 'long'},
                    'upload_date': {'type': 'date'},
                    'content': {'type': 'text'},
                    'source': {'type': 'keyword'}
                }
            }
        }
        
        client.indices.create(index=index_name, body=index_body)
        logger.info(f"Created index {index_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating metadata index: {str(e)}")
        raise


def create_vector_index():
    """Create vector index for embeddings — uses faiss engine required by Bedrock KB"""
    index_name = 'vector-index'

    try:
        # Always delete and recreate to ensure correct engine (faiss required by Bedrock KB)
        if client.indices.exists(index=index_name):
            logger.info(f"Deleting existing {index_name} to ensure correct faiss engine")
            client.indices.delete(index=index_name)

        index_body = {
            'settings': {
                'index': {
                    'number_of_shards': 1,
                    'number_of_replicas': 0,
                    'knn': True
                }
            },
            'mappings': {
                'properties': {
                    'document_id': {'type': 'keyword'},
                    'chunk_id': {'type': 'keyword'},
                    'text': {'type': 'text'},
                    'embedding': {
                        'type': 'knn_vector',
                        'dimension': 1536,
                        'method': {
                            'name': 'hnsw',
                            'space_type': 'l2',
                            'engine': 'faiss',
                            'parameters': {
                                'ef_construction': 256,
                                'm': 16
                            }
                        }
                    }
                }
            }
        }

        client.indices.create(index=index_name, body=index_body)
        logger.info(f"Created {index_name} with faiss engine")
        return True

    except Exception as e:
        logger.error(f"Error creating vector index: {str(e)}")
        raise


def create_suggestions_index():
    """Create suggestions index for autocomplete"""
    index_name = 'suggestions-index'
    
    try:
        # Check if index already exists
        if client.indices.exists(index=index_name):
            logger.info(f"Index {index_name} already exists")
            return True
        
        # Create suggestions index
        index_body = {
            'settings': {
                'index': {
                    'number_of_shards': 1,
                    'number_of_replicas': 0
                }
            },
            'mappings': {
                'properties': {
                    'suggestion': {'type': 'text'},
                    'weight': {'type': 'long'},
                    'document_id': {'type': 'keyword'}
                }
            }
        }
        
        client.indices.create(index=index_name, body=index_body)
        logger.info(f"Created index {index_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating suggestions index: {str(e)}")
        raise


def handler(event, context):
    """
    Lambda handler to bootstrap OpenSearch indexes
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Create all indexes
        logger.info("Starting index bootstrap process...")
        
        create_metadata_index()
        create_vector_index()
        create_suggestions_index()
        
        logger.info("Index bootstrap completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Indexes created successfully',
                'indexes': ['metadata-index', 'vector-index', 'suggestions-index']
            })
        }
        
    except Exception as e:
        logger.error(f"Error in index bootstrap: {str(e)}")
        return {
            'statusCode': 503,
            'body': json.dumps({
                'error': 'Failed to bootstrap indexes',
                'details': str(e)
            })
        }

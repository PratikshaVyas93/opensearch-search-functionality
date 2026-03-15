"""
Search Lambda Function
Searches metadata and vector indexes for documents matching a query
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
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS credentials for OpenSearch
credentials = boto3.Session().get_credentials()
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


def search_metadata_index(query):
    """Search metadata index for matching documents"""
    try:
        search_body = {
            'size': 10,
            'query': {
                'multi_match': {
                    'query': query,
                    'fields': ['title^2', 'content']
                }
            }
        }
        
        response = client.search(index='metadata-index', body=search_body)
        logger.info(f"Metadata search returned {len(response['hits']['hits'])} results")
        return response['hits']['hits']
        
    except Exception as e:
        logger.error(f"Error searching metadata index: {str(e)}")
        return []


def search_vector_index(query):
    """Search vector index for similar documents"""
    try:
        # For now, return empty as we need embeddings
        # In production, would call Bedrock to get query embedding
        logger.info("Vector search not yet implemented (requires query embedding)")
        return []
        
    except Exception as e:
        logger.error(f"Error searching vector index: {str(e)}")
        return []


def handler(event, context):
    """
    Lambda handler for search requests
    Expected query parameter: ?query=search_term
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract query from query parameters
        query_params = event.get('queryStringParameters', {})
        if not query_params:
            query_params = {}
        
        query = query_params.get('query', '').strip()
        
        if not query:
            logger.warning("No query parameter provided")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing query parameter'
                })
            }
        
        logger.info(f"Searching for: {query}")
        
        # Search both indexes
        metadata_results = search_metadata_index(query)
        vector_results = search_vector_index(query)
        
        # Combine and deduplicate results
        all_results = metadata_results + vector_results
        
        # Format results
        formatted_results = []
        seen_ids = set()
        
        for hit in all_results[:10]:  # Return top 10
            doc_id = hit['_id']
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                formatted_results.append({
                    'id': doc_id,
                    'score': hit['_score'],
                    'source': hit['_source']
                })
        
        logger.info(f"Returning {len(formatted_results)} results")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'query': query,
                'results': formatted_results,
                'count': len(formatted_results)
            })
        }
        
    except Exception as e:
        logger.error(f"Error in search handler: {str(e)}")
        return {
            'statusCode': 502,
            'body': json.dumps({
                'error': 'Search failed',
                'details': str(e)
            })
        }

"""
Suggestions Lambda Function
Provides autocomplete suggestions based on a prefix
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


def get_suggestions(prefix):
    """Get suggestions matching the given prefix"""
    try:
        search_body = {
            'size': 10,
            'query': {
                'match_phrase_prefix': {
                    'suggestion': {
                        'query': prefix,
                        'boost': 1.0
                    }
                }
            },
            'sort': [
                {'weight': {'order': 'desc'}},
                {'_score': {'order': 'desc'}}
            ]
        }
        
        response = client.search(index='suggestions-index', body=search_body)
        logger.info(f"Suggestions search returned {len(response['hits']['hits'])} results")
        return response['hits']['hits']
        
    except Exception as e:
        logger.error(f"Error searching suggestions index: {str(e)}")
        return []


def handler(event, context):
    """
    Lambda handler for suggestions requests
    Expected query parameter: ?prefix=search_prefix
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract prefix from query parameters
        query_params = event.get('queryStringParameters', {})
        if not query_params:
            query_params = {}
        
        prefix = query_params.get('prefix', '').strip()
        
        if not prefix:
            logger.warning("No prefix parameter provided")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing prefix parameter'
                })
            }
        
        logger.info(f"Getting suggestions for prefix: {prefix}")
        
        # Get suggestions
        suggestions = get_suggestions(prefix)
        
        # Format results
        formatted_suggestions = []
        for hit in suggestions[:10]:  # Return top 10
            formatted_suggestions.append({
                'suggestion': hit['_source'].get('suggestion', ''),
                'weight': hit['_source'].get('weight', 0),
                'score': hit['_score']
            })
        
        logger.info(f"Returning {len(formatted_suggestions)} suggestions")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'prefix': prefix,
                'suggestions': formatted_suggestions,
                'count': len(formatted_suggestions)
            })
        }
        
    except Exception as e:
        logger.error(f"Error in suggestions handler: {str(e)}")
        return {
            'statusCode': 502,
            'body': json.dumps({
                'error': 'Suggestions failed',
                'details': str(e)
            })
        }

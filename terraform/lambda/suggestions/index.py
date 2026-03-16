import json
import os
import boto3
import logging
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
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


def get_suggestions(query_prefix):
    """
    Get autocomplete suggestions from OpenSearch suggestions-index.
    
    Args:
        query_prefix: Prefix to search for suggestions
    
    Returns:
        List of suggestion strings
    """
    try:
        search_body = {
            "size": 10,
            "query": {
                "match_phrase_prefix": {
                    "text": query_prefix
                }
            }
        }
        
        response = opensearch_client.search(index='suggestions-index', body=search_body)
        
        suggestions = []
        for hit in response['hits']['hits']:
            suggestions.append({
                'text': hit['_source'].get('text'),
                'weight': hit['_source'].get('weight', 0),
                'doc_id': hit['_source'].get('doc_id')
            })
        
        # Sort by weight
        suggestions.sort(key=lambda x: x['weight'], reverse=True)
        return suggestions
        
    except Exception as e:
        logger.error(f"OpenSearch suggestions error: {str(e)}")
        raise


def lambda_handler(event, context):
    """
    Main Lambda handler for suggestions requests.
    
    Expected event format:
    {
        "queryStringParameters": {
            "q": "search prefix"
        }
    }
    """
    try:
        # Parse request
        query_params = event.get('queryStringParameters', {}) or {}
        query_prefix = query_params.get('q', '')
        
        if not query_prefix:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'q parameter is required'})
            }
        
        # Get suggestions
        logger.info(f"Getting suggestions for: {query_prefix}")
        suggestions = get_suggestions(query_prefix)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'suggestions': suggestions
            })
        }
        
    except Exception as e:
        logger.error(f"Suggestions Lambda error: {str(e)}")
        return {
            'statusCode': 502,
            'body': json.dumps({
                'error': 'suggestions_failed',
                'detail': str(e)
            })
        }

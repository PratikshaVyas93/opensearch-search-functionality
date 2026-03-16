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
rag_lambda_name = os.environ.get('RAG_LAMBDA_NAME')
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

lambda_client = boto3.client('lambda', region_name=region)


def search_opensearch(query, index_names=['chunk-index', 'metadata-index']):
    """
    Search OpenSearch indexes for relevant documents.
    
    Args:
        query: Search query string
        index_names: List of indexes to search
    
    Returns:
        List of search results with metadata
    """
    try:
        search_body = {
            "size": 10,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["text^2", "title", "s3_key"]
                }
            }
        }
        
        results = []
        for index in index_names:
            try:
                response = opensearch_client.search(index=index, body=search_body)
                for hit in response['hits']['hits']:
                    results.append({
                        'index': index,
                        'score': hit['_score'],
                        'source': hit['_source']
                    })
            except Exception as e:
                logger.warning(f"Error searching {index}: {str(e)}")
                continue
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:5]  # Return top 5 results
        
    except Exception as e:
        logger.error(f"OpenSearch search error: {str(e)}")
        raise


def invoke_rag_lambda(query, search_results):
    """
    Invoke RAG Lambda with search results for LLM generation.
    
    Args:
        query: Original search query
        search_results: Results from OpenSearch search
    
    Returns:
        Generated answer from RAG Lambda
    """
    try:
        payload = {
            'query': query,
            'context': json.dumps(search_results)
        }
        
        response = lambda_client.invoke(
            FunctionName=rag_lambda_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        response_payload = json.loads(response['Payload'].read())
        return response_payload
        
    except Exception as e:
        logger.error(f"RAG Lambda invocation error: {str(e)}")
        raise


def lambda_handler(event, context):
    """
    Main Lambda handler for search requests.
    
    Expected event format:
    {
        "body": {
            "query": "search query string"
        }
    }
    """
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        query = body.get('query')
        if not query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'query parameter is required'})
            }
        
        # Search OpenSearch
        logger.info(f"Searching for: {query}")
        search_results = search_opensearch(query)
        
        if not search_results:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'results': [],
                    'generated_answer': 'No relevant documents found.'
                })
            }
        
        # Invoke RAG Lambda
        logger.info(f"Invoking RAG Lambda with {len(search_results)} results")
        rag_response = invoke_rag_lambda(query, search_results)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'results': search_results,
                'generated_answer': rag_response.get('answer', 'Unable to generate answer')
            })
        }
        
    except Exception as e:
        logger.error(f"Search Lambda error: {str(e)}")
        return {
            'statusCode': 502,
            'body': json.dumps({
                'error': 'search_failed',
                'detail': str(e)
            })
        }

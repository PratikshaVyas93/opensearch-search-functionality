import json
import os
import boto3
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_client = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
bedrock_model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0')

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


def invoke_bedrock_with_retry(prompt, max_retries=MAX_RETRIES):
    """
    Invoke Bedrock Agent Runtime with exponential backoff retry logic.
    
    Args:
        prompt: The prompt to send to Bedrock
        max_retries: Maximum number of retry attempts
    
    Returns:
        Generated response from Bedrock
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Invoking Bedrock (attempt {attempt + 1}/{max_retries})")
            
            response = bedrock_client.invoke_model(
                modelId=bedrock_model_id,
                body=json.dumps({
                    'prompt': prompt,
                    'max_tokens': 1024,
                    'temperature': 0.7,
                    'top_p': 0.9
                })
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract text from response
            if 'completion' in response_body:
                return response_body['completion']
            elif 'content' in response_body:
                if isinstance(response_body['content'], list):
                    return response_body['content'][0].get('text', '')
                return response_body['content']
            
            return str(response_body)
            
        except bedrock_client.exceptions.ThrottlingException as e:
            logger.warning(f"Bedrock throttled (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                raise
                
        except Exception as e:
            logger.error(f"Bedrock invocation error (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                wait_time = RETRY_DELAY * (2 ** attempt)
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                raise
    
    raise Exception("Failed to invoke Bedrock after maximum retries")


def build_rag_prompt(query, context):
    """
    Build a RAG prompt with context for Bedrock.
    
    Args:
        query: Original user query
        context: Retrieved context from OpenSearch
    
    Returns:
        Formatted prompt string
    """
    context_text = ""
    if isinstance(context, str):
        try:
            context_data = json.loads(context)
        except:
            context_data = context
    else:
        context_data = context
    
    if isinstance(context_data, list):
        for i, item in enumerate(context_data, 1):
            if isinstance(item, dict):
                source = item.get('source', {})
                if isinstance(source, dict):
                    text = source.get('text', '')
                else:
                    text = str(source)
            else:
                text = str(item)
            context_text += f"{i}. {text}\n"
    else:
        context_text = str(context_data)
    
    prompt = f"""You are a helpful assistant. Answer the following question based on the provided context.

Context:
{context_text}

Question: {query}

Answer:"""
    
    return prompt


def lambda_handler(event, context):
    """
    Main Lambda handler for RAG generation.
    
    Expected event format:
    {
        "query": "user query",
        "context": "[search results as JSON string]"
    }
    """
    try:
        # Parse request
        query = event.get('query')
        context = event.get('context')
        
        if not query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'query parameter is required'})
            }
        
        if not context:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'context parameter is required'})
            }
        
        # Build RAG prompt
        logger.info(f"Building RAG prompt for query: {query}")
        prompt = build_rag_prompt(query, context)
        
        # Invoke Bedrock with retry logic
        logger.info("Invoking Bedrock for RAG generation")
        answer = invoke_bedrock_with_retry(prompt)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'answer': answer.strip()
            })
        }
        
    except Exception as e:
        logger.error(f"RAG Lambda error: {str(e)}")
        return {
            'statusCode': 503,
            'body': json.dumps({
                'error': 'generation_failed',
                'detail': str(e)
            })
        }

"""
Metadata & Suggestions Indexer Lambda
Reads a single JSON file from S3, dynamically indexes all fields into
metadata-index and extracts suggestions from any string/list values.

Designed to handle any JSON shape — no fixed schema required.
"""

import json
import logging
import os
import re
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')

session = boto3.Session()
AWS_REGION = session.region_name or 'us-east-1'
s3_client = boto3.client('s3')

credentials = session.get_credentials()
auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    AWS_REGION,
    'aoss',
    session_token=credentials.token
)

opensearch_client = OpenSearch(
    hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=30
)

# Fields to skip when building suggestions (low-value for autocomplete)
SKIP_SUGGESTION_FIELDS = {'document_id', 'id', 'url', 'uri', 'path', 'key',
                           'bucket', 'size', 'checksum', 'hash', 'version'}

# Minimum word length for suggestions
MIN_WORD_LENGTH = 3

# Max suggestions per document to avoid index bloat
MAX_SUGGESTIONS = 50


def load_json_from_s3(bucket, key):
    """Download and parse the JSON file from S3."""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        raw = response['Body'].read().decode('utf-8')
        data = json.loads(raw)
        logger.info(f"Loaded JSON from s3://{bucket}/{key} — fields: {list(data.keys())}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in s3://{bucket}/{key}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to read s3://{bucket}/{key}: {e}")
        raise


def derive_document_id(data, bucket, key):
    """
    Use document_id field if present, otherwise fall back to
    id, then the S3 key (stripped of extension).
    """
    for field in ('document_id', 'id', 'doc_id', 'documentId'):
        if field in data and data[field]:
            return str(data[field])
    # Fallback: use S3 key without extension
    return key.rsplit('.', 1)[0].replace('/', '_')


def build_metadata_doc(data, document_id, bucket, key):
    """
    Build the metadata document to index.
    Stores ALL fields from the JSON dynamically, plus adds
    _document_id, _s3_bucket, _s3_key as system fields.
    """
    doc = dict(data)  # copy all fields as-is
    doc['_document_id'] = document_id
    doc['_s3_bucket'] = bucket
    doc['_s3_key'] = key
    return doc


def extract_text_values(data, prefix='', depth=0):
    """
    Recursively walk the JSON and collect (field_name, text_value, weight) tuples.
    - String values → direct suggestion candidates
    - List values → each string item is a candidate
    - Nested dicts → recurse (max depth 3 to avoid runaway nesting)
    - Numbers/bools → skipped
    Weight is higher for top-level fields, lower for nested ones.
    """
    if depth > 3:
        return []

    results = []
    base_weight = max(1, 10 - depth * 3)

    for field, value in data.items():
        full_field = f"{prefix}.{field}" if prefix else field
        field_lower = field.lower()

        # Skip known low-value fields
        if field_lower in SKIP_SUGGESTION_FIELDS:
            continue

        if isinstance(value, str) and value.strip():
            results.append((full_field, value.strip(), base_weight))

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    results.append((full_field, item.strip(), base_weight))
                elif isinstance(item, dict):
                    results.extend(extract_text_values(item, full_field, depth + 1))

        elif isinstance(value, dict):
            results.extend(extract_text_values(value, full_field, depth + 1))

    return results


def tokenize(text):
    """Split text into meaningful words, deduplicated, min length enforced."""
    words = re.findall(r"[a-zA-Z0-9']+", text.lower())
    seen = set()
    result = []
    for w in words:
        w = w.strip("'")
        if len(w) >= MIN_WORD_LENGTH and w not in seen:
            seen.add(w)
            result.append(w)
    return result


def build_suggestions(data):
    """
    Dynamically build suggestions from all string/list fields.
    Two types:
    1. Full phrase suggestions — the entire field value (e.g. full title)
    2. Token suggestions — individual words from string values
    Returns list of {suggestion, weight, source_field}
    """
    suggestions = []
    seen_suggestions = set()

    text_values = extract_text_values(data)

    for field, text, weight in text_values:
        # Full phrase (high weight — exact matches are most useful)
        phrase = text.lower().strip()
        if phrase not in seen_suggestions and len(phrase) >= MIN_WORD_LENGTH:
            suggestions.append({
                'suggestion': text,
                'weight': weight + 5,  # boost full phrases
                'source_field': field
            })
            seen_suggestions.add(phrase)

        # Individual tokens from longer text values
        if len(text.split()) > 1:  # only tokenize multi-word values
            for token in tokenize(text):
                if token not in seen_suggestions:
                    suggestions.append({
                        'suggestion': token,
                        'weight': weight,
                        'source_field': field
                    })
                    seen_suggestions.add(token)

        if len(suggestions) >= MAX_SUGGESTIONS:
            break

    logger.info(f"Built {len(suggestions)} suggestions from {len(text_values)} text values")
    return suggestions[:MAX_SUGGESTIONS]


def index_metadata(document_id, doc):
    """Write the full metadata document to metadata-index."""
    try:
        opensearch_client.index(
            index='metadata-index',
            id=document_id,
            body=doc
        )
        logger.info(f"Indexed metadata for {document_id} ({len(doc)} fields)")
    except Exception as e:
        logger.error(f"Failed to index metadata for {document_id}: {e}")
        raise


def index_suggestions(document_id, suggestions):
    """Write all suggestion entries to suggestions-index."""
    try:
        for i, s in enumerate(suggestions):
            opensearch_client.index(
                index='suggestions-index',
                id=f"{document_id}_s_{i}",
                body={
                    'suggestion': s['suggestion'],
                    'weight': s['weight'],
                    'source_field': s['source_field'],
                    'document_id': document_id
                }
            )
        logger.info(f"Indexed {len(suggestions)} suggestions for {document_id}")
    except Exception as e:
        logger.error(f"Failed to index suggestions for {document_id}: {e}")
        raise


def handler(event, context):
    """
    Entry point. Receives bucket + key from Step Functions.
    Expected event shape:
    {
      "detail": {
        "bucket": { "name": "..." },
        "object": { "key": "..." }
      }
    }
    """
    logger.info(f"Event: {json.dumps(event)}")

    try:
        detail = event.get('detail', {})
        bucket = detail.get('bucket', {}).get('name')
        key = detail.get('object', {}).get('key')

        if not bucket or not key:
            # Also support flat event shape from Step Functions
            bucket = event.get('bucket')
            key = event.get('key')

        if not bucket or not key:
            raise ValueError(f"Missing bucket or key in event: {json.dumps(event)}")

        logger.info(f"Processing s3://{bucket}/{key}")

        # Load JSON
        data = load_json_from_s3(bucket, key)

        # Derive document ID
        document_id = derive_document_id(data, bucket, key)
        logger.info(f"Document ID: {document_id}")

        # Build and index metadata (all fields stored dynamically)
        metadata_doc = build_metadata_doc(data, document_id, bucket, key)
        index_metadata(document_id, metadata_doc)

        # Build and index suggestions (dynamic, from all string/list fields)
        suggestions = build_suggestions(data)
        index_suggestions(document_id, suggestions)

        return {
            'statusCode': 200,
            'document_id': document_id,
            'fields_indexed': len(data),
            'suggestions_indexed': len(suggestions)
        }

    except Exception as e:
        logger.error(f"Indexer failed: {e}")
        return {
            'statusCode': 500,
            'error': str(e)
        }

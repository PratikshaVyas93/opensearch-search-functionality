#!/usr/bin/env python3
"""Create OpenSearch indexes for the RAG pipeline.

Usage:
    OPENSEARCH_ENDPOINT=https://... python scripts/create_indexes.py
    python scripts/create_indexes.py --endpoint https://...
"""

import argparse
import json
import os
import sys

import boto3
import requests
from requests_aws4auth import AWS4Auth

INDEXES = {
    "chunk-index": {
        "settings": {"index.knn": True},
        "mappings": {
            "properties": {
                "id":         {"type": "keyword"},
                "text":       {"type": "text"},
                "embedding":  {"type": "knn_vector", "dimension": 1536},
                "source_uri": {"type": "keyword"},
                "chunk_seq":  {"type": "integer"},
            }
        },
    },
    "metadata-index": {
        "mappings": {
            "properties": {
                "doc_id":      {"type": "keyword"},
                "s3_key":      {"type": "keyword"},
                "title":       {"type": "text"},
                "uploaded_at": {"type": "date"},
                "tags":        {"type": "keyword"},
            }
        }
    },
    "suggestions-index": {
        "mappings": {
            "properties": {
                "suggestion_id": {"type": "keyword"},
                "text":          {"type": "completion"},
                "doc_id":        {"type": "keyword"},
                "weight":        {"type": "integer"},
            }
        }
    },
}


def get_aws_auth() -> AWS4Auth:
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    region = session.region_name or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    return AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        "es",
        session_token=credentials.token,
    )


def create_index(endpoint: str, name: str, body: dict, auth: AWS4Auth) -> None:
    url = f"{endpoint.rstrip('/')}/{name}"
    response = requests.put(
        url,
        auth=auth,
        headers={"Content-Type": "application/json"},
        data=json.dumps(body),
        timeout=30,
    )

    if response.status_code in (200, 201):
        print(f"Created index {name}")
        return

    if response.status_code == 400:
        try:
            error_type = response.json().get("error", {}).get("type", "")
        except ValueError:
            error_type = ""
        if error_type == "resource_already_exists_exception":
            print(f"Index {name} already exists, skipping")
            return

    print(f"ERROR creating {name}: {response.status_code} {response.text}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create OpenSearch indexes for the RAG pipeline.")
    parser.add_argument("--endpoint", help="OpenSearch endpoint URL")
    args = parser.parse_args()

    endpoint = os.environ.get("OPENSEARCH_ENDPOINT") or args.endpoint
    if not endpoint:
        print("ERROR: OPENSEARCH_ENDPOINT environment variable or --endpoint argument is required")
        sys.exit(1)

    auth = get_aws_auth()

    for name, body in INDEXES.items():
        create_index(endpoint, name, body, auth)


if __name__ == "__main__":
    main()

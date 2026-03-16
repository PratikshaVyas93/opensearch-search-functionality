"""
Property-based tests for the Terraform OpenSearch module.

**Validates: Requirements 4.1, 4.3**

Property 1: For any valid collection name (lowercase alphanumeric + hyphens,
3-32 chars, must start with a letter), the module must create a collection
resource using var.collection_name — no hardcoded names — and outputs.tf
must expose both collection_endpoint and collection_arn via resource
attribute references.

Feature: rag-pipeline-infrastructure
Property 1: OpenSearch module accepts any valid collection name
"""
import re
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OPENSEARCH_DIR = Path(__file__).parent.parent / "terraform" / "opensearch"

# Valid OpenSearch Serverless collection name rules:
# lowercase alphanumeric + hyphens, 3-32 chars, must start with a letter.
_LETTER = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=1,
    max_size=1,
)
_BODY = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
    min_size=0,
    max_size=30,
)

valid_collection_name = st.builds(
    lambda start, body: start + body,
    _LETTER,
    _BODY,
).filter(lambda s: 3 <= len(s) <= 32)


def read_tf(filename: str) -> str:
    return (OPENSEARCH_DIR / filename).read_text()


def extract_block(content: str, resource_type: str, resource_name: str) -> str:
    """Return the body of a Terraform resource block."""
    pattern = (
        r'resource\s+"'
        + re.escape(resource_type)
        + r'"\s+"'
        + re.escape(resource_name)
        + r'"\s*\{([^}]+)\}'
    )
    match = re.search(pattern, content, re.DOTALL)
    assert match, f"Could not locate {resource_type}.{resource_name} block"
    return match.group(1)


def extract_variable_block(content: str, var_name: str) -> str:
    pattern = r'variable\s+"' + re.escape(var_name) + r'"\s*\{([^}]+)\}'
    match = re.search(pattern, content, re.DOTALL)
    assert match, f"Could not locate variable '{var_name}' block"
    return match.group(1)


def extract_output_block(content: str, output_name: str) -> str:
    pattern = r'output\s+"' + re.escape(output_name) + r'"\s*\{([^}]+)\}'
    match = re.search(pattern, content, re.DOTALL)
    assert match, f"Could not locate output '{output_name}' block"
    return match.group(1)


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

class TestOpenSearchModuleAcceptsAnyValidCollectionName:
    """
    Property 1: For any valid collection name the module must create the
    collection resource using var.collection_name — no hardcoded names —
    and expose both endpoint and ARN outputs via resource attribute references.
    """

    @given(collection_name=valid_collection_name)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_collection_resource_uses_variable_not_hardcoded_name(
        self, collection_name: str
    ) -> None:
        """
        For any valid collection name, the collection resource must reference
        var.collection_name rather than embedding the name literally.
        """
        content = read_tf("main.tf")
        collection_block = extract_block(
            content, "aws_opensearchserverless_collection", "this"
        )

        assert "var.collection_name" in collection_block, (
            f"Collection block must use var.collection_name "
            f"(tested with collection_name={collection_name!r})"
        )
        assert collection_name not in collection_block, (
            f"Collection block must not contain a hardcoded name "
            f"(found {collection_name!r} in block)"
        )

    @given(collection_name=valid_collection_name)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_variables_accept_any_valid_collection_name(
        self, collection_name: str
    ) -> None:
        """
        For any valid collection name, variables.tf must declare collection_name
        as a plain string with no default — meaning any name is accepted without
        modifying the module.
        """
        content = read_tf("variables.tf")
        var_block = extract_variable_block(content, "collection_name")

        assert re.search(r"type\s*=\s*string", var_block), (
            "collection_name variable must have type = string"
        )
        assert "default" not in var_block, (
            f"collection_name must not have a default value "
            f"(tested with collection_name={collection_name!r})"
        )

    @given(collection_name=valid_collection_name)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_outputs_expose_endpoint_and_arn_for_any_collection_name(
        self, collection_name: str
    ) -> None:
        """
        For any valid collection name, outputs.tf must expose both
        collection_endpoint and collection_arn via resource attribute references.
        """
        content = read_tf("outputs.tf")

        endpoint_output = extract_output_block(content, "collection_endpoint")
        arn_output = extract_output_block(content, "collection_arn")

        assert re.search(
            r"value\s*=\s*aws_opensearchserverless_collection\.this\.collection_endpoint",
            endpoint_output,
        ), (
            "collection_endpoint output must reference "
            "aws_opensearchserverless_collection.this.collection_endpoint "
            f"(tested with collection_name={collection_name!r})"
        )
        assert re.search(
            r"value\s*=\s*aws_opensearchserverless_collection\.this\.arn",
            arn_output,
        ), (
            "collection_arn output must reference "
            "aws_opensearchserverless_collection.this.arn "
            f"(tested with collection_name={collection_name!r})"
        )

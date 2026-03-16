"""
Property-based tests for the Terraform backend module.

**Validates: Requirements 1.1, 1.3**

Property 1: For any valid bucket and table name (alphanumeric, hyphens, 3-63 chars),
the module must create both resources with those exact names via variable references —
no hardcoded names.

Feature: rag-pipeline-infrastructure
Property 1: backend module accepts any valid resource name
"""
import re
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BACKEND_DIR = Path(__file__).parent.parent / "terraform" / "backend"

# Valid AWS name alphabet: lowercase alphanumeric + hyphens, 3-63 chars,
# must start and end with an alphanumeric character.
_BODY = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
    min_size=1,
    max_size=61,
)
_ALNUM = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=1,
    max_size=1,
)

valid_resource_name = st.builds(
    lambda start, body, end: start + body + end,
    _ALNUM,
    _BODY,
    _ALNUM,
).filter(lambda s: 3 <= len(s) <= 63)


def read_tf(filename: str) -> str:
    return (BACKEND_DIR / filename).read_text()


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

class TestBackendModuleAcceptsAnyValidName:
    """
    Property 1: For any valid bucket and table name the module must create
    both resources with those exact names — via variable references only.
    """

    @given(bucket_name=valid_resource_name, table_name=valid_resource_name)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_s3_bucket_uses_variable_not_hardcoded_name(
        self, bucket_name: str, table_name: str
    ) -> None:
        """
        For any valid bucket name, the S3 bucket resource must reference
        var.state_bucket_name rather than embedding the name literally.
        """
        content = read_tf("main.tf")
        bucket_block = extract_block(content, "aws_s3_bucket", "terraform_state")

        # The bucket attribute must use the variable reference
        assert "var.state_bucket_name" in bucket_block, (
            f"S3 bucket block must use var.state_bucket_name "
            f"(tested with bucket_name={bucket_name!r})"
        )
        # The literal name must NOT appear in the bucket block
        assert bucket_name not in bucket_block, (
            f"S3 bucket block must not contain a hardcoded name "
            f"(found {bucket_name!r} in block)"
        )

    @given(bucket_name=valid_resource_name, table_name=valid_resource_name)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_dynamodb_table_uses_variable_not_hardcoded_name(
        self, bucket_name: str, table_name: str
    ) -> None:
        """
        For any valid table name, the DynamoDB table resource must reference
        var.lock_table_name rather than embedding the name literally.
        """
        content = read_tf("main.tf")
        table_block = extract_block(content, "aws_dynamodb_table", "terraform_lock")

        assert "var.lock_table_name" in table_block, (
            f"DynamoDB table block must use var.lock_table_name "
            f"(tested with table_name={table_name!r})"
        )
        assert table_name not in table_block, (
            f"DynamoDB table block must not contain a hardcoded name "
            f"(found {table_name!r} in block)"
        )

    @given(bucket_name=valid_resource_name, table_name=valid_resource_name)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_variables_accept_any_valid_name(
        self, bucket_name: str, table_name: str
    ) -> None:
        """
        For any valid name pair, the variables.tf must declare both input
        variables as plain strings with no default — meaning any name is
        accepted without modifying the module.
        """
        content = read_tf("variables.tf")

        bucket_var = extract_variable_block(content, "state_bucket_name")
        table_var = extract_variable_block(content, "lock_table_name")

        # Both variables must be typed as string
        assert re.search(r"type\s*=\s*string", bucket_var), (
            "state_bucket_name variable must have type = string"
        )
        assert re.search(r"type\s*=\s*string", table_var), (
            "lock_table_name variable must have type = string"
        )

        # Neither variable should have a hardcoded default that would
        # override the caller-supplied name
        assert "default" not in bucket_var, (
            f"state_bucket_name must not have a default value "
            f"(tested with bucket_name={bucket_name!r})"
        )
        assert "default" not in table_var, (
            f"lock_table_name must not have a default value "
            f"(tested with table_name={table_name!r})"
        )

    @given(bucket_name=valid_resource_name, table_name=valid_resource_name)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_outputs_expose_resource_names_for_any_input(
        self, bucket_name: str, table_name: str
    ) -> None:
        """
        For any valid name pair, the outputs.tf must expose both resource
        names by referencing the actual resource attributes — ensuring the
        caller always gets back the exact name that was passed in.
        """
        content = read_tf("outputs.tf")

        bucket_output = extract_output_block(content, "state_bucket_name")
        table_output = extract_output_block(content, "lock_table_name")

        assert re.search(
            r"value\s*=\s*aws_s3_bucket\.terraform_state\.id", bucket_output
        ), (
            "state_bucket_name output must reference aws_s3_bucket.terraform_state.id "
            f"(tested with bucket_name={bucket_name!r})"
        )
        assert re.search(
            r"value\s*=\s*aws_dynamodb_table\.terraform_lock\.name", table_output
        ), (
            "lock_table_name output must reference aws_dynamodb_table.terraform_lock.name "
            f"(tested with table_name={table_name!r})"
        )

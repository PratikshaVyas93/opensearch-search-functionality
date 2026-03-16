"""
Property-based tests for the Terraform S3 module.

**Validates: Requirements 2.1, 2.2**

Property 1: For any valid S3 bucket name (alphanumeric, hyphens, 3-63 chars),
the module must create a bucket with that exact name via variable reference —
no hardcoded names — and expose both the bucket name and ARN as outputs.

Feature: rag-pipeline-infrastructure
Property 1: S3 module accepts any valid bucket name
"""
import re
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

S3_DIR = Path(__file__).parent.parent / "terraform" / "s3"

# Valid S3 bucket name alphabet: lowercase alphanumeric + hyphens, 3-63 chars,
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

valid_bucket_name = st.builds(
    lambda start, body, end: start + body + end,
    _ALNUM,
    _BODY,
    _ALNUM,
).filter(lambda s: 3 <= len(s) <= 63)


def read_tf(filename: str) -> str:
    return (S3_DIR / filename).read_text()


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

class TestS3ModuleAcceptsAnyValidBucketName:
    """
    Property 1: For any valid S3 bucket name the module must create the bucket
    using a variable reference — no hardcoded names — and expose both the
    bucket name and ARN as outputs.
    """

    @given(bucket_name=valid_bucket_name)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_s3_bucket_uses_variable_not_hardcoded_name(
        self, bucket_name: str
    ) -> None:
        """
        For any valid bucket name, the aws_s3_bucket resource must reference
        var.bucket_name rather than embedding the name literally.
        """
        content = read_tf("main.tf")
        bucket_block = extract_block(content, "aws_s3_bucket", "documents")

        # The bucket attribute must use the variable reference
        assert "var.bucket_name" in bucket_block, (
            f"S3 bucket block must use var.bucket_name "
            f"(tested with bucket_name={bucket_name!r})"
        )
        # The literal name must NOT appear in the bucket block
        assert bucket_name not in bucket_block, (
            f"S3 bucket block must not contain a hardcoded name "
            f"(found {bucket_name!r} in block)"
        )

    @given(bucket_name=valid_bucket_name)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_variables_accept_any_valid_bucket_name(
        self, bucket_name: str
    ) -> None:
        """
        For any valid bucket name, variables.tf must declare bucket_name as a
        plain string with no default — meaning any name is accepted without
        modifying the module.
        """
        content = read_tf("variables.tf")
        bucket_var = extract_variable_block(content, "bucket_name")

        # Variable must be typed as string
        assert re.search(r"type\s*=\s*string", bucket_var), (
            "bucket_name variable must have type = string"
        )

        # Variable must not have a hardcoded default
        assert "default" not in bucket_var, (
            f"bucket_name must not have a default value "
            f"(tested with bucket_name={bucket_name!r})"
        )

    @given(bucket_name=valid_bucket_name)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_outputs_expose_bucket_name_and_arn_for_any_input(
        self, bucket_name: str
    ) -> None:
        """
        For any valid bucket name, outputs.tf must expose both bucket_name
        (via aws_s3_bucket.documents.id) and bucket_arn (via
        aws_s3_bucket.documents.arn) — ensuring the caller always gets back
        the exact name and ARN for the created bucket.
        """
        content = read_tf("outputs.tf")

        name_output = extract_output_block(content, "bucket_name")
        arn_output = extract_output_block(content, "bucket_arn")

        assert re.search(
            r"value\s*=\s*aws_s3_bucket\.documents\.id", name_output
        ), (
            "bucket_name output must reference aws_s3_bucket.documents.id "
            f"(tested with bucket_name={bucket_name!r})"
        )
        assert re.search(
            r"value\s*=\s*aws_s3_bucket\.documents\.arn", arn_output
        ), (
            "bucket_arn output must reference aws_s3_bucket.documents.arn "
            f"(tested with bucket_name={bucket_name!r})"
        )

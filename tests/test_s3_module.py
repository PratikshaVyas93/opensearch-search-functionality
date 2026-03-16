"""
Unit tests for the Terraform S3 module.
Validates terraform/s3/{main,variables,outputs}.tf by parsing HCL content directly.
"""
import re
from pathlib import Path

S3_DIR = Path(__file__).parent.parent / "terraform" / "s3"


def read(filename: str) -> str:
    return (S3_DIR / filename).read_text()


# ---------------------------------------------------------------------------
# main.tf
# ---------------------------------------------------------------------------

class TestS3Bucket:
    def setup_method(self):
        self.content = read("main.tf")

    def test_s3_bucket_resource_exists(self):
        assert re.search(r'resource\s+"aws_s3_bucket"\s+"documents"', self.content), \
            "aws_s3_bucket.documents resource not found"

    def test_s3_bucket_name_uses_variable(self):
        """Bucket name must reference var.bucket_name, not a hardcoded string."""
        bucket_block = re.search(
            r'resource\s+"aws_s3_bucket"\s+"documents"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert bucket_block, "Could not locate aws_s3_bucket.documents block"
        assert "var.bucket_name" in bucket_block.group(1), \
            "S3 bucket name should use var.bucket_name, not a hardcoded value"


class TestS3Versioning:
    def setup_method(self):
        self.content = read("main.tf")

    def test_s3_versioning_resource_exists(self):
        assert re.search(r'resource\s+"aws_s3_bucket_versioning"\s+"documents"', self.content), \
            "aws_s3_bucket_versioning.documents resource not found"

    def test_s3_versioning_enabled(self):
        versioning_block = re.search(
            r'resource\s+"aws_s3_bucket_versioning"\s+"documents"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert versioning_block, "Could not locate aws_s3_bucket_versioning.documents block"
        assert re.search(r'status\s*=\s*"Enabled"', versioning_block.group(1)), \
            "Versioning status should be 'Enabled'"

    def test_s3_versioning_references_bucket(self):
        versioning_block = re.search(
            r'resource\s+"aws_s3_bucket_versioning"\s+"documents"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert versioning_block, "Could not locate aws_s3_bucket_versioning.documents block"
        assert "aws_s3_bucket.documents.id" in versioning_block.group(1), \
            "Versioning resource should reference aws_s3_bucket.documents.id"


class TestS3PublicAccessBlock:
    def setup_method(self):
        self.content = read("main.tf")

    def test_public_access_block_resource_exists(self):
        assert re.search(r'resource\s+"aws_s3_bucket_public_access_block"\s+"documents"', self.content), \
            "aws_s3_bucket_public_access_block.documents resource not found"

    def test_block_public_acls_is_true(self):
        block = re.search(
            r'resource\s+"aws_s3_bucket_public_access_block"\s+"documents"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_s3_bucket_public_access_block.documents block"
        assert re.search(r'block_public_acls\s*=\s*true', block.group(1)), \
            "block_public_acls should be true"

    def test_block_public_policy_is_true(self):
        block = re.search(
            r'resource\s+"aws_s3_bucket_public_access_block"\s+"documents"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_s3_bucket_public_access_block.documents block"
        assert re.search(r'block_public_policy\s*=\s*true', block.group(1)), \
            "block_public_policy should be true"

    def test_ignore_public_acls_is_true(self):
        block = re.search(
            r'resource\s+"aws_s3_bucket_public_access_block"\s+"documents"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_s3_bucket_public_access_block.documents block"
        assert re.search(r'ignore_public_acls\s*=\s*true', block.group(1)), \
            "ignore_public_acls should be true"

    def test_restrict_public_buckets_is_true(self):
        block = re.search(
            r'resource\s+"aws_s3_bucket_public_access_block"\s+"documents"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_s3_bucket_public_access_block.documents block"
        assert re.search(r'restrict_public_buckets\s*=\s*true', block.group(1)), \
            "restrict_public_buckets should be true"


# ---------------------------------------------------------------------------
# variables.tf
# ---------------------------------------------------------------------------

class TestVariables:
    def setup_method(self):
        self.content = read("variables.tf")

    def test_bucket_name_variable_defined(self):
        assert re.search(r'variable\s+"bucket_name"', self.content), \
            "variable 'bucket_name' not defined"

    def test_bucket_name_is_string_type(self):
        var_block = re.search(
            r'variable\s+"bucket_name"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert var_block, "Could not locate bucket_name variable block"
        assert re.search(r'type\s*=\s*string', var_block.group(1)), \
            "bucket_name should have type = string"


# ---------------------------------------------------------------------------
# outputs.tf
# ---------------------------------------------------------------------------

class TestOutputs:
    def setup_method(self):
        self.content = read("outputs.tf")

    def test_bucket_name_output_exists(self):
        assert re.search(r'output\s+"bucket_name"', self.content), \
            "output 'bucket_name' not found"

    def test_bucket_name_output_value(self):
        output_block = re.search(
            r'output\s+"bucket_name"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert output_block, "Could not locate bucket_name output block"
        assert re.search(r'value\s*=\s*aws_s3_bucket\.documents\.id', output_block.group(1)), \
            "bucket_name output value should reference aws_s3_bucket.documents.id"

    def test_bucket_arn_output_exists(self):
        assert re.search(r'output\s+"bucket_arn"', self.content), \
            "output 'bucket_arn' not found"

    def test_bucket_arn_output_value(self):
        output_block = re.search(
            r'output\s+"bucket_arn"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert output_block, "Could not locate bucket_arn output block"
        assert re.search(r'value\s*=\s*aws_s3_bucket\.documents\.arn', output_block.group(1)), \
            "bucket_arn output value should reference aws_s3_bucket.documents.arn"

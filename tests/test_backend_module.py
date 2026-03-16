"""
Unit tests for the Terraform backend module.
Validates terraform/backend/{main,variables,outputs}.tf by parsing HCL content directly.
"""
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent / "terraform" / "backend"


def read(filename: str) -> str:
    return (BACKEND_DIR / filename).read_text()


# ---------------------------------------------------------------------------
# main.tf
# ---------------------------------------------------------------------------

class TestS3Bucket:
    def setup_method(self):
        self.content = read("main.tf")

    def test_s3_bucket_resource_exists(self):
        assert re.search(r'resource\s+"aws_s3_bucket"\s+"terraform_state"', self.content), \
            "aws_s3_bucket.terraform_state resource not found"

    def test_s3_bucket_name_uses_variable(self):
        """Bucket name must reference var.state_bucket_name, not a hardcoded string."""
        bucket_block = re.search(
            r'resource\s+"aws_s3_bucket"\s+"terraform_state"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert bucket_block, "Could not locate aws_s3_bucket block"
        assert "var.state_bucket_name" in bucket_block.group(1), \
            "S3 bucket name should use var.state_bucket_name, not a hardcoded value"

    def test_s3_versioning_resource_exists(self):
        assert re.search(r'resource\s+"aws_s3_bucket_versioning"\s+"terraform_state"', self.content), \
            "aws_s3_bucket_versioning resource not found"

    def test_s3_versioning_enabled(self):
        versioning_block = re.search(
            r'resource\s+"aws_s3_bucket_versioning"\s+"terraform_state"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert versioning_block, "Could not locate aws_s3_bucket_versioning block"
        assert re.search(r'status\s*=\s*"Enabled"', versioning_block.group(1)), \
            "Versioning status should be 'Enabled'"

    def test_s3_versioning_references_bucket(self):
        versioning_block = re.search(
            r'resource\s+"aws_s3_bucket_versioning"\s+"terraform_state"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert versioning_block, "Could not locate aws_s3_bucket_versioning block"
        assert "aws_s3_bucket.terraform_state.id" in versioning_block.group(1), \
            "Versioning resource should reference aws_s3_bucket.terraform_state.id"


class TestDynamoDBTable:
    def setup_method(self):
        self.content = read("main.tf")

    def test_dynamodb_table_resource_exists(self):
        assert re.search(r'resource\s+"aws_dynamodb_table"\s+"terraform_lock"', self.content), \
            "aws_dynamodb_table.terraform_lock resource not found"

    def test_dynamodb_table_name_uses_variable(self):
        """Table name must reference var.lock_table_name, not a hardcoded string."""
        table_block = re.search(
            r'resource\s+"aws_dynamodb_table"\s+"terraform_lock"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert table_block, "Could not locate aws_dynamodb_table block"
        assert "var.lock_table_name" in table_block.group(1), \
            "DynamoDB table name should use var.lock_table_name, not a hardcoded value"

    def test_dynamodb_billing_mode_pay_per_request(self):
        table_block = re.search(
            r'resource\s+"aws_dynamodb_table"\s+"terraform_lock"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert table_block, "Could not locate aws_dynamodb_table block"
        assert re.search(r'billing_mode\s*=\s*"PAY_PER_REQUEST"', table_block.group(1)), \
            "DynamoDB billing_mode should be PAY_PER_REQUEST"

    def test_dynamodb_hash_key_is_lock_id(self):
        table_block = re.search(
            r'resource\s+"aws_dynamodb_table"\s+"terraform_lock"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert table_block, "Could not locate aws_dynamodb_table block"
        assert re.search(r'hash_key\s*=\s*"LockID"', table_block.group(1)), \
            "DynamoDB hash_key should be 'LockID'"


# ---------------------------------------------------------------------------
# variables.tf
# ---------------------------------------------------------------------------

class TestVariables:
    def setup_method(self):
        self.content = read("variables.tf")

    def test_state_bucket_name_variable_defined(self):
        assert re.search(r'variable\s+"state_bucket_name"', self.content), \
            "variable 'state_bucket_name' not defined"

    def test_state_bucket_name_is_string_type(self):
        var_block = re.search(
            r'variable\s+"state_bucket_name"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert var_block, "Could not locate state_bucket_name variable block"
        assert re.search(r'type\s*=\s*string', var_block.group(1)), \
            "state_bucket_name should have type = string"

    def test_lock_table_name_variable_defined(self):
        assert re.search(r'variable\s+"lock_table_name"', self.content), \
            "variable 'lock_table_name' not defined"

    def test_lock_table_name_is_string_type(self):
        var_block = re.search(
            r'variable\s+"lock_table_name"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert var_block, "Could not locate lock_table_name variable block"
        assert re.search(r'type\s*=\s*string', var_block.group(1)), \
            "lock_table_name should have type = string"


# ---------------------------------------------------------------------------
# outputs.tf
# ---------------------------------------------------------------------------

class TestOutputs:
    def setup_method(self):
        self.content = read("outputs.tf")

    def test_state_bucket_name_output_exists(self):
        assert re.search(r'output\s+"state_bucket_name"', self.content), \
            "output 'state_bucket_name' not found"

    def test_state_bucket_name_output_value(self):
        output_block = re.search(
            r'output\s+"state_bucket_name"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert output_block, "Could not locate state_bucket_name output block"
        assert re.search(r'value\s*=\s*aws_s3_bucket\.terraform_state\.id', output_block.group(1)), \
            "state_bucket_name output value should reference aws_s3_bucket.terraform_state.id"

    def test_lock_table_name_output_exists(self):
        assert re.search(r'output\s+"lock_table_name"', self.content), \
            "output 'lock_table_name' not found"

    def test_lock_table_name_output_value(self):
        output_block = re.search(
            r'output\s+"lock_table_name"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert output_block, "Could not locate lock_table_name output block"
        assert re.search(r'value\s*=\s*aws_dynamodb_table\.terraform_lock\.name', output_block.group(1)), \
            "lock_table_name output value should reference aws_dynamodb_table.terraform_lock.name"

"""
Unit tests for the Terraform OpenSearch Serverless module.
Validates terraform/opensearch/{main,variables,outputs}.tf by parsing HCL content directly.
"""
import re
from pathlib import Path

OPENSEARCH_DIR = Path(__file__).parent.parent / "terraform" / "opensearch"


def read(filename: str) -> str:
    return (OPENSEARCH_DIR / filename).read_text()


# ---------------------------------------------------------------------------
# main.tf — aws_opensearchserverless_collection
# ---------------------------------------------------------------------------

class TestOpenSearchCollection:
    def setup_method(self):
        self.content = read("main.tf")

    def test_collection_resource_exists(self):
        assert re.search(
            r'resource\s+"aws_opensearchserverless_collection"\s+"this"',
            self.content,
        ), "aws_opensearchserverless_collection.this resource not found"

    def test_collection_name_uses_variable(self):
        block = re.search(
            r'resource\s+"aws_opensearchserverless_collection"\s+"this"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_opensearchserverless_collection.this block"
        assert "var.collection_name" in block.group(1), \
            "collection name should reference var.collection_name"

    def test_collection_type_is_vectorsearch(self):
        block = re.search(
            r'resource\s+"aws_opensearchserverless_collection"\s+"this"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_opensearchserverless_collection.this block"
        assert re.search(r'type\s*=\s*"VECTORSEARCH"', block.group(1)), \
            "collection type should be 'VECTORSEARCH'"

    def test_collection_has_depends_on(self):
        block = re.search(
            r'resource\s+"aws_opensearchserverless_collection"\s+"this"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_opensearchserverless_collection.this block"
        assert "depends_on" in block.group(1), \
            "collection resource should have a depends_on block"


# ---------------------------------------------------------------------------
# main.tf — aws_opensearchserverless_encryption_policy
# ---------------------------------------------------------------------------

class TestEncryptionPolicy:
    def setup_method(self):
        self.content = read("main.tf")

    def test_encryption_policy_resource_exists(self):
        assert re.search(
            r'resource\s+"aws_opensearchserverless_encryption_policy"\s+"this"',
            self.content,
        ), "aws_opensearchserverless_encryption_policy.this resource not found"

    def test_encryption_policy_type_is_encryption(self):
        block = re.search(
            r'resource\s+"aws_opensearchserverless_encryption_policy"\s+"this"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_opensearchserverless_encryption_policy.this block"
        assert re.search(r'type\s*=\s*"encryption"', block.group(1)), \
            "encryption policy type should be 'encryption'"

    def test_encryption_policy_uses_aws_owned_key(self):
        block = re.search(
            r'resource\s+"aws_opensearchserverless_encryption_policy"\s+"this"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_opensearchserverless_encryption_policy.this block"
        assert re.search(r'AWSOwnedKey\s*=\s*true', block.group(1)), \
            "encryption policy should set AWSOwnedKey = true"


# ---------------------------------------------------------------------------
# main.tf — aws_opensearchserverless_security_policy (network)
# ---------------------------------------------------------------------------

class TestNetworkPolicy:
    def setup_method(self):
        self.content = read("main.tf")

    def test_network_policy_resource_exists(self):
        assert re.search(
            r'resource\s+"aws_opensearchserverless_security_policy"\s+"network"',
            self.content,
        ), "aws_opensearchserverless_security_policy.network resource not found"

    def test_network_policy_type_is_network(self):
        block = re.search(
            r'resource\s+"aws_opensearchserverless_security_policy"\s+"network"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_opensearchserverless_security_policy.network block"
        assert re.search(r'type\s*=\s*"network"', block.group(1)), \
            "network policy type should be 'network'"

    def test_network_policy_allows_public_access(self):
        block = re.search(
            r'resource\s+"aws_opensearchserverless_security_policy"\s+"network"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_opensearchserverless_security_policy.network block"
        assert re.search(r'AllowFromPublic\s*=\s*true', block.group(1)), \
            "network policy should set AllowFromPublic = true"


# ---------------------------------------------------------------------------
# main.tf — aws_opensearchserverless_access_policy
# ---------------------------------------------------------------------------

class TestAccessPolicy:
    def setup_method(self):
        self.content = read("main.tf")

    def test_access_policy_resource_exists(self):
        assert re.search(
            r'resource\s+"aws_opensearchserverless_access_policy"\s+"this"',
            self.content,
        ), "aws_opensearchserverless_access_policy.this resource not found"

    def test_access_policy_type_is_data(self):
        block = re.search(
            r'resource\s+"aws_opensearchserverless_access_policy"\s+"this"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_opensearchserverless_access_policy.this block"
        assert re.search(r'type\s*=\s*"data"', block.group(1)), \
            "access policy type should be 'data'"

    def test_access_policy_grants_aoss_permissions(self):
        block = re.search(
            r'resource\s+"aws_opensearchserverless_access_policy"\s+"this"\s*\{(.+?)\n\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate aws_opensearchserverless_access_policy.this block"
        assert re.search(r'"aoss:\*"', block.group(1)), \
            "access policy should grant aoss:* permissions"


# ---------------------------------------------------------------------------
# variables.tf
# ---------------------------------------------------------------------------

class TestVariables:
    def setup_method(self):
        self.content = read("variables.tf")

    def test_collection_name_variable_defined(self):
        assert re.search(r'variable\s+"collection_name"', self.content), \
            "variable 'collection_name' not defined"

    def test_collection_name_is_string_type(self):
        block = re.search(
            r'variable\s+"collection_name"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate collection_name variable block"
        assert re.search(r'type\s*=\s*string', block.group(1)), \
            "collection_name should have type = string"

    def test_access_principal_arns_variable_defined(self):
        assert re.search(r'variable\s+"access_principal_arns"', self.content), \
            "variable 'access_principal_arns' not defined"

    def test_access_principal_arns_is_list_of_string(self):
        block = re.search(
            r'variable\s+"access_principal_arns"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate access_principal_arns variable block"
        assert re.search(r'type\s*=\s*list\(string\)', block.group(1)), \
            "access_principal_arns should have type = list(string)"


# ---------------------------------------------------------------------------
# outputs.tf
# ---------------------------------------------------------------------------

class TestOutputs:
    def setup_method(self):
        self.content = read("outputs.tf")

    def test_collection_endpoint_output_exists(self):
        assert re.search(r'output\s+"collection_endpoint"', self.content), \
            "output 'collection_endpoint' not found"

    def test_collection_endpoint_output_value(self):
        block = re.search(
            r'output\s+"collection_endpoint"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate collection_endpoint output block"
        assert re.search(
            r'value\s*=\s*aws_opensearchserverless_collection\.this\.collection_endpoint',
            block.group(1),
        ), "collection_endpoint output should reference aws_opensearchserverless_collection.this.collection_endpoint"

    def test_collection_arn_output_exists(self):
        assert re.search(r'output\s+"collection_arn"', self.content), \
            "output 'collection_arn' not found"

    def test_collection_arn_output_value(self):
        block = re.search(
            r'output\s+"collection_arn"\s*\{([^}]+)\}',
            self.content,
            re.DOTALL,
        )
        assert block, "Could not locate collection_arn output block"
        assert re.search(
            r'value\s*=\s*aws_opensearchserverless_collection\.this\.arn',
            block.group(1),
        ), "collection_arn output should reference aws_opensearchserverless_collection.this.arn"

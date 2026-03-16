"""Unit tests for scripts/create_indexes.py."""

import sys
import json
from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# Patch heavy dependencies before importing the module under test
# ---------------------------------------------------------------------------

# Fake AWS4Auth so requests_aws4auth doesn't need to be installed
fake_auth = MagicMock(name="FakeAWS4Auth")

with patch.dict("sys.modules", {
    "boto3": MagicMock(),
    "requests_aws4auth": MagicMock(AWS4Auth=MagicMock(return_value=fake_auth)),
}):
    # Ensure a clean import each test run
    if "scripts.create_indexes" in sys.modules:
        del sys.modules["scripts.create_indexes"]
    if "create_indexes" in sys.modules:
        del sys.modules["create_indexes"]

    sys.path.insert(0, "scripts")
    import create_indexes  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ENDPOINT = "https://search.example.com"


def _mock_response(status_code: int, json_body: dict | None = None, text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if json_body is not None:
        resp.json.return_value = json_body
    else:
        resp.json.side_effect = ValueError("no json")
    return resp


# ---------------------------------------------------------------------------
# 1. Correct HTTP method and URL for each index
# ---------------------------------------------------------------------------

class TestCreateIndexURL:
    """Verify that create_index sends PUT to the correct URL for each index."""

    @pytest.mark.parametrize("index_name", list(create_indexes.INDEXES.keys()))
    def test_put_url(self, index_name):
        body = create_indexes.INDEXES[index_name]
        expected_url = f"{ENDPOINT}/{index_name}"

        with patch("create_indexes.requests.put", return_value=_mock_response(201)) as mock_put:
            create_indexes.create_index(ENDPOINT, index_name, body, fake_auth)

        mock_put.assert_called_once()
        actual_url = mock_put.call_args[0][0]
        assert actual_url == expected_url

    def test_all_three_indexes_called_from_main(self):
        """main() must call create_index (via requests.put) for all three indexes."""
        with patch("create_indexes.requests.put", return_value=_mock_response(201)) as mock_put, \
             patch("create_indexes.get_aws_auth", return_value=fake_auth), \
             patch.dict("os.environ", {"OPENSEARCH_ENDPOINT": ENDPOINT}):
            create_indexes.main()

        assert mock_put.call_count == 3
        called_urls = {c[0][0] for c in mock_put.call_args_list}
        for name in create_indexes.INDEXES:
            assert f"{ENDPOINT}/{name}" in called_urls


# ---------------------------------------------------------------------------
# 2. chunk-index body: knn_vector dimension=1536 and index.knn=True
# ---------------------------------------------------------------------------

class TestChunkIndexBody:
    def test_knn_vector_dimension(self):
        props = create_indexes.INDEXES["chunk-index"]["mappings"]["properties"]
        assert props["embedding"]["type"] == "knn_vector"
        assert props["embedding"]["dimension"] == 1536

    def test_index_knn_setting(self):
        settings = create_indexes.INDEXES["chunk-index"]["settings"]
        assert settings.get("index.knn") is True


# ---------------------------------------------------------------------------
# 3. metadata-index body: required fields
# ---------------------------------------------------------------------------

class TestMetadataIndexBody:
    REQUIRED_FIELDS = {"doc_id", "s3_key", "title", "uploaded_at", "tags"}

    def test_required_fields_present(self):
        props = create_indexes.INDEXES["metadata-index"]["mappings"]["properties"]
        assert self.REQUIRED_FIELDS.issubset(props.keys())


# ---------------------------------------------------------------------------
# 4. suggestions-index body: required fields and completion type
# ---------------------------------------------------------------------------

class TestSuggestionsIndexBody:
    def test_required_fields_present(self):
        props = create_indexes.INDEXES["suggestions-index"]["mappings"]["properties"]
        for field in ("suggestion_id", "text", "doc_id", "weight"):
            assert field in props

    def test_text_is_completion_type(self):
        props = create_indexes.INDEXES["suggestions-index"]["mappings"]["properties"]
        assert props["text"]["type"] == "completion"


# ---------------------------------------------------------------------------
# 5. HTTP 400 resource_already_exists_exception → no sys.exit (exit code 0)
# ---------------------------------------------------------------------------

class TestAlreadyExists:
    def test_no_exit_on_already_exists(self):
        resp = _mock_response(
            400,
            json_body={"error": {"type": "resource_already_exists_exception"}},
        )
        with patch("create_indexes.requests.put", return_value=resp):
            # Should NOT raise SystemExit
            create_indexes.create_index(ENDPOINT, "chunk-index", {}, fake_auth)

    def test_no_exit_on_already_exists_any_index(self):
        resp = _mock_response(
            400,
            json_body={"error": {"type": "resource_already_exists_exception"}},
        )
        with patch("create_indexes.requests.put", return_value=resp):
            for name in create_indexes.INDEXES:
                create_indexes.create_index(ENDPOINT, name, {}, fake_auth)  # must not raise


# ---------------------------------------------------------------------------
# 6. HTTP 500 → sys.exit(1)
# ---------------------------------------------------------------------------

class TestGeneric500:
    def test_exit_1_on_500(self):
        resp = _mock_response(500, text="Internal Server Error")
        with patch("create_indexes.requests.put", return_value=resp):
            with pytest.raises(SystemExit) as exc_info:
                create_indexes.create_index(ENDPOINT, "chunk-index", {}, fake_auth)
        assert exc_info.value.code == 1

    def test_exit_1_on_other_4xx(self):
        """Any non-already-exists 400 should also exit 1."""
        resp = _mock_response(400, json_body={"error": {"type": "some_other_error"}})
        with patch("create_indexes.requests.put", return_value=resp):
            with pytest.raises(SystemExit) as exc_info:
                create_indexes.create_index(ENDPOINT, "chunk-index", {}, fake_auth)
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# 7. HTTP 201 → success (no exit)
# ---------------------------------------------------------------------------

class TestSuccessResponse:
    @pytest.mark.parametrize("status_code", [200, 201])
    def test_no_exit_on_success(self, status_code):
        resp = _mock_response(status_code)
        with patch("create_indexes.requests.put", return_value=resp):
            # Should NOT raise SystemExit
            create_indexes.create_index(ENDPOINT, "chunk-index", {}, fake_auth)


# ---------------------------------------------------------------------------
# 8. Missing endpoint → sys.exit(1)
# ---------------------------------------------------------------------------

class TestMissingEndpoint:
    def test_exit_1_when_no_endpoint(self):
        with patch("create_indexes.get_aws_auth", return_value=fake_auth), \
             patch.dict("os.environ", {}, clear=True), \
             patch("sys.argv", ["create_indexes.py"]):
            with pytest.raises(SystemExit) as exc_info:
                create_indexes.main()
        assert exc_info.value.code == 1

    def test_endpoint_from_env_var(self):
        """When OPENSEARCH_ENDPOINT is set, main() should not exit."""
        with patch("create_indexes.requests.put", return_value=_mock_response(201)), \
             patch("create_indexes.get_aws_auth", return_value=fake_auth), \
             patch.dict("os.environ", {"OPENSEARCH_ENDPOINT": ENDPOINT}), \
             patch("sys.argv", ["create_indexes.py"]):
            create_indexes.main()  # must not raise

"""
Property-based tests for scripts/create_indexes.py.

**Validates: Requirements 5.1, 5.3, 5.4, 5.6**

Property 1: For any valid OpenSearch endpoint, script must issue PUT requests
for exactly three indexes with correct mappings.

Property 2: For any HTTP response, script must exit with status 0 iff response
is 2xx or already-exists, non-zero otherwise.

Feature: rag-pipeline-infrastructure
Property 1: index script issues PUT for exactly three indexes with correct mappings
Property 2: exit code is 0 iff response is 2xx or already-exists
"""

import sys
import json
from unittest.mock import MagicMock, patch, call

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Patch heavy dependencies before importing the module under test
# ---------------------------------------------------------------------------

fake_auth = MagicMock(name="FakeAWS4Auth")

with patch.dict("sys.modules", {
    "boto3": MagicMock(),
    "requests_aws4auth": MagicMock(AWS4Auth=MagicMock(return_value=fake_auth)),
}):
    if "scripts.create_indexes" in sys.modules:
        del sys.modules["scripts.create_indexes"]
    if "create_indexes" in sys.modules:
        del sys.modules["create_indexes"]

    sys.path.insert(0, "scripts")
    import create_indexes  # noqa: E402

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Valid hostname characters: alphanumeric, hyphens, dots
_hostname_char = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-.",
    min_size=3,
    max_size=40,
).filter(lambda s: not s.startswith("-") and not s.endswith("-") and ".." not in s)

# Optional path segment: empty or /something
_path_segment = st.one_of(
    st.just(""),
    st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_/",
        min_size=1,
        max_size=20,
    ).map(lambda s: "/" + s.lstrip("/")),
)

valid_endpoint = st.builds(
    lambda host, path: f"https://{host}{path}",
    _hostname_char,
    _path_segment,
)

# HTTP status codes split by category
status_2xx = st.integers(min_value=200, max_value=299)
status_3xx = st.integers(min_value=300, max_value=399)
status_4xx_non_already_exists = st.integers(min_value=401, max_value=499)
status_5xx = st.integers(min_value=500, max_value=599)
status_any = st.integers(min_value=100, max_value=599)

# Arbitrary response body text
response_body = st.text(min_size=0, max_size=200)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EXPECTED_INDEXES = {"chunk-index", "metadata-index", "suggestions-index"}


def _mock_response(status_code: int, json_body=None, text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if json_body is not None:
        resp.json.return_value = json_body
    else:
        resp.json.side_effect = ValueError("no json")
    return resp


# ---------------------------------------------------------------------------
# Property 1: For any valid endpoint, PUT is issued for exactly three indexes
#             with correct mappings
# ---------------------------------------------------------------------------

class TestProperty1IndexCreation:
    """
    Property 1: For any valid OpenSearch endpoint, script must issue PUT
    requests for exactly three indexes with correct mappings.
    """

    @given(endpoint=valid_endpoint)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_exactly_three_indexes_called(self, endpoint: str) -> None:
        """
        For any valid endpoint, main() must call requests.put exactly three
        times — once per index.
        """
        with patch("create_indexes.requests.put", return_value=_mock_response(201)) as mock_put, \
             patch("create_indexes.get_aws_auth", return_value=fake_auth), \
             patch.dict("os.environ", {"OPENSEARCH_ENDPOINT": endpoint}):
            create_indexes.main()

        assert mock_put.call_count == 3, (
            f"Expected exactly 3 PUT calls for endpoint {endpoint!r}, "
            f"got {mock_put.call_count}"
        )

    @given(endpoint=valid_endpoint)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_put_urls_match_expected_indexes(self, endpoint: str) -> None:
        """
        For any valid endpoint, the PUT URLs must correspond to exactly the
        three expected index names: chunk-index, metadata-index, suggestions-index.
        """
        with patch("create_indexes.requests.put", return_value=_mock_response(201)) as mock_put, \
             patch("create_indexes.get_aws_auth", return_value=fake_auth), \
             patch.dict("os.environ", {"OPENSEARCH_ENDPOINT": endpoint}):
            create_indexes.main()

        called_urls = {c[0][0] for c in mock_put.call_args_list}
        base = endpoint.rstrip("/")
        expected_urls = {f"{base}/{name}" for name in EXPECTED_INDEXES}

        assert called_urls == expected_urls, (
            f"PUT URLs {called_urls!r} do not match expected {expected_urls!r} "
            f"for endpoint {endpoint!r}"
        )

    @given(endpoint=valid_endpoint)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_indexes_dict_always_has_exactly_three_keys(self, endpoint: str) -> None:
        """
        The INDEXES dict must always contain exactly chunk-index, metadata-index,
        and suggestions-index — regardless of endpoint.
        """
        assert set(create_indexes.INDEXES.keys()) == EXPECTED_INDEXES, (
            f"INDEXES keys {set(create_indexes.INDEXES.keys())!r} != {EXPECTED_INDEXES!r}"
        )

    @given(endpoint=valid_endpoint)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_chunk_index_has_knn_vector_dimension_1536(self, endpoint: str) -> None:
        """
        For any valid endpoint, chunk-index must always declare a knn_vector
        field with dimension=1536.
        """
        props = create_indexes.INDEXES["chunk-index"]["mappings"]["properties"]
        assert props["embedding"]["type"] == "knn_vector", (
            "chunk-index embedding field must be of type knn_vector"
        )
        assert props["embedding"]["dimension"] == 1536, (
            f"chunk-index embedding dimension must be 1536, "
            f"got {props['embedding']['dimension']!r}"
        )


# ---------------------------------------------------------------------------
# Property 2: exit code is 0 iff response is 2xx or already-exists
# ---------------------------------------------------------------------------

class TestProperty2ExitCode:
    """
    Property 2: For any HTTP response, script must exit with status 0 iff
    response is 2xx or already-exists (400 + resource_already_exists_exception),
    non-zero otherwise.
    """

    @given(status=status_2xx, body=response_body)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_2xx_no_system_exit(self, status: int, body: str) -> None:
        """For any 2xx status, create_index must not raise SystemExit."""
        resp = _mock_response(status, text=body)
        with patch("create_indexes.requests.put", return_value=resp):
            # Must not raise
            create_indexes.create_index("https://example.com", "chunk-index", {}, fake_auth)

    @given(body=response_body)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_400_already_exists_no_system_exit(self, body: str) -> None:
        """
        For status 400 with resource_already_exists_exception, create_index
        must not raise SystemExit.
        """
        resp = _mock_response(
            400,
            json_body={"error": {"type": "resource_already_exists_exception"}},
            text=body,
        )
        with patch("create_indexes.requests.put", return_value=resp):
            create_indexes.create_index("https://example.com", "chunk-index", {}, fake_auth)

    @given(
        error_type=st.text(min_size=1, max_size=60).filter(
            lambda s: s != "resource_already_exists_exception"
        ),
        body=response_body,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_400_other_error_type_exits_1(self, error_type: str, body: str) -> None:
        """
        For status 400 with any error type other than resource_already_exists_exception,
        create_index must raise SystemExit(1).
        """
        resp = _mock_response(
            400,
            json_body={"error": {"type": error_type}},
            text=body,
        )
        with patch("create_indexes.requests.put", return_value=resp):
            with pytest.raises(SystemExit) as exc_info:
                create_indexes.create_index("https://example.com", "chunk-index", {}, fake_auth)
        assert exc_info.value.code == 1, (
            f"Expected SystemExit(1) for 400 with error_type={error_type!r}, "
            f"got code={exc_info.value.code!r}"
        )

    @given(status=status_3xx, body=response_body)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_3xx_exits_1(self, status: int, body: str) -> None:
        """For any 3xx status, create_index must raise SystemExit(1)."""
        resp = _mock_response(status, text=body)
        with patch("create_indexes.requests.put", return_value=resp):
            with pytest.raises(SystemExit) as exc_info:
                create_indexes.create_index("https://example.com", "chunk-index", {}, fake_auth)
        assert exc_info.value.code == 1, (
            f"Expected SystemExit(1) for status {status}, got {exc_info.value.code!r}"
        )

    @given(status=status_4xx_non_already_exists, body=response_body)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_4xx_non_already_exists_exits_1(self, status: int, body: str) -> None:
        """For any 4xx status (401-499), create_index must raise SystemExit(1)."""
        resp = _mock_response(status, text=body)
        with patch("create_indexes.requests.put", return_value=resp):
            with pytest.raises(SystemExit) as exc_info:
                create_indexes.create_index("https://example.com", "chunk-index", {}, fake_auth)
        assert exc_info.value.code == 1, (
            f"Expected SystemExit(1) for status {status}, got {exc_info.value.code!r}"
        )

    @given(status=status_5xx, body=response_body)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_5xx_exits_1(self, status: int, body: str) -> None:
        """For any 5xx status, create_index must raise SystemExit(1)."""
        resp = _mock_response(status, text=body)
        with patch("create_indexes.requests.put", return_value=resp):
            with pytest.raises(SystemExit) as exc_info:
                create_indexes.create_index("https://example.com", "chunk-index", {}, fake_auth)
        assert exc_info.value.code == 1, (
            f"Expected SystemExit(1) for status {status}, got {exc_info.value.code!r}"
        )

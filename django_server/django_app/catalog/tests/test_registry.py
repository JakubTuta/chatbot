"""registry.ollama.ai returns 200 with a manifest for a pullable tag, 404 for
one that doesn't exist, and has no `tags/list` endpoint — verify_tag must
turn each of those into the right VerifyResult without ever raising.
"""

import httpx
import pytest

from django_app.catalog import registry


class _FakeResponse:
    def __init__(self, status_code: int, json_body: dict | None = None):
        self.status_code = status_code
        self._json_body = json_body or {}

    def json(self):
        return self._json_body


def _client_returning(response: _FakeResponse):
    class _Client:
        def get(self, url, headers=None, timeout=None):
            return response

    return _Client()


def test_ok_manifest_sums_config_and_layer_sizes():
    manifest = {
        "config": {"size": 500},
        "layers": [{"size": 1000}, {"size": 2500}],
    }
    result = registry.verify_tag(_client_returning(_FakeResponse(200, manifest)), "llama3.1", "8b")

    assert result.status == "ok"
    assert result.size_bytes == 4000


def test_not_found_tag():
    result = registry.verify_tag(_client_returning(_FakeResponse(404)), "llama3.1", "bogus-tag")

    assert result.status == "not_found"
    assert result.size_bytes is None


def test_unexpected_status_is_error_not_a_crash():
    result = registry.verify_tag(_client_returning(_FakeResponse(500)), "llama3.1", "8b")

    assert result.status == "error"


def test_network_failure_is_error_not_a_crash():
    class _RaisingClient:
        def get(self, url, headers=None, timeout=None):
            raise httpx.ConnectError("connection refused")

    result = registry.verify_tag(_RaisingClient(), "llama3.1", "8b")

    assert result.status == "error"


def test_malformed_json_is_error_not_a_crash():
    class _BadJsonResponse:
        status_code = 200

        def json(self):
            raise ValueError("not json")

    result = registry.verify_tag(_client_returning(_BadJsonResponse()), "llama3.1", "8b")

    assert result.status == "error"


@pytest.mark.parametrize(
    ("size_bytes", "expected"),
    [
        (None, "unknown"),
        (0, "unknown"),
        (512, "512 B"),
        (2048, "2.0 KB"),
        (4_700_000_000, "4.4 GB"),
    ],
)
def test_format_size(size_bytes, expected):
    assert registry.format_size(size_bytes) == expected

import pytest

from app.config import resolve_secret_key, parse_origins


def test_secret_key_from_environment_is_used():
    assert resolve_secret_key("real-secret", "production") == "real-secret"


def test_missing_secret_key_in_production_raises():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        resolve_secret_key("", "production")


def test_missing_secret_key_in_dev_and_test_falls_back():
    assert resolve_secret_key("", "dev")
    assert resolve_secret_key("", "test")


def test_cors_origins_are_split_on_commas():
    assert parse_origins("http://a.test, http://b.test") == ["http://a.test", "http://b.test"]


def test_cors_allows_configured_origin(client):
    r = client.options("/health", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    })
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_rejects_unknown_origin(client):
    r = client.options("/health", headers={
        "Origin": "http://evil.test",
        "Access-Control-Request-Method": "GET",
    })
    assert "access-control-allow-origin" not in r.headers

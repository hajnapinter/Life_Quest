"""Regression tests for Supabase API error handling."""

import ast
import io
import json
from pathlib import Path
from unittest.mock import Mock
from urllib.error import HTTPError


def api_function(response):
    """Load api_request without starting the Streamlit application."""
    source = Path(__file__).resolve().parents[1] / "app.py"
    tree = ast.parse(source.read_text())
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "api_request"
    )

    scope = {
        "supabase_config": lambda: ("https://example.supabase.co", "test-key"),
        "json": json,
        "Request": Mock(),
        "urlopen": Mock(side_effect=response),
        "HTTPError": HTTPError,
        "URLError": __import__("urllib.error", fromlist=["URLError"]).URLError,
        "TimeoutError": TimeoutError,
        "auth_error_message": lambda code, status: "Authentication failed.",
    }

    exec(
        compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"),
        scope,
    )
    return scope["api_request"]


def http_error(body, status=400):
    """Build a simulated Supabase HTTP error."""
    return HTTPError(
        "https://example.supabase.co",
        status,
        "Bad Request",
        {},
        io.BytesIO(body),
    )


def test_malformed_http_error_returns_safe_message():
    api = api_function(http_error(b"not valid JSON"))

    data, error = api("GET", "/rest/v1/profiles")

    assert data is None
    assert error == "The Supabase request could not be completed. Please try again."


def test_unexpected_json_type_returns_safe_message():
    api = api_function(http_error(b'["unexpected", "response"]'))

    data, error = api("GET", "/rest/v1/profiles")

    assert data is None
    assert error == "The Supabase request could not be completed. Please try again."


def test_database_details_are_not_exposed():
    api = api_function(
        http_error(b'{"message":"internal database details"}', 500)
    )

    data, error = api("GET", "/rest/v1/profiles")

    assert data is None
    assert "internal database details" not in error


def test_invalid_invitation_code_has_friendly_message():
    api = api_function(
        http_error(b'{"msg":"That invite code is not valid."}')
    )

    data, error = api(
        "POST",
        "/rest/v1/rpc/join_squad",
        {"invite_code_input": "NOPE99"},
    )

    assert data is None
    assert error == "That invite code is not valid."

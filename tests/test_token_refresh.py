"""Tests for Supabase session token refreshing."""

import ast
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


class SessionState(dict):
    """Simulate Streamlit session state with attribute access."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self[name] = value


def refresh_function():
    """Load the refresh function without running the Streamlit app."""
    source = Path(__file__).resolve().parents[1] / "app.py"
    tree = ast.parse(source.read_text())

    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "refresh_access_token"
    ]

    assert len(functions) == 1

    state = SessionState(
        access_token="old-access",
        refresh_token="old-refresh",
        token_expires_at=100,
    )

    api_request = Mock()
    scope = {
        "st": SimpleNamespace(session_state=state),
        "api_request": api_request,
        "time": time,
    }

    module = ast.Module(body=functions, type_ignores=[])
    exec(compile(module, str(source), "exec"), scope)

    return scope["refresh_access_token"], state, api_request


def test_refresh_updates_tokens_and_expiration():
    refresh, state, api_request = refresh_function()

    api_request.return_value = (
        {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_in": 3600,
        },
        None,
    )

    before = time.time()

    assert refresh() is True
    assert state.access_token == "new-access"
    assert state.refresh_token == "new-refresh"
    assert before + 3600 <= state.token_expires_at <= time.time() + 3600

    api_request.assert_called_once_with(
        "POST",
        "/auth/v1/token?grant_type=refresh_token",
        {"refresh_token": "old-refresh"},
    )


def test_missing_refresh_token_does_not_call_api():
    refresh, state, api_request = refresh_function()

    state.refresh_token = None

    assert refresh() is False
    api_request.assert_not_called()


def test_invalid_refresh_response_preserves_tokens():
    refresh, state, api_request = refresh_function()

    api_request.return_value = ({"access_token": "incomplete"}, None)

    assert refresh() is False
    assert state.access_token == "old-access"
    assert state.refresh_token == "old-refresh"


def test_network_failure_preserves_tokens():
    refresh, state, api_request = refresh_function()

    api_request.return_value = (None, "Network unavailable")

    assert refresh() is False
    assert state.access_token == "old-access"
    assert state.refresh_token == "old-refresh"

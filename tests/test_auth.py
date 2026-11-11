import ast
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auth_helpers import auth_error_message, retry_seconds, valid_app_url, valid_email, verified_oauth_user


def test_email_validation():
    assert valid_email(' person@example.com ')
    for value in ('', 'bad', 'a@@b.com', 'a b@example.com'):
        assert not valid_email(value)


def test_cooldown_boundary():
    assert retry_seconds(100, 159.1) == 1
    assert retry_seconds(100, 160) == 0
    assert retry_seconds(0, 10) == 0


def test_redirect_requires_safe_url():
    for value in ('https://lifequest.example/', 'http://127.0.0.1:8502/', 'http://localhost:8502/'):
        assert valid_app_url(value)
    for value in ('javascript:alert(1)', 'http://evil.example/', 'https://u:p@example.com/', 'https://example.com/?token=x'):
        assert not valid_app_url(value)


def test_error_messages_cover_limits_and_unconfirmed():
    assert 'confirm' in auth_error_message('email_not_confirmed')
    assert 'sending limit' in auth_error_message('over_email_send_rate_limit')
    assert 'email service' in auth_error_message('email_address_not_authorized')
    assert 'Too many' in auth_error_message('unknown', 429)


def test_google_identity_checked_with_server():
    request = Mock(return_value=({'id': 'verified-user'}, None))
    assert verified_oauth_user('token', request) == {'id': 'verified-user'}
    request.assert_called_once_with('GET', '/auth/v1/user', access_token='token')
    for response in ((None, 'expired'), ({}, None), ({'id': 'forged'}, 'invalid')):
        assert verified_oauth_user('bad', Mock(return_value=response)) is None


def auth_functions():
    """Load auth actions without rendering the app or contacting Supabase."""
    tree = ast.parse((Path(__file__).resolve().parents[1] / 'app.py').read_text())
    names = {'auth_notice', 'email_cooldown', 'resend_confirmation', 'authenticate'}
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    attempts, lock = {}, threading.Lock()
    state = SimpleNamespace(auth_message=None, auth_message_kind='info', access_token=None,
                            user=None, profile=None, confirmation_email='')
    scope = dict(st=SimpleNamespace(session_state=state, rerun=Mock()), hashlib=hashlib,
                 time=time, email_attempts=lambda: (attempts, lock), retry_seconds=retry_seconds,
                 valid_email=valid_email, confirmation_path=lambda s: s, api_request=Mock(return_value=({}, None)))
    exec(compile(ast.Module(body=funcs, type_ignores=[]), 'auth_actions', 'exec'), scope)
    return scope, state


def test_resend_invalid_email_never_calls_api():
    scope, state = auth_functions()
    scope['resend_confirmation']('invalid')
    scope['api_request'].assert_not_called()
    assert state.auth_message_kind == 'error'


def test_resend_payload_and_double_click_guard():
    scope, state = auth_functions()
    scope['resend_confirmation'](' person@example.com ')
    scope['api_request'].assert_called_once_with('POST', '/auth/v1/resend', {'type': 'signup', 'email': 'person@example.com'})
    assert 'If this address' in state.auth_message
    scope['resend_confirmation']('PERSON@example.com')
    assert scope['api_request'].call_count == 1
    assert state.auth_message_kind == 'warning'


def test_resend_server_error_not_reported_as_delivery():
    scope, state = auth_functions()
    scope['api_request'].return_value = (None, 'Sending limit reached')
    scope['resend_confirmation']('person@example.com')
    assert state.auth_message == 'Sending limit reached'
    assert state.auth_message_kind == 'error'
    assert state.access_token is None


def test_signup_and_resend_share_cooldown():
    scope, state = auth_functions()
    scope['authenticate']('person@example.com', 'password123', True)
    assert state.user is None
    assert 'Delivery is not yet confirmed' in state.auth_message
    scope['resend_confirmation']('person@example.com')
    assert scope['api_request'].call_count == 1


def test_successful_password_login_sets_session():
    scope, state = auth_functions()
    scope['api_request'].return_value = ({'access_token': 'session', 'user': {'id': 'user'}}, None)
    scope['authenticate']('person@example.com', 'password123', False)
    assert state.access_token == 'session'
    assert state.user == {'id': 'user'}
    scope['st'].rerun.assert_called_once()


def test_login_and_signup_pages_without_network(monkeypatch):
    from io import BytesIO
    from streamlit.testing.v1 import AppTest

    network = Mock(side_effect=lambda *a, **kw: BytesIO(b'{"external":{"google":false}}'))
    monkeypatch.setattr('urllib.request.urlopen', network)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=10)
    app.secrets['supabase'] = {'url': 'https://test.supabase.co', 'anon_key': 'test-public-key'}
    app.run()

    def button(label):
        return next(b for b in app.button if b.label == label)

    def field(label):
        return next(f for f in app.text_input if f.label == label)

    assert not app.exception
    assert button('Continue with Google').disabled
    assert button('Resend confirmation email')
    assert not any(f.label == 'Confirm password' for f in app.text_input)
    assert not any(b.label == 'Create account' for b in app.button)

    # Invalid login is rejected locally, without contacting authentication services.
    network.reset_mock()
    field('Email').set_value('bad')
    button('Log in').click().run()
    assert not app.exception
    assert any('valid email' in e.value for e in app.error)
    network.assert_not_called()

    # Account creation navigates to a separate form and clears the login error.
    button('Create a new account').click().run()
    assert not app.exception
    assert not app.error
    assert field('Confirm password')
    assert button('Continue with Google').disabled
    assert not any(b.label == 'Log in' for b in app.button)

    field('Email').set_value('person@example.com')
    field('Password').set_value('password123')
    field('Confirm password').set_value('different123')
    network.reset_mock()
    button('Create account').click().run()
    assert not app.exception
    assert any('Passwords do not match' in e.value for e in app.error)
    network.assert_not_called()

    field('Email').set_value('invalid')
    button('Create account').click().run()
    assert any('valid email' in e.value for e in app.error)
    network.assert_not_called()

    button('Back to log in').click().run()
    assert not app.exception
    assert not app.error
    assert button('Log in')
    assert not any(f.label == 'Confirm password' for f in app.text_input)

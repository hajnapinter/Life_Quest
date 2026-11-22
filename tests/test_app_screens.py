"""The app starts and rejects bad input on the login screen (Streamlit AppTest, no real Supabase)."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")
# A local address that refuses connections: the app must handle the failure, not crash.
OFFLINE = {"url": "http://127.0.0.1:9", "anon_key": "test-anon-key"}


def button(at, label):
    return next(b for b in at.button if b.label == label)


def start(secrets):
    at = AppTest.from_file(APP, default_timeout=30)
    at.secrets["supabase"] = secrets
    return at.run()


def test_missing_configuration_shows_a_clear_message():
    at = start({"url": "YOUR_SUPABASE_PROJECT_URL", "anon_key": "YOUR_SUPABASE_ANON_KEY"})
    assert not at.exception
    assert any("Supabase is not configured" in e.value for e in at.error)


def test_login_screen_renders_when_supabase_is_unreachable():
    at = start(OFFLINE)
    assert not at.exception
    assert at.title[0].value == "Welcome back"
    google = button(at, "Continue with Google")
    assert google.disabled  # Google sign-in is switched off, not broken, when Supabase can't be reached
    assert [t.label for t in at.text_input][:2] == ["Email", "Password"]


def test_login_rejects_an_invalid_email_without_calling_supabase():
    at = start(OFFLINE)
    at.text_input[0].input("not-an-email")
    at.text_input[1].input("secret123")
    button(at, "Log in").click().run()
    assert not at.exception
    assert any("valid email" in e.value for e in at.error)
    assert at.session_state.access_token is None


def test_login_rejects_an_empty_password():
    at = start(OFFLINE)
    at.text_input[0].input("ana@example.com")
    button(at, "Log in").click().run()
    assert any("valid email" in e.value for e in at.error)
    assert at.session_state.access_token is None


def test_signup_rejects_short_and_mismatched_passwords():
    at = AppTest.from_file(APP, default_timeout=30)
    at.secrets["supabase"] = OFFLINE
    at.query_params["auth"] = "signup"
    at.run()
    at.text_input[0].input("ana@example.com")
    at.text_input[1].input("short")
    at.text_input[2].input("short")
    button(at, "Create account").click().run()
    assert any("at least 8 characters" in e.value for e in at.error)

    at.text_input[1].input("longenough1")
    at.text_input[2].input("different22")
    button(at, "Create account").click().run()
    assert any("do not match" in e.value for e in at.error)
    assert at.session_state.access_token is None

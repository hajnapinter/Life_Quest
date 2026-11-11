"""Authentication rules, independent of Streamlit and external services."""
import math
import re
from urllib.parse import urlsplit


def valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value.strip()))


def retry_seconds(last_attempt: float, now: float, delay: int = 60) -> int:
    return max(0, math.ceil(last_attempt + delay - now)) if last_attempt else 0


def valid_app_url(value: str) -> bool:
    parts = urlsplit(value)
    return bool(parts.hostname and not parts.username and not parts.password
                and not parts.query and not parts.fragment
                and (parts.scheme == "https" or
                     (parts.scheme == "http" and parts.hostname in ("localhost", "127.0.0.1"))))


def auth_error_message(code: str, status: int = 400) -> str:
    messages = {
        "email_not_confirmed": "Please confirm your email before signing in. You can request a new confirmation below.",
        "invalid_credentials": "The email or password is incorrect. Please try again.",
        "email_address_not_authorized": "Email delivery is not enabled for this address yet. The app team needs to configure its email service.",
        "over_email_send_rate_limit": "The email service has reached its sending limit. Please try later; repeated requests will not speed up delivery.",
        "over_request_rate_limit": "Too many attempts. Please wait before trying again.",
        "email_address_invalid": "Please enter a valid email address.",
        "weak_password": "Choose a stronger password with at least 8 characters.",
        "signup_disabled": "New registrations are currently unavailable.",
        "provider_disabled": "Google sign-in is not available yet. Please use email and password.",
        "validation_failed": "Please check your email and password and try again.",
    }
    return messages.get(code, "Too many attempts. Please try again later." if status == 429 else
                        "Authentication could not be completed. Please try again. If it continues, contact the app team.")


def verified_oauth_user(token: str, request):
    """Never accept the user identity supplied by browser component data."""
    user, error = request("GET", "/auth/v1/user", access_token=token)
    if error or not isinstance(user, dict) or not user.get("id"):
        return None
    return user

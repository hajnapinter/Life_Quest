from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import time
import hashlib
import threading
from pathlib import Path

from auth_helpers import valid_email, retry_seconds, valid_app_url, auth_error_message, verified_oauth_user
import streamlit.components.v1 as components

from datetime import date, datetime, timedelta, timezone
from collections import Counter

import streamlit as st
from onboarding import render_onboarding
from ai_quest_ui import render_home, render_pillar, prepare_initial_quests, fetch_quests
from onboarding import PILLARS
from social_play import render_social


st.set_page_config(page_title="Life Quest", page_icon="🗺️", layout="centered")

st.markdown(
      """
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #243B2D;
    }

    h1, h2, h3 {
        color: #245C43;
    }

    /* Forest green buttons */
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"] {
        background-color: #245C43 !important;
        color: #FFFFFF !important;
        border: none;
        border-radius: 12px;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        border-color: #245C43;
        color: #245C43;
    }

    /* Mint statistics cards */
    div[data-testid="stMetric"] {
        background-color: #DFF7EA;
        padding: 14px;
        border-radius: 14px;
    }

    /* Mint sidebar */
    section[data-testid="stSidebar"] {
        background-color: #DFF7EA;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #245C43;
    }

    /* Forest green progress bar */
    div[data-testid="stProgress"] div[role="progressbar"] > div {
        background-color: #245C43 !important;
    }

    /* Forest green selected statistics controls */
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
        background-color: #245C43 !important;
        color: #FFFFFF !important;
    }

    /* Mint table borders */
    div[data-testid="stDataFrame"] {
        border: 1px solid #C7EEDC;
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def initialise_state() -> None:
    defaults = {
        "access_token": None,
        "user": None,
        "profile": None,
        "challenges": [],
        "completed_challenges": set(),
        "completion_dates": [],
        "leaderboard": [],
        "squad": [],
        "squad_invite_code": None,
        "squad_error": None,
        "auth_message": None,
        "auth_message_kind": "info",
        "confirmation_email": "",
        "handled_oauth_code": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def supabase_config() -> tuple[str, str] | None:
    try:
        config = st.secrets["supabase"]
        url = str(config["url"]).strip()
        anon_key = str(config["anon_key"]).strip()
    except (KeyError, FileNotFoundError):
        return None

    if not url or not anon_key or "YOUR_" in url or "YOUR_" in anon_key:
        return None
    return url.rstrip("/"), anon_key


def api_request(
    method: str,
    path: str,
    payload: dict | None = None,
    access_token: str | None = None,
) -> tuple[object | None, str | None]:
    config = supabase_config()
    if config is None:
        return None, "Supabase secrets are not configured."

    base_url, anon_key = config
    headers = {"apikey": anon_key, "Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(f"{base_url}{path}", data=body, headers=headers, method=method)

    try:
        with urlopen(request, timeout=15) as response:
            response_body = response.read().decode("utf-8")
            return (json.loads(response_body) if response_body else None), None
    except HTTPError as error:
        message = error.read().decode("utf-8")
        try:
            details = json.loads(message)
            message = details.get("msg") or details.get("message") or details.get("error_description") or message
        except json.JSONDecodeError:
            pass
        if path.startswith("/auth/"):
            code = details.get("error_code", details.get("code", "")) if isinstance(locals().get("details"), dict) else ""
            message = auth_error_message(code, error.code)
        return None, message
    except (URLError, TimeoutError):
        return None, "The Supabase service could not be reached. Check your internet connection."


def auth_notice(message: str, kind: str = "info") -> None:
    st.session_state.auth_message = message
    st.session_state.auth_message_kind = kind


@st.cache_resource
def email_attempts():
    # Shared across browser sessions on this server; Supabase enforces global limits.
    return {}, threading.Lock()


def email_cooldown(email: str, reserve: bool = False) -> int:
    attempts, lock = email_attempts()
    key = hashlib.sha256(email.strip().lower().encode()).hexdigest()
    now = time.time()
    with lock:
        for old_key in list(attempts):
            if now - attempts[old_key] >= 3600:
                del attempts[old_key]
        remaining = retry_seconds(attempts.get(key, 0), now)
        if reserve and not remaining:
            attempts[key] = now
        return remaining


def app_redirect_url() -> str | None:
    try:
        value = json.loads((Path(__file__).parent / "auth_config.json").read_text())["app_url"]
        return value if isinstance(value, str) and valid_app_url(value) else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def confirmation_path(endpoint: str) -> str:
    redirect = app_redirect_url()
    return endpoint + ("?" + urlencode({"redirect_to": redirect}) if redirect else "")


def authenticate(email: str, password: str, sign_up: bool) -> None:
    email = email.strip()
    if sign_up:
        remaining = email_cooldown(email, reserve=True)
        if remaining:
            auth_notice(f"Please wait {remaining} seconds before requesting another confirmation.", "warning")
            return
        st.session_state.confirmation_email = email
        data, error = api_request("POST", confirmation_path("/auth/v1/signup"), {"email": email, "password": password})
    else:
        data, error = api_request("POST", "/auth/v1/token?grant_type=password", {"email": email, "password": password})
    if error:
        st.session_state.confirmation_email = email
        auth_notice(error, "error")
        return
    if isinstance(data, dict) and data.get("access_token") and data.get("user"):
        st.session_state.access_token = data["access_token"]
        st.session_state.user = data["user"]
        st.session_state.profile = None
        st.session_state.auth_message = None
        st.rerun()
    elif sign_up:
        auth_notice("Registration request accepted. If this address needs confirmation, check your inbox and spam folder. Delivery is not yet confirmed. After confirming, return here and log in.")
    else:
        auth_notice("Sign-in could not be completed. Please try again.", "error")


def resend_confirmation(email: str) -> None:
    email = email.strip()
    if not valid_email(email):
        auth_notice("Enter a valid email address to request a confirmation.", "error")
        return
    remaining = email_cooldown(email, reserve=True)
    if remaining:
        auth_notice(f"Please wait {remaining} seconds before trying again.", "warning")
        return
    _, error = api_request("POST", confirmation_path("/auth/v1/resend"), {"type": "signup", "email": email})
    if error:
        auth_notice(error, "error")
    else:
        auth_notice("Request accepted. If this address has an unconfirmed account, a new confirmation email will be requested. Check your inbox and spam folder; delivery is not guaranteed by this message.")


@st.fragment(run_every="1s")
def render_confirmation_help() -> None:
    with st.expander("Didn't receive a confirmation email?", expanded=bool(st.session_state.confirmation_email)):
        email = st.text_input("Confirmation email address", key="confirmation_email")
        remaining = email_cooldown(email) if valid_email(email) else 0
        label = f"Try again in {remaining}s" if remaining else "Resend confirmation email"
        if st.button(label, disabled=bool(remaining), key="resend_confirmation"):
            resend_confirmation(email)
            st.rerun()
        st.caption("Check spam and your organisation's email quarantine. Repeated requests do not make delivery faster. Already confirmed? Use Log in above.")


_google_component = components.declare_component("lifequest_google", path=str(Path(__file__).parent / "auth_component"))


@st.cache_data(ttl=60, show_spinner=False)
def google_available(base_url: str) -> bool:
    settings, error = api_request("GET", "/auth/v1/settings")
    return not error and isinstance(settings, dict) and settings.get("external", {}).get("google") is True


def render_google_login() -> None:
    config = supabase_config()
    redirect = app_redirect_url()
    code = st.query_params.get("code")
    if st.query_params.get("error"):
        auth_notice("Google sign-in was cancelled or could not be completed. Please try again.", "warning")
        for key in ("error", "error_description", "error_code"):
            if key in st.query_params:
                del st.query_params[key]
    enabled = bool(config and redirect and google_available(config[0]))
    if not enabled and not code:
        st.button("Continue with Google", disabled=True)
        st.caption("Google sign-in is not available yet. Please use email and password.")
        return
    if not config or not redirect:
        auth_notice("Google sign-in is not configured for this app address.", "error")
        return
    result = _google_component(supabase_url=config[0], public_key=config[1],
                               redirect_url=redirect, enabled=enabled, code=code, key="google_login")
    if not isinstance(result, dict) or not code or result.get("code") != code:
        return
    if st.session_state.handled_oauth_code == code:
        return
    st.session_state.handled_oauth_code = code
    if "code" in st.query_params:
        del st.query_params["code"]
    token = result.get("access_token")
    if not isinstance(token, str) or not token:
        auth_notice("Google sign-in could not be completed. Start again in the same browser.", "error")
        return
    user = verified_oauth_user(token, api_request)
    if user is None:
        auth_notice("Google sign-in could not be verified. Please try again.", "error")
        return
    st.session_state.access_token = token
    st.session_state.user = user
    st.session_state.profile = None
    st.session_state.auth_message = None
    st.rerun()


def navigate_auth(page: str) -> None:
    st.query_params["auth"] = page
    st.session_state.auth_message = None
    st.rerun()


def render_auth() -> None:
    signing_up = st.query_params.get("auth") == "signup"
    st.title("🌱 Create your Life Quest account" if signing_up else "🌱 Welcome to Life Quest")
    st.subheader("Your adventure starts here" if signing_up else "Turn your everyday life into an adventure")
    st.write("Build better habits, discover new experiences, and grow through small daily challenges. Complete quests, earn points, and level up with friends.")
    render_google_login()
    st.divider()
    st.caption("Or create an account with email" if signing_up else "Or log in with email")
    with st.form("signup_form" if signing_up else "login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password",
                                 help="Use at least 8 characters." if signing_up else None)
        confirmation = st.text_input("Confirm password", type="password") if signing_up else None
        submitted = st.form_submit_button("Create account" if signing_up else "Log in", type="primary")
    if submitted:
        if not valid_email(email) or not password:
            auth_notice("Enter a valid email address and your password.", "error")
        elif signing_up and len(password) < 8:
            auth_notice("Choose a password with at least 8 characters.", "error")
        elif signing_up and password != confirmation:
            auth_notice("Passwords do not match. Please enter the same password in both fields.", "error")
        else:
            authenticate(email, password, signing_up)
    if st.session_state.auth_message:
        getattr(st, st.session_state.auth_message_kind)(st.session_state.auth_message)
    if signing_up:
        st.caption("Already have an account?")
        if st.button("Back to log in"):
            navigate_auth("login")
    else:
        st.caption("New to Life Quest?")
        if st.button("Create a new account"):
            navigate_auth("signup")
    render_confirmation_help()


def load_user_data() -> bool:
    token = st.session_state.access_token
    user_id = st.session_state.user["id"]
    profile_query = urlencode({"select": "*", "id": f"eq.{user_id}"})
    profiles, error = api_request("GET", f"/rest/v1/profiles?{profile_query}", access_token=token)
    if error:
        st.error(error)
        return False
    st.session_state.profile = profiles[0] if profiles else None

    challenge_query = urlencode({"select": "*", "is_active": "eq.true", "order": "id"})
    challenges, error = api_request("GET", f"/rest/v1/challenges?{challenge_query}", access_token=token)
    if error:
        st.error(error)
        return False
    st.session_state.challenges = challenges or []

    completed_query = urlencode({"select": "challenge_id,completed_at:created_at", "user_id": f"eq.{user_id}"})
    completed, error = api_request("GET", f"/rest/v1/completed_challenges?{completed_query}", access_token=token)
    if error:
        st.error(error)
        return False
    st.session_state.legacy_completions = completed or []
    st.session_state.completed_challenges = {row["challenge_id"] for row in completed or []}
    st.session_state.completion_dates = [row["completed_at"] for row in completed or [] if row.get("completed_at")]
    ai_rows, ai_error = fetch_quests(api_request)
    st.session_state.ai_completed_count = 0
    if not ai_error:
        finished = [q for q in ai_rows if q["status"] == "completed"]
        st.session_state.ai_completed_count = len(finished)
        st.session_state.completion_dates.extend(q["completed_at"] for q in finished if q.get("completed_at"))

    leaderboard, error = api_request(
        "POST", "/rest/v1/rpc/get_weekly_leaderboard", {}, access_token=token
    )
    if error:
        st.error(error)
        return False
    st.session_state.leaderboard = leaderboard or []

    squad, error = api_request("POST", "/rest/v1/rpc/get_my_squad", {}, access_token=token)
    st.session_state.squad_error = error
    st.session_state.squad = squad or [] if not error else []
    if st.session_state.squad:
        st.session_state.squad_invite_code = st.session_state.squad[0].get("invite_code")
    return True


def save_onboarding(nickname: str, location: str, categories: list[str], levels: dict) -> bool:
    token = st.session_state.access_token
    answers = {"version": 1, "nickname": nickname, "categories": categories,
               "levels": levels, "completed": True}
    user, error = api_request("PUT", "/auth/v1/user", {"data": {"lifequest_onboarding": answers}}, token)
    if error:
        st.error("We couldn’t save your answers. " + error)
        return False
    if isinstance(user, dict) and user.get("id"):
        st.session_state.user = user
    profile = {"id": st.session_state.user["id"], "display_name": nickname,
               "location": location.strip(), "selected_categories": categories}
    data, error = api_request("POST", "/rest/v1/profiles", profile, token)
    if error:
        st.error("We couldn’t save your profile. " + error)
        return False
    st.session_state.profile = data[0] if isinstance(data, list) and data else profile
    notice = prepare_initial_quests(api_request)
    if notice:
        st.session_state.ai_notice = notice
    return True


def render_profile_setup() -> None:
    render_onboarding(save_onboarding)


def complete_challenge(challenge_id: int) -> None:
    data, error = api_request(
        "POST",
        "/rest/v1/rpc/complete_challenge",
        {"challenge_id_input": challenge_id},
        st.session_state.access_token,
    )
    if error:
        st.error(error)
        return
    if isinstance(data, list) and data:
        st.session_state.profile["points"] = data[0]["new_points"]
    st.session_state.completed_challenges.add(challenge_id)
    st.rerun()


def create_squad(name: str) -> None:
    data, error = api_request(
        "POST",
        "/rest/v1/rpc/create_squad",
        {"squad_name_input": name.strip()},
        st.session_state.access_token,
    )
    if error:
        st.error(error)
        return
    if isinstance(data, list) and data:
        st.session_state.squad_invite_code = data[0]["invite_code"]
    load_user_data()
    st.rerun()


def join_squad(invite_code: str) -> None:
    data, error = api_request(
        "POST",
        "/rest/v1/rpc/join_squad",
        {"invite_code_input": invite_code.strip().upper()},
        st.session_state.access_token,
    )
    if error:
        st.error(error)
        return
    load_user_data()
    st.rerun()


def render_squad() -> None:
    render_social(api_request)


def calculate_statistics(completion_dates: list[str]) -> tuple[int, int, list[int]]:
    days = []

    for value in completion_dates:
        completed_day = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).date()
        days.append(completed_day)

    today = datetime.now(timezone.utc).date()
    completed_days = set(days)

    streak = 0
    current_day = today

    # Keep yesterday's streak if no quest was completed today.
    if current_day not in completed_days:
        current_day -= timedelta(days=1)

    while current_day in completed_days:
        streak += 1
        current_day -= timedelta(days=1)

    weekly_counts = [
        days.count(today - timedelta(days=offset))
        for offset in range(6, -1, -1)
    ]

    return len(days), streak, weekly_counts
TRANSLATIONS = {
    "en": {
        "profile": "Your profile",
        "home": "Home",
        "squad": "Squad",
        "leaderboard": "Leaderboard",
        "settings": "Settings",
        "language": "🌍 Language",
        "choose": "Choose your language",
        "notifications": "Notifications",
        "reminders": "Daily email reminders",
        "logout": "Log out",
    },
    "pt": {
        "profile": "O teu perfil",
        "home": "Início",
        "squad": "Equipa",
        "leaderboard": "Classificação",
        "settings": "Definições",
        "language": "🌍 Idioma",
        "choose": "Escolhe o teu idioma",
        "notifications": "Notificações",
        "reminders": "Lembretes diários por email",
        "logout": "Terminar sessão",
    },
    "fr": {
        "profile": "Ton profil",
        "home": "Accueil",
        "squad": "Équipe",
        "leaderboard": "Classement",
        "settings": "Paramètres",
        "language": "🌍 Langue",
        "choose": "Choisis ta langue",
        "notifications": "Notifications",
        "reminders": "Rappels quotidiens par e-mail",
        "logout": "Se déconnecter",
    },
    "de": {
        "profile": "Dein Profil",
        "home": "Startseite",
        "squad": "Team",
        "leaderboard": "Rangliste",
        "settings": "Einstellungen",
        "language": "🌍 Sprache",
        "choose": "Wähle deine Sprache",
        "notifications": "Benachrichtigungen",
        "reminders": "Tägliche E-Mail-Erinnerungen",
        "logout": "Abmelden",
    },
}


def t(key):
    language = st.session_state.get("language", "en")
    return TRANSLATIONS.get(language, TRANSLATIONS["en"]).get(key, key)

def render_settings() -> None:
    profile = st.session_state.profile
    lang = st.session_state.get("language", "en")

    translations = {
        "en": {
            "profile": "Your profile",
            "notifications": "Notifications",
            "reminders": "Daily email reminders",
            "save_error": "We couldn't save your notification setting. Please try again.",
            "privacy": "Your selected pillars, starting levels and quest feedback personalise your quests.",
            "ai_privacy": "AI requests go through Requesty and its free model provider; your name and email are not sent.",
            "next": "Your next chapter starts here",
        },
        "pt": {
            "profile": "O teu perfil",
            "notifications": "Notificações",
            "reminders": "Lembretes diários por email",
            "save_error": "Não foi possível guardar as definições. Tenta novamente.",
            "privacy": "As áreas escolhidas, os níveis iniciais e o teu feedback personalizam as missões.",
            "ai_privacy": "Os pedidos de IA passam pelo Requesty e pelo seu fornecedor de modelo gratuito; o teu nome e email não são enviados.",
            "next": "O teu próximo capítulo começa aqui",
        },
        "fr": {
            "profile": "Ton profil",
            "notifications": "Notifications",
            "reminders": "Rappels quotidiens par e-mail",
            "save_error": "Impossible d'enregistrer ce paramètre. Réessaie.",
            "privacy": "Tes domaines choisis, tes niveaux de départ et tes commentaires personnalisent tes quêtes.",
            "ai_privacy": "Les demandes d'IA passent par Requesty et son fournisseur de modèle gratuit ; ton nom et ton e-mail ne sont pas envoyés.",
            "next": "Ton prochain chapitre commence ici",
        },
        "de": {
            "profile": "Dein Profil",
            "notifications": "Benachrichtigungen",
            "reminders": "Tägliche E-Mail-Erinnerungen",
            "save_error": "Deine Einstellung konnte nicht gespeichert werden. Bitte versuche es erneut.",
            "privacy": "Deine ausgewählten Bereiche, Startlevel und dein Feedback personalisieren deine Quests.",
            "ai_privacy": "KI-Anfragen laufen über Requesty und dessen kostenlosen Modellanbieter; dein Name und deine E-Mail werden nicht gesendet.",
            "next": "Dein nächstes Kapitel beginnt hier",
        },
    }

    text = translations.get(lang, translations["en"])

    st.title(text["profile"])
    st.write(f"**{profile.get('display_name', 'Quest explorer')}**")
    st.caption(
        f"{profile.get('points', 0)} XP · "
        f"{profile.get('location') or text['next']}"
    )

    st.divider()
    st.subheader(text["notifications"])

    reminders = st.toggle(
        text["reminders"],
        value=bool(profile.get("email_reminders", False))
    )

    if reminders != bool(profile.get("email_reminders", False)):
        query = urlencode({"id": f"eq.{st.session_state.user['id']}"})
        _, error = api_request(
            "PATCH",
            f"/rest/v1/profiles?{query}",
            {"email_reminders": reminders},
            st.session_state.access_token
        )

        if error:
            st.error(text["save_error"])
        else:
            profile["email_reminders"] = reminders

    st.caption(text["privacy"] + " " + text["ai_privacy"])

    if st.button(t("logout")):
        st.session_state.clear()
        st.rerun()


def render_dashboard() -> None:
    profile = st.session_state.profile
    col_profile, col_language = st.columns([3, 1])

    with col_profile:
        st.write(f"👤 {profile.get('display_name', 'Quest explorer')}")

    with col_language:
        languages = {
            "🇬🇧 English": "en",
            "🇵🇹 Português": "pt",
            "🇫🇷 Français": "fr",
            "🇩🇪 Deutsch": "de",
        }

        current_language = st.session_state.get("language", "en")

        selected_language = st.selectbox(
            "🌍",
            options=list(languages),
            index=list(languages.values()).index(current_language),
            key="header_language",
        )

        if languages[selected_language] != current_language:
            st.session_state.language = languages[selected_language]
            st.rerun()
    categories = [c for c in profile.get("selected_categories", []) if c in PILLARS]
    pillar_pages = {f"{PILLARS[c][0]} {c}": c for c in categories}
    pages = ["🏠 Home", *pillar_pages, "👥 Squad", "🏆 Leaderboard", "⚙️ Settings"]
    def nav_label(item):
        labels = {
            "🏠 Home": t("home"),
            "👥 Squad": t("squad"),
            "🏆 Leaderboard": t("leaderboard"),
            "⚙️ Settings": t("settings"),
        }

        language = st.session_state.get("language", "en")
        if "Finance" in item:
            return item.replace("Finance", {
                "en": "Finance",
                "pt": "Finanças",
                "fr": "Finances",
                "de": "Finanzen",
            }.get(language, "Finance"))
        if "Adventure" in item:
            return item.replace("Adventure", {
                "en": "Adventure",
                "pt": "Aventura",
                "fr": "Aventure",
                "de": "Abenteuer",
            }.get(language, "Adventure"))
        if "Social" in item:
            return item.replace("Social", {
                "en": "Social",
                "pt": "Vida Social",
                "fr": "Vie sociale",
                "de": "Soziales",
            }.get(language, "Social"))
        if "Personal Growth" in item:
            return item.replace("Personal Growth", {
                "en": "Personal Growth",
                "pt": "Desenvolvimento Pessoal",
                "fr": "Développement personnel",
                "de": "Persönliche Entwicklung",
            }.get(language, "Personal Growth"))
        if "Languages" in item:
            return item.replace("Languages", {
                "en": "Languages",
                "pt": "Idiomas",
                "fr": "Langues",
                "de": "Sprachen",
            }.get(language, "Languages"))
        if "Health" in item:
            return item.replace("Health", {
                "en": "Health",
                "pt": "Saúde",
                "fr": "Santé",
                "de": "Gesundheit",
            }.get(language, "Health"))

        return labels.get(item, item.replace("Fitness", {
            "en": "Fitness",
            "pt": "Exercício",
            "fr": "Sport",
            "de": "Fitness",
        }.get(language, "Fitness")))
    if st.session_state.get("current_page") not in pages:
        st.session_state.current_page = "🏠 Home"
    st.markdown("""
    <style>
    .stMainBlockContainer {max-width:900px;padding-top:5rem;padding-bottom:115px;}
    .st-key-bottom_navigation [role="radiogroup"] {display:flex;flex-wrap:nowrap!important;
       gap:10px;overflow-x:auto;scrollbar-width:thin;padding:3px 0;}
    .st-key-bottom_navigation [role="radiogroup"] label {white-space:nowrap;border-radius:15px;
       padding:9px 13px;margin:0;background:#f3f8f4;border:1px solid #e0ebe3;}
    .st-key-bottom_navigation [role="radiogroup"] label:has(input:checked) {background:#dff2e6;border-color:#245c43;}
    .st-key-bottom_navigation [data-testid="stRadioOption"]>div>div:first-child {display:none!important;}
    .st-key-bottom_navigation [data-testid="stRadioOption"][data-selected="true"] {background:#dff2e6;border-color:#245c43;}
    .st-key-bottom_navigation [data-testid="stRadioOption"]>div {gap:0!important;}
    div[data-testid="stVerticalBlockBorderWrapper"] {border-radius:20px;}
    div.stButton>button {border-radius:12px;min-height:42px;}
    </style>""", unsafe_allow_html=True)
    with st.container(key="bottom_navigation"):
       page = st.radio("Explore Life Quest", pages, key="current_page", horizontal=True, label_visibility="collapsed", format_func=nav_label)
    if page == "🏠 Home":
        render_home(api_request)
    elif page in pillar_pages:
        render_pillar(api_request, pillar_pages[page])
    elif page == "👥 Squad":
        render_squad()
    elif page == "⚙️ Settings":
        render_settings()
    elif page == "🏆 Leaderboard":
        st.title({
            "en": "Weekly leaderboard",
            "pt": "Classificação semanal",
            "fr": "Classement hebdomadaire",
            "de": "Wöchentliche Rangliste",
        }.get(st.session_state.get("language", "en")))

        st.caption({
            "en": "XP earned since the start of this week",
            "pt": "XP ganhos desde o início desta semana",
            "fr": "XP gagnés depuis le début de cette semaine",
            "de": "Seit Beginn dieser Woche verdiente XP",
        }.get(st.session_state.get("language", "en")))

        leaderboard, error = api_request(
            "POST",
            "/rest/v1/rpc/get_weekly_leaderboard",
            {},
            st.session_state.access_token
        )

        if error:
            st.error({
                "en": "The leaderboard could not be loaded. Please try again.",
                "pt": "Não foi possível carregar a classificação. Tenta novamente.",
                "fr": "Impossible de charger le classement. Réessaie.",
                "de": "Die Rangliste konnte nicht geladen werden. Bitte versuche es erneut.",
            }.get(st.session_state.get("language", "en")))

        elif leaderboard:
            lang = st.session_state.get("language", "en")
            labels = {
                "en": ["Rank", "Player", "XP", "Quests"],
                "pt": ["Posição", "Jogador", "XP", "Missões"],
                "fr": ["Rang", "Joueur", "XP", "Quêtes"],
                "de": ["Rang", "Spieler", "XP", "Quests"],
            }
            headers = labels.get(lang, labels["en"])

            st.dataframe(
                [
                    {
                        headers[0]: i,
                        headers[1]: row["display_name"],
                        headers[2]: row["weekly_points"],
                        headers[3]: row["quests_completed"],
                    }
                    for i, row in enumerate(leaderboard, 1)
                ],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info({
                "en": "Complete a quest to appear on this week's leaderboard.",
                "pt": "Conclui uma missão para aparecer na classificação desta semana.",
                "fr": "Termine une quête pour apparaître dans le classement de cette semaine.",
                "de": "Schließe eine Quest ab, um in der Rangliste dieser Woche zu erscheinen.",
            }.get(st.session_state.get("language", "en")))
        
initialise_state()

if supabase_config() is None:
    st.error("Supabase is not configured for this deployment.")
    st.info(
        "The person who manages the Streamlit deployment must add the existing "
        "Supabase Project URL and anon key as deployment secrets under "
        "[supabase]. Local files named .streamlit/secrets.toml are not uploaded "
        "automatically."
    )
    st.stop()

if not st.session_state.access_token:
    render_auth()
elif st.session_state.profile is None:
    if load_user_data():
        if st.session_state.profile is None:
            render_profile_setup()
        else:
            render_dashboard()
else:
    render_dashboard()

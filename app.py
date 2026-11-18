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
from ai_quest_ui import render_home, render_pillar, prepare_initial_quests, fetch_quests, quests_shown, category_name
from onboarding import PILLARS
from social_play import render_social
from design import apply_styles, brand, hero, profile_card, splash
from places import city_picker, clear_city_picker
from pro import pillar_limit, render_pro_card, is_pro
from account import photo as account_photo, ring as account_ring, render_photo_setting, render_push_setting


st.set_page_config(page_title="Life Quest", page_icon="🌱", layout="centered")
apply_styles()
if not st.session_state.get("splash_shown"):
    # Animated loading screen on the first load of each browser session.
    splash()
    st.session_state.splash_shown = True

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
    # The deployment sets [app] url = "https://…" in its Secrets; local runs use auth_config.json.
    try:
        deployed = st.secrets.get("app", {}).get("url")
    except (FileNotFoundError, AttributeError, KeyError):
        deployed = None
    if isinstance(deployed, str) and valid_app_url(deployed):
        return deployed
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
    brand()
    st.title("Create your account" if signing_up else "Welcome back")
    hero(
        "Your adventure starts here" if signing_up else "A little better, every day",
        "Turn everyday life into an adventure",
        "Small daily quests, real progress, and friends to cheer you on.",
    )
    render_google_login()
    st.caption("Or create an account with email" if signing_up else "Or log in with email")
    with st.form("signup_form" if signing_up else "login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password",
                                 help="Use at least 8 characters." if signing_up else None)
        confirmation = st.text_input("Confirm password", type="password") if signing_up else None
        submitted = st.form_submit_button("Create account" if signing_up else "Log in", type="primary", width="stretch")
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


def save_onboarding(nickname: str, location: str, categories: list[str], levels: dict, quests_shown: dict | None = None) -> bool:
    token = st.session_state.access_token
    answers = {"version": 1, "nickname": nickname, "categories": categories,
               "levels": levels, "quests_shown": quests_shown or {}, "completed": True}
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

def update_profile(fields: dict) -> bool:
    """PATCH the user's own profile row and mirror the change in session state."""
    query = urlencode({"id": f"eq.{st.session_state.user['id']}"})
    _, error = api_request("PATCH", f"/rest/v1/profiles?{query}", fields, st.session_state.access_token)
    if error:
        return False
    st.session_state.profile.update(fields)
    return True


def render_pillars_setting(lang: str) -> None:
    """Add or remove pillars. Free: up to 3 (accounts that already had more keep them); Pro: all 7."""
    labels = {
        "en": ("Your pillars", "Save pillars", "Free plan: up to {n} pillars. Pro unlocks all 7.", "Pillars saved. New quests are being prepared.", "Keep at least one pillar.", "We couldn't save your pillars. Please try again."),
        "pt": ("As tuas áreas", "Guardar áreas", "Plano gratuito: até {n} áreas. O Pro desbloqueia as 7.", "Áreas guardadas. Estamos a preparar novas missões.", "Mantém pelo menos uma área.", "Não foi possível guardar as áreas. Tenta novamente."),
        "fr": ("Tes domaines", "Enregistrer", "Offre gratuite : {n} domaines maximum. Pro débloque les 7.", "Domaines enregistrés. De nouvelles quêtes se préparent.", "Garde au moins un domaine.", "Impossible d'enregistrer tes domaines. Réessaie."),
        "de": ("Deine Bereiche", "Bereiche speichern", "Kostenlos: bis zu {n} Bereiche. Pro schaltet alle 7 frei.", "Bereiche gespeichert. Neue Quests werden vorbereitet.", "Behalte mindestens einen Bereich.", "Deine Bereiche konnten nicht gespeichert werden. Bitte versuche es erneut."),
    }
    title, save_label, limit_note, saved, need_one, failed = labels.get(lang, labels["en"])
    if st.session_state.get("pillars_toast"):
        st.toast(st.session_state.pop("pillars_toast"), icon="🌱")
    st.subheader(title)
    current = [c for c in st.session_state.profile.get("selected_categories", []) if c in PILLARS]
    limit = pillar_limit(len(current))
    chosen = st.multiselect(title, list(PILLARS), default=current, max_selections=limit, key="pillars_setting",
                            format_func=lambda c: f"{PILLARS[c][0]} {category_name(c)}", label_visibility="collapsed")
    if limit < len(PILLARS):
        st.caption("✨ " + limit_note.format(n=limit))
    if st.button(save_label, key="pillars_save", disabled=sorted(chosen) == sorted(current)):
        if not chosen:
            st.error(need_one)
        elif update_profile({"selected_categories": chosen}):
            st.session_state.pillars_toast = saved
            st.rerun()
        else:
            st.error(failed)


def render_city_setting(lang: str) -> None:
    labels = {
        "en": ("Change city", "Your city", "City saved.", "We couldn't save your city. Please try again.",
               "Start typing your city, for example Lisbon", "No matching city found. Check the spelling.",
               "City search is unavailable right now. Please try again later."),
        "pt": ("Mudar cidade", "A tua cidade", "Cidade guardada.", "Não foi possível guardar a cidade. Tenta novamente.",
               "Começa a escrever a tua cidade, por exemplo Lisboa", "Nenhuma cidade encontrada. Verifica a ortografia.",
               "A pesquisa de cidades não está disponível agora. Tenta mais tarde."),
        "fr": ("Changer de ville", "Ta ville", "Ville enregistrée.", "Impossible d'enregistrer ta ville. Réessaie.",
               "Commence à écrire ta ville, par exemple Lisbonne", "Aucune ville trouvée. Vérifie l'orthographe.",
               "La recherche de villes est indisponible pour le moment. Réessaie plus tard."),
        "de": ("Stadt ändern", "Deine Stadt", "Stadt gespeichert.", "Deine Stadt konnte nicht gespeichert werden. Bitte versuche es erneut.",
               "Gib deine Stadt ein, zum Beispiel Lissabon", "Keine passende Stadt gefunden. Prüfe die Schreibweise.",
               "Die Städtesuche ist gerade nicht verfügbar. Bitte versuche es später erneut."),
    }
    title, field, saved, failed, placeholder, none_found, unavailable = labels.get(lang, labels["en"])
    if st.session_state.get("city_toast"):
        st.toast(st.session_state.pop("city_toast"), icon="📍")
    with st.expander("📍 " + title):
        place = city_picker("settings_city", "", label=field, placeholder=placeholder,
                            none_found=none_found, unavailable=unavailable)
        if place:
            if update_profile({"location": place["label"]}):
                clear_city_picker("settings_city")  # otherwise the same city is saved again on every rerun
                st.session_state.city_toast = saved
                st.rerun()
            else:
                st.error(failed)


def render_quests_shown_setting(lang: str) -> None:
    """Per pillar: how many of the five ready quests to show (saved with the onboarding answers)."""
    labels = {
        "en": ("Quests per pillar", "How many quests to show at once. A new one appears whenever you finish one.", "Saved.", "We couldn't save this. Please try again."),
        "pt": ("Missões por área", "Quantas missões mostrar de cada vez. Aparece uma nova sempre que concluis uma.", "Guardado.", "Não foi possível guardar. Tenta novamente."),
        "fr": ("Quêtes par domaine", "Combien de quêtes afficher à la fois. Une nouvelle apparaît à chaque quête terminée.", "Enregistré.", "Impossible d'enregistrer. Réessaie."),
        "de": ("Quests pro Bereich", "Wie viele Quests gleichzeitig angezeigt werden. Nach jedem Abschluss erscheint eine neue.", "Gespeichert.", "Konnte nicht gespeichert werden. Bitte versuche es erneut."),
    }
    title, help_text, saved, failed = labels.get(lang, labels["en"])
    if st.session_state.get("shown_toast"):
        st.toast(st.session_state.pop("shown_toast"), icon="👀")
    st.subheader(title)
    st.caption(help_text)
    categories = [c for c in st.session_state.profile.get("selected_categories", []) if c in PILLARS]
    for category in categories:
        current = quests_shown(category)
        # One compact row per pillar: name on the left, 1-5 on the right.
        name_col, pick_col = st.columns([1, 1], vertical_alignment="center")
        name_col.markdown(f"**{PILLARS[category][0]} {category_name(category)}**")
        with pick_col:
            choice = st.segmented_control(
                f"{PILLARS[category][0]} {category_name(category)}", [1, 2, 3, 4, 5],
                default=current, key="shown_" + category, label_visibility="collapsed",
            )
        if choice is None or choice == current:
            continue
        answers = dict(st.session_state.user.get("user_metadata", {}).get("lifequest_onboarding", {}))
        answers["quests_shown"] = {**(answers.get("quests_shown") or {}), category: int(choice)}
        user, error = api_request("PUT", "/auth/v1/user", {"data": {"lifequest_onboarding": answers}},
                                  st.session_state.access_token)
        if error:
            st.error(failed)
            return
        if isinstance(user, dict) and user.get("id"):
            st.session_state.user = user
        else:
            st.session_state.user.setdefault("user_metadata", {})["lifequest_onboarding"] = answers
        st.session_state.shown_toast = saved
        st.rerun()


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

    st.markdown('<div class="lq-eyebrow">' + t("settings") + '</div>', unsafe_allow_html=True)
    st.title(text["profile"])
    left, right = st.columns(2, gap="large")
    with left, st.container(key="card_profile"):
        profile_card(
            profile.get('display_name', 'Quest explorer'),
            ("✨ Pro · " if is_pro() else "") + f"🌱 {profile.get('points', 0)} XP · {profile.get('location') or text['next']}",
            photo=account_photo(), ring=account_ring(),
        )
        render_photo_setting(api_request, lang)
        render_city_setting(lang)
        st.caption(text["privacy"] + " " + text["ai_privacy"])
    with left, st.container(key="card_pillars"):
        render_pillars_setting(lang)
    with left, st.container(key="card_quests_shown"):
        render_quests_shown_setting(lang)
    with right, st.container(key="card_pro"):
        render_pro_card(api_request, lang)
    with right, st.container(key="card_notifications"):
        st.subheader(text["notifications"])
        reminders = st.toggle(
            text["reminders"],
            value=bool(profile.get("email_reminders", False))
        )

        render_push_setting(api_request, lang)

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
        if st.button(t("logout"), width="stretch"):
            st.session_state.clear()
            st.rerun()


def render_dashboard() -> None:
    profile = st.session_state.profile
    col_profile, col_language = st.columns([3, 1], vertical_alignment="center")

    with col_profile:
        brand()

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
            label_visibility="collapsed",
        )

        if languages[selected_language] != current_language:
            st.session_state.language = languages[selected_language]
            st.rerun()
    categories = [c for c in profile.get("selected_categories", []) if c in PILLARS]
    pillar_pages = {f"{PILLARS[c][0]} {c}": c for c in categories}
    pages = ["🏠 Home", *pillar_pages, "👥 Squad", "⚙️ Settings"]
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

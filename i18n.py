import streamlit as st

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
    """Return translated text for the selected language, falling back to English."""
    language = st.session_state.get("language", "en")
    return TRANSLATIONS.get(
        language, TRANSLATIONS["en"]
    ).get(key, key)



LANGUAGES = {
    "🇬🇧 English": "en",
    "🇵🇹 Português": "pt",
    "🇫🇷 Français": "fr",
    "🇩🇪 Deutsch": "de",
}



PILLAR_TRANSLATIONS = {
    "Finance": {
        "en": "Finance", "pt": "Finanças",
        "fr": "Finances", "de": "Finanzen",
    },
    "Adventure": {
        "en": "Adventure", "pt": "Aventura",
        "fr": "Aventure", "de": "Abenteuer",
    },
    "Social": {
        "en": "Social", "pt": "Vida Social",
        "fr": "Vie sociale", "de": "Soziales",
    },
    "Personal Growth": {
        "en": "Personal Growth", "pt": "Desenvolvimento Pessoal",
        "fr": "Développement personnel", "de": "Persönliche Entwicklung",
    },
    "Languages": {
        "en": "Languages", "pt": "Idiomas",
        "fr": "Langues", "de": "Sprachen",
    },
    "Health": {
        "en": "Health", "pt": "Saúde",
        "fr": "Santé", "de": "Gesundheit",
    },
    "Fitness": {
        "en": "Fitness", "pt": "Exercício",
        "fr": "Sport", "de": "Fitness",
    },
}


def translate_pillar_label(item: str, language: str | None = None) -> str:
    """Translate a pillar navigation label while preserving its emoji prefix."""
    if language is None:
        language = st.session_state.get("language", "en")

    for category, translations in PILLAR_TRANSLATIONS.items():
        if category in item:
            return item.replace(
                category,
                translations.get(language, category),
                1,
            )

    return item

def language_picker(key: str) -> None:
    """Compact language selector; changing it re-runs the page in the new language."""
    current = st.session_state.get("language", "en")
    codes = list(LANGUAGES.values())
    choice = st.selectbox(
        "🌍", list(LANGUAGES), index=codes.index(current) if current in codes else 0,
        key=key, label_visibility="collapsed",
    )
    if LANGUAGES[choice] != current:
        st.session_state.language = LANGUAGES[choice]
        st.rerun()

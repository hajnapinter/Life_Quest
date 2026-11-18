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
    language = st.session_state.get("language", "en")
    return TRANSLATIONS.get(
        language, TRANSLATIONS["en"]
    ).get(key, key)


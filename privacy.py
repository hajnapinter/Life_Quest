"""Public privacy notice and an honest, user-initiated rights request path."""
from pathlib import Path
from urllib.parse import urlencode

import streamlit as st

CONTACT = "81324@novasbe.pt"
CONTROLLER = "Hajna Pinter"
TEXT = {
    "en": ("Privacy policy", "Your data, your choice", "Request account deletion", "Request my data or another privacy right", "This opens your email app. Send the message yourself from your account email. Nothing is sent or deleted by clicking. We verify your identity before taking action. Never send your password.", "Back to Life Quest"),
    "pt": ("Política de privacidade", "Os teus dados, a tua escolha", "Pedir a eliminação da conta", "Pedir os meus dados ou exercer outro direito", "Abre a tua aplicação de email. Envia a mensagem a partir do email da tua conta. O clique não envia nem elimina nada. Verificamos a tua identidade antes de agir. Nunca envies a palavra-passe.", "Voltar ao Life Quest"),
    "fr": ("Politique de confidentialité", "Tes données, ton choix", "Demander la suppression du compte", "Demander mes données ou exercer un autre droit", "Ouvre ton application e-mail. Envoie toi-même le message depuis l’adresse de ton compte. Le clic n’envoie ni ne supprime rien. Nous vérifions ton identité avant d’agir. N’envoie jamais ton mot de passe.", "Retour à Life Quest"),
    "de": ("Datenschutzerklärung", "Deine Daten, deine Wahl", "Kontolöschung anfragen", "Meine Daten oder ein anderes Datenschutzrecht anfragen", "Öffnet dein E-Mail-Programm. Sende die Nachricht selbst von deiner Konto-Adresse. Ein Klick versendet und löscht nichts. Vor einer Bearbeitung prüfen wir deine Identität. Sende niemals dein Passwort.", "Zurück zu Life Quest"),
}


def language():
    value = st.session_state.get("language", "en")
    return value if value in TEXT else "en"


def request_url(deletion=False, lang="en"):
    text = TEXT.get(lang, TEXT["en"])
    return "mailto:" + CONTACT + "?" + urlencode({"subject": "Life Quest — " + text[2 if deletion else 3]})


def notice_text(lang):
    lang = lang if lang in TEXT else "en"
    return (Path(__file__).parent / "docs" / f"privacy-{lang}.md").read_text()


def render_privacy_link():
    from invitations import base_url
    root = (base_url() or "https://life-quest-team.streamlit.app/").rstrip("/")
    st.link_button(TEXT[language()][0], root + "/?privacy=1")


def render_privacy_controls():
    text = TEXT[language()]
    with st.expander(text[1]):
        render_privacy_link()
        st.caption(text[4])
        st.link_button(text[2], request_url(True, language()))
        st.link_button(text[3], request_url(False, language()))
        st.caption(f"{CONTROLLER} · {CONTACT}")


def render_privacy_page():
    from design import brand
    from i18n import language_picker
    brand()
    language_picker("privacy_language")
    text = TEXT[language()]
    st.title(text[0])
    st.markdown(notice_text(language()))
    render_privacy_controls()
    from invitations import base_url
    st.link_button(text[5], base_url() or "https://life-quest-team.streamlit.app/")

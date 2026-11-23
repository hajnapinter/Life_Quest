"""Profile photo, avatar ring and device notifications.

Stored in the user's auth metadata under `lifequest_profile`:
    {"photo": "data:image/jpeg;base64,...", "ring": "lilac", "push": true}

There is no Supabase Storage bucket in this project, so the photo is shrunk to a
small 80x80 JPEG (a few KB) before saving. If the team adds a Storage bucket later,
move the photo there and keep only its URL here.
"""
import base64
import io
import json

import streamlit as st
import streamlit.components.v1 as components

from design import AVATAR_RINGS, avatar_html
from profile_data import save_user_data

PHOTO_SIZE = 80
MAX_PHOTO_CHARS = 9000  # keeps the saved photo small enough for the login token
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # reject huge uploads before decoding them

TEXT = {
    "en": {"photo": "Profile photo", "upload": "Upload a photo", "remove": "Remove photo", "ring": "Avatar style",
           "ring_hint": "Choose your avatar ring", "saved": "Profile updated.", "bad": "That file isn't an image we can read. Try a JPG or PNG.",
           "error": "We couldn't save this. Please try again.",
           "push": "Device notification test", "push_help": "Send a test on this device. Background push delivery is not enabled.",
           "enable": "Turn on for this device", "on": "Notifications are on for this device.",
           "blocked": "Notifications are blocked. Allow them in your browser settings.",
           "unsupported": "This browser doesn't support notifications. On iPhone, add Life Quest to your Home Screen first.",
           "test_title": "Life Quest 🌱", "test_body": "Notifications are on. Small steps, every day!"},
    "pt": {"photo": "Foto de perfil", "upload": "Carregar uma foto", "remove": "Remover foto", "ring": "Estilo do avatar",
           "ring_hint": "Escolhe o anel do teu avatar", "saved": "Perfil atualizado.", "bad": "Não conseguimos ler esse ficheiro. Experimenta um JPG ou PNG.",
           "error": "Não foi possível guardar. Tenta novamente.",
           "push": "Teste de notificação neste dispositivo", "push_help": "Envia um teste neste dispositivo. O envio de notificações em segundo plano não está ativo.",
           "enable": "Ativar neste dispositivo", "on": "As notificações estão ativas neste dispositivo.",
           "blocked": "As notificações estão bloqueadas. Permite-as nas definições do navegador.",
           "unsupported": "Este navegador não suporta notificações. No iPhone, adiciona primeiro o Life Quest ao ecrã principal.",
           "test_title": "Life Quest 🌱", "test_body": "Notificações ativas. Pequenos passos, todos os dias!"},
    "fr": {"photo": "Photo de profil", "upload": "Ajouter une photo", "remove": "Supprimer la photo", "ring": "Style d'avatar",
           "ring_hint": "Choisis l'anneau de ton avatar", "saved": "Profil mis à jour.", "bad": "Impossible de lire ce fichier. Essaie un JPG ou un PNG.",
           "error": "Impossible d'enregistrer. Réessaie.",
           "push": "Test de notification sur cet appareil", "push_help": "Envoie un test sur cet appareil. Les notifications en arrière-plan ne sont pas activées.",
           "enable": "Activer sur cet appareil", "on": "Les notifications sont activées sur cet appareil.",
           "blocked": "Les notifications sont bloquées. Autorise-les dans les réglages du navigateur.",
           "unsupported": "Ce navigateur ne gère pas les notifications. Sur iPhone, ajoute d'abord Life Quest à l'écran d'accueil.",
           "test_title": "Life Quest 🌱", "test_body": "Notifications activées. De petits pas, chaque jour !"},
    "de": {"photo": "Profilfoto", "upload": "Foto hochladen", "remove": "Foto entfernen", "ring": "Avatar-Stil",
           "ring_hint": "Wähle deinen Avatar-Ring", "saved": "Profil aktualisiert.", "bad": "Diese Datei können wir nicht lesen. Versuche ein JPG oder PNG.",
           "error": "Konnte nicht gespeichert werden. Bitte versuche es erneut.",
           "push": "Benachrichtigung auf diesem Gerät testen", "push_help": "Sende einen Test auf diesem Gerät. Hintergrund-Push ist nicht aktiviert.",
           "enable": "Auf diesem Gerät aktivieren", "on": "Benachrichtigungen sind auf diesem Gerät aktiv.",
           "blocked": "Benachrichtigungen sind blockiert. Erlaube sie in den Browser-Einstellungen.",
           "unsupported": "Dieser Browser unterstützt keine Benachrichtigungen. Auf dem iPhone füge Life Quest zuerst zum Home-Bildschirm hinzu.",
           "test_title": "Life Quest 🌱", "test_body": "Benachrichtigungen sind aktiv. Kleine Schritte, jeden Tag!"},
}


def _t(lang: str) -> dict:
    return TEXT.get(lang, TEXT["en"])


def prefs() -> dict:
    user = st.session_state.get("user") or {}
    return (user.get("user_metadata") or {}).get("lifequest_profile") or {}


def photo() -> str | None:
    value = prefs().get("photo")
    return value if isinstance(value, str) and value.startswith("data:image/") else None


def ring() -> str:
    """Use a valid saved avatar style."""
    chosen = prefs().get("ring", "peach")
    return chosen if chosen in AVATAR_RINGS else "peach"


def _save(api, changes: dict, lang: str) -> None:
    error = save_user_data(api, {"lifequest_profile": {**prefs(), **changes}})
    if error:
        st.error(_t(lang)["error"])
    else:
        st.session_state.profile_toast = _t(lang)["saved"]
        st.rerun()


def shrink_photo(raw: bytes) -> str | None:
    """Centre-crop to a square, resize to PHOTO_SIZE and return a small JPEG data URL."""
    from PIL import Image, ImageOps, UnidentifiedImageError
    if not raw or len(raw) > MAX_UPLOAD_BYTES:
        return None
    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
        return None
    image = ImageOps.fit(image, (PHOTO_SIZE, PHOTO_SIZE), Image.LANCZOS)
    for quality in (75, 60, 45):
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=quality, optimize=True)
        url = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()
        if len(url) <= MAX_PHOTO_CHARS:
            return url
    return None


def render_photo_setting(api, lang: str) -> None:
    """Photo upload and avatar style picker."""
    t = _t(lang)
    if st.session_state.get("profile_toast"):
        st.toast(st.session_state.pop("profile_toast"), icon="📸")
    with st.expander("📸 " + t["photo"]):
        upload = st.file_uploader(t["upload"], type=["jpg", "jpeg", "png", "webp"], key="photo_upload",
                                  label_visibility="collapsed")
        if upload is not None and st.session_state.get("photo_done") != upload.file_id:
            st.session_state.photo_done = upload.file_id
            url = shrink_photo(upload.getvalue())
            if url is None:
                st.error(t["bad"])
            else:
                _save(api, {"photo": url}, lang)
        if photo() and st.button(t["remove"], key="photo_remove"):
            _save(api, {"photo": None}, lang)
        st.caption(t["ring_hint"])
        current = prefs().get("ring", "peach")
        name = st.session_state.profile.get("display_name", "")
        previews = "".join(avatar_html(name, photo(), r, size=40) for r in AVATAR_RINGS)
        st.markdown(f'<div class="lq-rings">{previews}</div>', unsafe_allow_html=True)
        choice = st.segmented_control(t["ring"], list(AVATAR_RINGS), default=current, key="ring_pick",
                                      format_func=str.capitalize, label_visibility="collapsed")
        if choice and choice != current:
            _save(api, {"ring": choice}, lang)


def render_push_setting(api, lang: str) -> None:
    """Device notifications: saved preference + browser permission on this device."""
    t = _t(lang)
    enabled = bool(prefs().get("push"))
    wanted = st.toggle(t["push"], value=enabled, key="push_toggle", help=t["push_help"])
    if wanted != enabled:
        _save(api, {"push": wanted}, lang)
    if wanted:
        _permission_button(t)


def _permission_button(t: dict) -> None:
    """Asks the browser for notification permission and shows a test notification."""
    labels = json.dumps({k: t[k] for k in ("enable", "on", "blocked", "unsupported", "test_title", "test_body")})
    components.html(f"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600&display=swap">
<style>
  body{{margin:0;padding:2px;font-family:"Inter Tight",system-ui,sans-serif;color:#2B2330;background:transparent}}
  button{{border:1px solid #F1E4DA;background:#fff;border-radius:999px;height:40px;padding:0 18px;font:600 14px "Inter Tight",system-ui,sans-serif;
    color:#2B2330;cursor:pointer;transition:transform .18s ease,box-shadow .18s ease}}
  button:hover{{transform:translateY(-2px);box-shadow:0 10px 20px -12px rgba(212,85,31,.7)}}
  button:focus-visible{{outline:2px solid #BF4A1A;outline-offset:2px}}
  p{{margin:6px 4px 0;font-size:13px;color:#7A6E7E}}
</style>
<button id="b">🔔 </button><p id="s" role="status" aria-live="polite"></p>
<script>
  const L = {labels};
  const b = document.getElementById('b'), s = document.getElementById('s');
  b.textContent = '🔔 ' + L.enable;
  let N = null;
  try {{ N = window.parent.Notification || window.Notification; }} catch (e) {{ N = window.Notification; }}
  function show(state) {{
    if (!N) {{ s.textContent = L.unsupported; b.disabled = true; return; }}
    if (state === 'granted') s.textContent = L.on;
    else if (state === 'denied') s.textContent = L.blocked;
  }}
  show(N ? N.permission : null);
  b.addEventListener('click', async () => {{
    if (!N) return show(null);
    const state = await N.requestPermission();
    show(state);
    if (state === 'granted') new N(L.test_title, {{body: L.test_body}});
  }});
</script>""", height=78)

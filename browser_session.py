"""Restore a verified Supabase session after reload or reopening the app.

Only the rotating refresh credential is saved in project-scoped browser storage,
for at most 30 days since its last authenticated rotation. No access token is
persisted. Logout clears persistent and legacy tab storage and revokes the session.
"""
import time
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

_session = components.declare_component('lifequest_session', path=str(Path(__file__).parent/'session_component'))

RESTORE_TEXT = {
    'en': ('Restoring your sign-in…', 'Your connection was interrupted. Retry to restore your sign-in.', 'Try again', 'Sign in again', 'Your browser blocked session storage. Sign-in cannot be remembered on this device.'),
    'pt': ('A recuperar a tua sessão…', 'A ligação foi interrompida. Tenta recuperar a tua sessão.', 'Tentar novamente', 'Iniciar sessão novamente', 'O navegador bloqueou o armazenamento da sessão. Não é possível memorizar o acesso neste dispositivo.'),
    'fr': ('Restauration de ta connexion…', 'La connexion a été interrompue. Réessaie de restaurer ta session.', 'Réessayer', 'Se reconnecter', 'Ton navigateur bloque le stockage de session. La connexion ne peut pas être mémorisée sur cet appareil.'),
    'de': ('Deine Anmeldung wird wiederhergestellt…', 'Die Verbindung wurde unterbrochen. Versuche die Anmeldung erneut wiederherzustellen.', 'Erneut versuchen', 'Erneut anmelden', 'Dein Browser blockiert den Sitzungsspeicher. Die Anmeldung kann auf diesem Gerät nicht gespeichert werden.'),
}


def sync_session(api, project_url):
    clearing=st.session_state.get('clear_browser_session',False)
    token=st.session_state.get('refresh_token')
    mode='clear' if clearing else 'write' if token else 'read'
    reply=_session(project=project_url,mode=mode,refresh_token=token if mode=='write' else None,
                   key='browser_session',default=None)
    if not isinstance(reply,dict) or not isinstance(reply.get('nonce'),str):
        return 'ready' if st.session_state.get('access_token') else 'pending'
    if clearing:
        if reply.get('action')=='clear':
            st.session_state.clear_browser_session=False
            return 'ready'
        return 'pending'
    if reply.get('action')=='logout':
        if st.session_state.get('browser_session_seen') != reply['nonce']:
            st.session_state.clear()
            st.session_state.clear_browser_session=True
            st.rerun()
        return 'pending'
    if st.session_state.get('access_token'):
        return 'ready'
    if reply.get('action')=='unavailable':
        return 'unavailable'
    if reply.get('action') in ('write','clear'):
        return 'ready'
    saved=reply.get('refresh_token')
    if not isinstance(saved,str) or not 1<=len(saved)<=4096:
        return 'ready'
    if st.session_state.get('browser_session_seen')==reply['nonce']:
        return 'ready'
    data,error=api('POST','/auth/v1/token?grant_type=refresh_token',{'refresh_token':saved})
    if error or not isinstance(data,dict):
        # Preserve the credential on transient failures. Do not flash a login form.
        return 'retry'
    access=data.get('access_token'); refresh=data.get('refresh_token'); user=data.get('user')
    if not isinstance(access,str) or not isinstance(refresh,str) or not isinstance(user,dict) or not user.get('id'):
        return 'retry'
    verified,error=api('GET','/auth/v1/user',access_token=access)
    if error or not isinstance(verified,dict) or verified.get('id')!=user['id']:
        return 'retry'
    st.session_state.browser_session_seen=reply['nonce']
    st.session_state.update(access_token=access,refresh_token=refresh,user=verified,profile=None,
                            token_expires_at=time.time()+max(0,int(data.get('expires_in') or 3600)))
    st.rerun()
    return 'ready'


def render_restore_status(status):
    """Keep restore/retry separate from an explicit request to sign in again."""
    text=RESTORE_TEXT.get(st.session_state.get('language','en'),RESTORE_TEXT['en'])
    if status=='pending':
        st.info(text[0])
    elif status=='retry':
        st.warning(text[1])
        if st.button(text[2],key='retry_saved_session'):
            st.rerun()
        if st.button(text[3],key='discard_saved_session'):
            st.session_state.clear_browser_session=True
            st.rerun()
    elif status=='unavailable':
        st.caption(text[4])

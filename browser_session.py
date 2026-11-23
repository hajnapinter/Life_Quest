"""Restore a Supabase session after reload in the same browser tab.

Only a refresh token is kept in sessionStorage, never a URL or disk. It is
rotated and verified with Supabase before any profile is loaded. Closing the
tab clears storage; explicit logout clears storage and revokes the session.
"""
import time
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

_session = components.declare_component('lifequest_session', path=str(Path(__file__).parent/'session_component'))


def sync_session(api, project_url):
    clearing=st.session_state.get('clear_browser_session',False)
    token=st.session_state.get('refresh_token')
    mode='clear' if clearing else 'write' if token else 'read'
    reply=_session(project=project_url,mode=mode,refresh_token=token if mode=='write' else None,
                   key='browser_session',default=None)
    if not isinstance(reply,dict) or not isinstance(reply.get('nonce'),str):
        return
    if clearing:
        if reply.get('action')=='clear':
            st.session_state.clear_browser_session=False
        return
    if st.session_state.get('browser_session_seen')==reply['nonce']:
        return
    st.session_state.browser_session_seen=reply['nonce']
    saved=reply.get('refresh_token')
    if st.session_state.get('access_token') or not isinstance(saved,str) or not 1<=len(saved)<=4096:
        return
    data,error=api('POST','/auth/v1/token?grant_type=refresh_token',{'refresh_token':saved})
    if error or not isinstance(data,dict):
        # A temporary network failure must not destroy a valid saved session.
        return
    access=data.get('access_token'); refresh=data.get('refresh_token'); user=data.get('user')
    if not isinstance(access,str) or not isinstance(refresh,str) or not isinstance(user,dict) or not user.get('id'):
        return
    verified,error=api('GET','/auth/v1/user',access_token=access)
    if error or not isinstance(verified,dict) or verified.get('id')!=user['id']:
        return
    st.session_state.update(access_token=access,refresh_token=refresh,user=verified,profile=None,
                            token_expires_at=time.time()+max(0,int(data.get('expires_in') or 3600)))
    st.rerun()

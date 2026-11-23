"""Restoration must verify identity and tolerate a transient connection failure."""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import browser_session as session

class State(dict):
    __getattr__=dict.get
    __setattr__=dict.__setitem__

def setup(monkeypatch, reply, **values):
    state=State(values)
    monkeypatch.setattr(session,'st',SimpleNamespace(session_state=state,rerun=Mock()))
    monkeypatch.setattr(session,'_session',lambda **kw:reply)
    return state

def test_reload_waits_for_browser_instead_of_claiming_signed_out(monkeypatch):
    setup(monkeypatch,None)
    assert session.sync_session(Mock(),'https://project.supabase.co')=='pending'

def test_transient_restore_failure_can_retry_the_same_browser_reply(monkeypatch):
    state=setup(monkeypatch,{'nonce':'same-load','action':'read','refresh_token':'saved'})
    api=Mock(return_value=(None,'temporary connection failure'))
    assert session.sync_session(api,'https://project.supabase.co')=='retry'
    assert state.browser_session_seen is None
    api.side_effect=[({'access_token':'new-access','refresh_token':'rotated','user':{'id':'user-a'},'expires_in':3600},None),({'id':'user-a'},None)]
    assert session.sync_session(api,'https://project.supabase.co')=='ready'
    assert state.user=={'id':'user-a'} and state.refresh_token=='rotated'
    assert api.call_args.kwargs=={'access_token':'new-access'}

def test_restoring_a_different_identity_never_signs_in(monkeypatch):
    state=setup(monkeypatch,{'nonce':'load','refresh_token':'saved'})
    api=Mock(side_effect=[({'access_token':'access','refresh_token':'refresh','user':{'id':'a'}},None),({'id':'b'},None)])
    assert session.sync_session(api,'https://project.supabase.co')=='retry'
    assert state.access_token is None and state.user is None

def test_other_tab_logout_clears_the_server_session(monkeypatch):
    state=setup(monkeypatch,{'nonce':'logout','action':'logout'},access_token='access',refresh_token='saved',user={'id':'a'})
    assert session.sync_session(Mock(),'https://project.supabase.co')=='pending'
    assert state.access_token is None and state.user is None and state.clear_browser_session


def test_restore_css_stays_inside_the_style_element():
    from design import _CSS
    assert _CSS.lstrip().startswith("<style>")
    assert _CSS.index("<style>") < _CSS.index(".st-key-auth_restoring") < _CSS.index("</style>")


def test_oauth_callback_takes_priority_over_a_previously_saved_account(monkeypatch):
    setup(monkeypatch,None)
    component=Mock(side_effect=AssertionError('must not mount a competing restore'))
    monkeypatch.setattr(session,'_session',component)
    api=Mock()
    assert session.sync_session(api,'https://project.supabase.co',oauth_pending=True)=='ready'
    component.assert_not_called()
    api.assert_not_called()

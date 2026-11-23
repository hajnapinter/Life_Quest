"""Regressions from the two-user live review; existing progression is preserved."""
from copy import deepcopy
from datetime import date
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest

from personalization import personalize_title
from quest_plan import slot_plan,weekly_recap,quest_xp
from test_features import State
from test_workflows import backend,ready_user,log_in,go,quest_boxes,everything_text,button,field
import browser_session


def test_home_updates_xp_in_same_render(backend):
    ready_user(backend,'xp@example.com',categories=('Fitness',))
    at=log_in('xp@example.com')
    quest_boxes(at)[0].check().run()
    assert not at.exception
    assert '20 XP' in everything_text(at)
    # Explicitly retain the user's existing immediate progression.
    assert next(q for q in backend.quests if q['status']=='active' and q['slot']==1)['target']==6000


def test_recap_includes_squad_and_individual_activity(backend):
    user=ready_user(backend,'recap@example.com',categories=('Fitness',))
    at=log_in('recap@example.com')
    quest_boxes(at)[0].check().run()
    backend.rewards.append({'user_id':user['id'],'category':'Squad','title':'Cook together','points':30,
        'status':'completed','completed_at':date.today().isoformat()+'T12:00:00Z'})
    go(at,'📊 Recap')
    metrics={m.label:m.value for m in at.metric}
    assert metrics['XP earned']=='50'
    assert metrics['Quests completed']=='2'


def test_weekly_bonus_is_xp_not_an_extra_completed_quest():
    today=date(2026,11,23)
    rows=[{'status':'completed','category':'Competition','completed_at':'2026-11-23T12:00:00Z',
           'points':50,'counts_as_quest':False}]
    result=weekly_recap(rows,today)
    assert result['xp']==50 and result['completed']==0
    assert quest_xp({'difficulty':5,'xp_awarded':0})==0


@pytest.mark.parametrize('lang,name',[('en','Japanese'),('pt','Japonês'),('fr','Japonais'),('de','Japanisch')])
def test_target_language_is_specific_in_every_display_language(lang,name):
    plan=slot_plan('Languages',1,3,[]); original=deepcopy(plan)
    title=personalize_title(plan['title'],plan,{'target_language':'ja'},'Lisbon, Portugal',lang)
    assert name in title and '15' in title
    assert plan==original


def test_country_changes_recipe_and_currency_without_changing_targets():
    recipe=slot_plan('Adventure',4,2,[])
    assert 'Portuguese' in personalize_title(recipe['title'],recipe,{},'Lisbon, Portugal')
    money=slot_plan('Finance',1,2,[])
    assert personalize_title(money['title'],money,{},'Budapest, Hungary')=='Track 5 expenses in HUF'
    assert money['target']==5


def test_mobile_navigation_has_five_main_destinations(backend):
    ready_user(backend,'nav@example.com',categories=('Fitness','Languages','Health','Social'))
    at=log_in('nav@example.com')
    assert len(at.radio(key='main_navigation').options)==6
    button(at,'💪 Fitness →').click().run()
    assert at.title[0].value=='💪 Fitness'


def test_can_leave_squad_without_losing_xp(backend):
    user=ready_user(backend,'leave@example.com')
    at=go(log_in('leave@example.com'),'👥 Squad')
    field(at,'Squad name').input('Leave test')
    button(at,'Start a squad').click().run()
    backend.profiles[user['id']]['points']=30
    button(at,'Leave squad').click().run()
    assert user['id'] not in backend.squads[0]['members']
    assert backend.profiles[user['id']]['points']==30


def test_browser_session_rotates_and_verifies_before_restoring(monkeypatch):
    state=State(access_token=None,refresh_token=None)
    monkeypatch.setattr(browser_session,'st',SimpleNamespace(session_state=state,rerun=lambda:None))
    monkeypatch.setattr(browser_session,'_session',lambda **kwargs:{'nonce':'load-1','refresh_token':'saved-fixture'})
    calls=[]
    def api(method,path,payload=None,access_token=None):
        calls.append(path)
        if path.startswith('/auth/v1/token'):
            return {'access_token':'new-fixture','refresh_token':'rotated-fixture','user':{'id':'u1'},'expires_in':3600},None
        return {'id':'u1'},None
    browser_session.sync_session(api,'https://fixture.supabase.test')
    assert state.access_token=='new-fixture' and state.refresh_token=='rotated-fixture'
    assert calls==['/auth/v1/token?grant_type=refresh_token','/auth/v1/user']


def test_browser_session_cannot_restore_a_mismatched_identity(monkeypatch):
    state=State(access_token=None)
    monkeypatch.setattr(browser_session,'st',SimpleNamespace(session_state=state,rerun=lambda:pytest.fail('must not restore')))
    monkeypatch.setattr(browser_session,'_session',lambda **kwargs:{'nonce':'load-2','refresh_token':'fixture'})
    def api(method,path,payload=None,access_token=None):
        return ({'access_token':'fixture','refresh_token':'fixture2','user':{'id':'u1'}} if method=='POST' else {'id':'different'}),None
    browser_session.sync_session(api,'https://fixture.supabase.test')
    assert state.access_token is None


def test_reminder_worker_does_not_send_during_configuration_check(monkeypatch,capsys):
    path=Path(__file__).resolve().parents[1]/'scripts/send_reminders.py'
    spec=importlib.util.spec_from_file_location('send_reminders',path)
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    from unittest.mock import MagicMock
    smtp=MagicMock();smtp.__enter__.return_value=smtp
    monkeypatch.setattr(worker.smtplib,'SMTP',lambda *args,**kwargs:smtp)
    calls=[]
    monkeypatch.setattr(worker,'rpc',lambda config,name,payload:calls.append(name) or True)
    worker.run({'SMTP_HOST':'fixture','SMTP_USERNAME':'fixture','SMTP_PASSWORD':'fixture'},check_only=True)
    smtp.send_message.assert_not_called()
    assert calls==['check_reminder_worker']


def test_reminder_copy_is_localized_and_headers_reject_injection():
    path=Path(__file__).resolve().parents[1]/'scripts/send_reminders.py'
    spec=importlib.util.spec_from_file_location('reminder_copy',path)
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    config={'SMTP_SENDER':'sender@example.com','APP_URL':'https://example.com'}
    recipient={'id':'fixture','email':'recipient@example.com','name':'Ana','language':'fr'}
    mail=worker.message(recipient,config)
    assert 'prochain' in mail['Subject'] and 'Paramètres' in mail.get_content()
    with pytest.raises(ValueError):
        worker.message({**recipient,'email':'recipient@example.com\nBcc: other@example.com'},config)


@pytest.mark.parametrize('body,expected',[(b'',None),(b'null',None),(b'[]',[])])
def test_reminder_rpc_accepts_successful_empty_void_response(monkeypatch,body,expected):
    import io
    path=Path(__file__).resolve().parents[1]/'scripts/send_reminders.py'
    spec=importlib.util.spec_from_file_location('reminder_rpc',path)
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    monkeypatch.setattr(worker,'urlopen',lambda *a,**k:io.BytesIO(body))
    config={'SUPABASE_URL':'https://fixture.supabase.test','SUPABASE_ANON_KEY':'fixture','REMINDER_WORKER_KEY':'fixture'}
    assert worker.rpc(config,'settle_due_competitions',{})==expected

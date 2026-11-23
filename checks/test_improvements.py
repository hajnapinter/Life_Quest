"""Regression checks for variety, factual insights and invitation-link journeys."""
from copy import deepcopy
from datetime import date
import io
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlsplit

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests'))
from quest_plan import TRACKS, EXPERIENCE_FOCUSES, slot_plan
from quest_variety import VARIANTS, varied_plan, render_variant
from progress_insights import insight_facts, insight_messages
from invitations import invitation_url, valid_invitation
from test_workflows import backend, ready_user, log_in, new_app, button, field, go, everything_text


def test_each_track_has_distinct_translated_activities_without_changing_progression():
    assert set(VARIANTS)=={track[0] for tracks in TRACKS.values() for track in tracks}
    for category,tracks in TRACKS.items():
        for slot,track in enumerate(tracks,1):
            history=[];titles=[]
            for i in range(len(VARIANTS[track[0]])+1):
                plan=slot_plan(category,slot,2,history);before=deepcopy(plan)
                varied=varied_plan(plan,history,{'target_language':'ja','location':'Lisbon, Portugal','level':2})
                assert plan==before
                assert all(varied[k]==plan[k] for k in ('target','difficulty','minutes','metric','slot','focus'))
                assert 1<=len(varied['title'])<=100
                for lang in ('en','pt','fr','de'):
                    text=render_variant(varied,varied['context'],'Lisbon, Portugal',lang)
                    assert text and '{' not in text
                    if varied['metric']:
                        assert str(varied['target']) in text.replace(',','')
                    else:
                        assert not any(x in text for x in ('minutes','minutos','Minuten'))
                assert not titles or varied['context']['variant']!=history[-1]['context']['variant']
                titles.append(varied['title'])
                history.append({**varied,'status':'completed','completed_at':f'2026-11-23T12:{i:02d}:00Z'})
            assert len(set(q['context']['variant'] for q in history[:-1]))==len(VARIANTS[track[0]])


def test_variety_cycle_advances_after_skipping():
    plan=slot_plan('Adventure',4,2,[])
    first=varied_plan(plan,[],{})
    second=varied_plan(plan,[{**first,'status':'skipped'}],{})
    assert first['context']['variant']!=second['context']['variant']
    assert first['target']==second['target']==1


def row(day,**extra):
    return {'status':'completed','category':'Fitness','focus':'steps','completed_at':day+'T12:00:00Z',**extra}


def test_insights_compare_equivalent_weekdays_and_exclude_bonus_future_and_invalid_rows():
    rows=[row('2026-11-23'),row('2026-11-24'),row('2026-11-24'),row('2026-11-16'),
          row('2026-11-18'),row('2026-11-25'),row('invalid'),row('2026-11-24',counts_as_quest=False),
          row('2026-11-24',status='active')]
    f=insight_facts(rows,date(2026,11,24))
    assert f['count']==3 and f['days']==2 and f['previous']==1
    assert f['best']['focus']=='steps'
    assert 'compared with 1' in ' '.join(insight_messages(rows,today=date(2026,11,24)))


def test_insights_do_not_mix_languages_or_count_bonus_as_a_habit():
    rows=[row('2026-11-23',category='Languages',focus='vocabulary',context={'target_language':'ja'}),
          row('2026-11-24',category='Languages',focus='vocabulary',context={'target_language':'fr'}),
          row('2026-11-24',category='Languages',focus='vocabulary',context={'target_language':'fr'}),
          row('2026-11-24',category='Competition',focus=None,counts_as_quest=False)]
    f=insight_facts(rows,date(2026,11,24))
    assert f['best']['goal']=='fr' and f['best']['count']==2
    for language in ('en','pt','fr','de'):
        assert insight_messages(rows,language,date(2026,11,24))
        assert len(insight_messages([],language,date(2026,11,24)))==1


@pytest.mark.parametrize('root',['javascript:alert(1)','https://evil.example/?next=x','https://u:p@evil.example/','http://evil.example/'])
def test_invitation_links_reject_untrusted_redirect_shapes(root):
    assert invitation_url(root,'squad','ABCD1234') is None


def test_invitation_link_roundtrip_and_code_validation():
    link=invitation_url('https://life-quest-team.streamlit.app/','competition','abcdef123456')
    query=parse_qs(urlsplit(link).query)
    assert valid_invitation({'kind':query['join'][0],'code':query['invite'][0]})=={'kind':'competition','code':'ABCDEF123456'}
    for value in [None,{}, {'kind':'other','code':'ABCD1234'}, {'kind':'squad','code':'<script>'}, {'kind':'competition','code':'ABCD1234'}]:
        assert valid_invitation(value) is None


def test_logged_out_invitation_survives_email_login_and_requires_explicit_acceptance(backend):
    creator=ready_user(backend,'creator@example.com')
    # Create through the same fake RPC that backs existing workflow tests.
    backend.rpc_create_squad(creator['id'],{'squad_name_input':'Invitation QA'})
    squad=backend.squads[0]
    # Production codes are hexadecimal; the fake's generated code need not be.
    squad['invite_code']='ABCD1234'
    friend=ready_user(backend,'friend@example.com')
    at=new_app()
    at.query_params.update({'join':'squad','invite':'ABCD1234'})
    at.run()
    assert any('Sign in or create your account' in x.value for x in at.info)
    field(at,'Email').input('friend@example.com');field(at,'Password').input('password123')
    button(at,'Log in').click().run()
    assert not at.exception
    assert friend['id'] not in squad['members']
    assert at.session_state.pending_invitation['code']=='ABCD1234'
    button(at,'Accept invitation').click().run()
    assert not at.exception
    assert friend['id'] in squad['members']
    assert 'join' not in at.query_params and 'invite' not in at.query_params
    assert at.session_state.current_page=='👥 Squad'


def test_invalid_invitation_does_not_join_or_discard_the_pending_link(backend):
    ready_user(backend,'invalid-invite@example.com')
    at=log_in('invalid-invite@example.com')
    at.query_params.update({'join':'squad','invite':'DEAD1234'});at.run()
    button(at,'Accept invitation').click().run()
    assert not at.exception
    assert any('could not be accepted' in x.value for x in at.error)
    assert at.session_state.pending_invitation['code']=='DEAD1234'
    button(at,'Dismiss invitation').click().run()
    assert not at.exception
    assert 'join' not in at.query_params


def test_curated_quests_switch_languages_without_ai_and_keep_completed_history(backend):
    from ai_quest_ui import display_titles
    ready_user(backend,'variety@example.com',categories=('Languages',),metadata={'lifequest_preferences':{'target_language':'ja'}})
    at=log_in('variety@example.com')
    first=next(q for q in backend.quests if q['category']=='Languages' and q['slot']==1)
    assert first['context']['variety_version']==1
    assert any('Japanese' in q.label for q in at.checkbox)
    at.selectbox(key='header_language').set_value('🇵🇹 Português').run()
    assert any('Japonês' in q.label for q in at.checkbox)
    at.selectbox(key='header_language').set_value('🇬🇧 English').run()
    go(at,'📊 Recap')
    assert any(h.value=='Your progress, in words' for h in at.subheader)


def test_ai_repeated_activity_uses_the_varied_fallback(monkeypatch):
    import ai_quests
    responses=[{'data':[{'id':ai_quests.FREE_MODEL,'input_price':0,'output_price':0}]},
               {'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'quests':[{'slot':1,'title':'Walk 6,000 steps today','description':'Walk comfortably.','minutes':60}]})}}]}]
    def reply(*args,**kwargs):
        return io.BytesIO(json.dumps(responses.pop(0)).encode())
    monkeypatch.setattr(ai_quests,'urlopen',reply)
    plan=slot_plan('Fitness',1,3,[])
    with pytest.raises(ai_quests.QuestGenerationError,match='repeated'):
        ai_quests.generate_slot_quests('fixture',[plan],[{'slot':1,'status':'completed','title':'Walk 4,000 steps today'}])


def test_single_completion_feedback_uses_singular_words():
    messages=insight_messages([row('2026-11-23')],'en',date(2026,11,23))
    assert '1 completed quest across 1 day' in messages[0]
    assert 'multiple days' not in messages[0]

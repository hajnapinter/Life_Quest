from pathlib import Path
import sys,io,json
from datetime import date
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from invitations import normalize_invite_code
from duel_progress import standings
from habit_journey import habit_name,journey_texts,journey_facts
from quest_plan import TRACKS,slot_plan
from progress_insights import progress_evidence
from test_workflows import backend,ready_user,log_in,go,button,field
import ai_quests

@pytest.mark.parametrize('value,kind,code',[
 (' 4a5c-0018-a3c0 ','competition','4A5C0018A3C0'),(' abcd1234 ','squad','ABCD1234'),
 ('https://life-quest-team.streamlit.app/?join=competition&invite=ABCDEF123456','competition','ABCDEF123456')])
def test_codes_and_links_route_by_actual_type(value,kind,code):
 assert normalize_invite_code(value)=={'kind':kind,'code':code}

@pytest.mark.parametrize('value',['NOPE99','<script>',None,'https://example.com/?x=y'])
def test_invalid_codes_are_rejected_locally(value):
 assert normalize_invite_code(value) is None


def test_duel_live_standings_do_not_award_unsettled_xp():
 pair={'creator':'a','opponent':'b','opponent_name':'Bea','days':[
 {'day':'2026-11-23','settled':True,'winner':'a','scores':[{'user_id':'a','value':50},{'user_id':'b','value':20}]},
 {'day':'2026-11-24','settled':False,'winner':None,'scores':[{'user_id':'a','value':10},{'user_id':'b','value':30}]}]}
 rows=standings(pair,{'today':'2026-11-24','week_start':'2026-11-23'},'a','Ana')
 assert rows[0]['points']==35 and rows[1]['points']==15
 assert rows[0]['result']==10 and rows[1]['result']==30
 assert [r['place'] for r in rows]==[1,2]


def test_all_habits_have_broad_names_and_journeys_in_four_languages():
 for category,tracks in TRACKS.items():
  for slot,track in enumerate(tracks,1):
   plan=slot_plan(category,slot,2,[])
   for lang in ('en','pt','fr','de'):
    assert habit_name(plan['focus'],lang)
    assert len(journey_texts(plan,[],lang))==4
    assert '{' not in ' '.join(journey_texts(plan,[],lang))


def test_journey_distinguishes_first_latest_and_next_targets():
 rows=[{'category':'Fitness','slot':1,'focus':'steps','status':'completed','target':8000,'completed_at':'2026-11-22T12:00:00Z'},
       {'category':'Fitness','slot':1,'focus':'steps','status':'completed','target':10000,'completed_at':'2026-11-23T12:00:00Z'}]
 plan=slot_plan('Fitness',1,4,rows);facts=journey_facts(plan,rows)
 assert (facts['first'],facts['latest'],facts['next'],facts['goal'])==(8000,10000,12000,12000)
 assert 'latest completed: 10000' in ' '.join(journey_texts(plan,rows))


def test_ai_evidence_excludes_identity_and_unfinished_claims():
 row={'category':'Fitness','slot':1,'focus':'steps','status':'completed','target':8000,'title':'Walk 8000 steps','completed_at':'2026-11-23T12:00:00Z','email':'private@example.com','name':'Private','location':'Secret'}
 evidence=progress_evidence([row,{**row,'status':'active','target':10000}]);encoded=json.dumps(evidence)
 assert 'private@example.com' not in encoded and 'Secret' not in encoded and 'Private' not in encoded
 assert evidence['tracks'][0]['latest_completed_target']==8000 and evidence['tracks'][0]['next_target']==10000

@pytest.mark.parametrize('message,allowed',[
 ('You moved from 8000 to 10000 recorded steps. Keep the next walk comfortable.',True),
 ('You have lost 15 kilograms and saved 999 euros. Keep it up!',False),
 ('I moved from 8000 to 10000 steps and I am proud of myself.',False)])
def test_free_ai_reflection_rejects_unsupported_numbers(monkeypatch,message,allowed):
 replies=[{'data':[{'id':ai_quests.FREE_MODEL,'input_price':0,'output_price':0}]},
          {'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'message':message})}}]}]
 monkeypatch.setattr(ai_quests,'urlopen',lambda *a,**k:io.BytesIO(json.dumps(replies.pop(0)).encode()))
 if allowed:assert ai_quests.generate_progress_message('fixture',{'first':8000,'latest':10000})==message
 else:
  with pytest.raises(ai_quests.QuestGenerationError):ai_quests.generate_progress_message('fixture',{'first':8000,'latest':10000})


def test_settings_removed_sections_and_nav_labels(backend):
 ready_user(backend,'new-settings@example.com')
 at=go(log_in('new-settings@example.com'),'⚙️ Settings')
 assert not at.exception
 assert len(at.radio(key='main_navigation').options)==6
 assert not any(x.value=='Make quests yours' for x in at.subheader)
 assert not any(x.label=='Your city' for x in at.text_input)


def test_1v1_code_in_squad_form_opens_competition(backend):
 ready_user(backend,'cross-code@example.com');calls=[]
 backend.rpc_join_friend_duel=lambda uid,body:calls.append(body['invite']) or 'pair-fixture'
 at=go(log_in('cross-code@example.com'),'👥 Squad')
 field(at,'Squad invite code').input('4A5C0018A3C0')
 button(at,'Join my friends').click().run()
 assert not at.exception
 assert calls==['4A5C0018A3C0']
 assert at.session_state.current_page=='⚔️ Competition'


def test_global_leaderboard_renders_every_account_and_avatars(backend):
 user=ready_user(backend,'global@example.com')
 backend.rpc_get_global_weekly_ranking=lambda uid,body:{'week_start':'2026-11-23','prizes':[],
  'rows':[{'user_id':user['id'],'name':'Ana','points':50,'quests':2,'photo':None},
          {'user_id':'other','name':'Bea','points':35,'quests':1,'photo':None},
          {'user_id':'third','name':'Carla','points':10,'quests':1,'photo':None},
          {'user_id':'zero','name':'Dana','points':0,'quests':0,'photo':None}]}
 at=go(log_in('global@example.com'),'Leaderboard')
 assert not at.exception
 markup=' '.join(m.value for m in at.markdown)
 assert all(name in markup for name in ('Ana','Bea','Carla','Dana'))
 assert '🥇' in markup and '🥈' in markup and '🥉' in markup


def test_active_competition_renders_live_standings_and_score_form(backend):
 user=ready_user(backend,'duel-layout@example.com');uid=user['id']
 state={'today':'2026-11-23','week_start':'2026-11-23','points':0,'squads':[],'friends':[],
 'duels':[{'id':'pair-fixture','creator':uid,'opponent':'friend','creator_name':'Ana','opponent_name':'Bea','status':'active',
           'code':'ABCDEF123456','weeks':[],'days':[{'id':'day-fixture','day':'2026-11-23','title':'Who can walk more steps today?',
           'unit':'steps','max':50000,'settled':False,'winner':None,'scores':[{'user_id':uid,'value':1234}]}]}]}
 backend.rpc_get_social_state=lambda uid,body:state
 at=go(log_in('duel-layout@example.com'),'⚔️ Competition')
 assert not at.exception
 assert '1234' in ' '.join(m.value for m in at.markdown)
 assert any('Your total' in n.label for n in at.number_input)
 assert any(e.label=='Scoring & deadlines' for e in at.expander)
 assert 'Confirmed weekly XP' in ' '.join(m.value for m in at.markdown)

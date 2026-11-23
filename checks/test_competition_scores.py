"""Competition totals exceed the former per-quest and machine-integer ceilings."""
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from competition_scores import score_text
from duel_progress import standings
from test_workflows import backend,ready_user,log_in,go,button,field

@pytest.mark.parametrize('value,expected', [('301','301'),('50001','50001'),(' 0000 ','0'),('000400','400'),
 ('1234567890123456789012345678901234567890','1234567890123456789012345678901234567890')])
def test_totals_preserve_digits_without_a_challenge_ceiling(value,expected):
 assert score_text(value)==expected

@pytest.mark.parametrize('value',['','-1','1.5','1e9','NaN','Infinity','<script>','１２３',None])
def test_only_nonnegative_whole_numbers_are_accepted(value):
 with pytest.raises(ValueError):score_text(value)

@pytest.mark.parametrize('total',['301','50001','9007199254740993','123456789012345678901234567890'])
def test_competition_sends_an_exact_large_total_even_for_a_legacy_300_page_day(backend,total):
 user=ready_user(backend,'uncapped@example.com');uid=user['id'];calls=[]
 backend.rpc_get_social_state=lambda uid,body:{'today':'2026-11-23','week_start':'2026-11-23','points':0,'squads':[],'friends':[],
  'duels':[{'id':'pair-fixture','creator':uid,'opponent':'friend','creator_name':'Ana','opponent_name':'Bea','status':'active',
   'code':'ABCDEF123456','weeks':[],'days':[{'id':'day-fixture','day':'2026-11-23','title':'Who can read more book pages today?',
   'unit':'pages','max':300,'settled':False,'winner':None,'scores':[]}]}]}
 backend.rpc_record_duel_score=lambda uid,body:calls.append(body)
 at=go(log_in('uncapped@example.com'),'⚔️ Competition')
 field(at,'Your total (pages)').input(total)
 button(at,'Save my result').click().run()
 assert not at.exception
 assert calls==[{'quest_id':'day-fixture','result_value':total}]


def test_large_provisional_scores_sort_correctly_without_awarding_more_xp():
 big=10**40
 pair={'creator':'a','opponent':'b','days':[{'day':'2026-11-23','settled':False,'winner':None,
  'scores':[{'user_id':'a','value':big},{'user_id':'b','value':big+1}]}]}
 rows=standings(pair,{'today':'2026-11-23','week_start':'2026-11-23'},'a','Ana')
 assert rows[0]['user_id']=='b' and rows[0]['result']==big+1
 assert [r['points'] for r in rows]==[0,0]

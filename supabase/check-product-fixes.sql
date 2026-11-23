-- Manual regression: temporary fixture accounts; transaction always rolled back. No email is sent.
begin;
create temporary table qa_result(check_name text,passed boolean);
do $$
declare a uuid:=gen_random_uuid(); b uuid:=gen_random_uuid(); outsider uuid:=gen_random_uuid(); sid bigint; invite text; qid uuid; duel uuid; day_id uuid; state jsonb; batch jsonb; before_xp integer; worker text:=repeat('qa-rollback-',4); claimed jsonb; event uuid;
begin
 insert into auth.users(id,email,email_confirmed_at,raw_user_meta_data) values
 (a,a::text||'@example.invalid',now(),'{"lifequest_language":"de"}'),
 (b,b::text||'@example.invalid',now(),'{}'),(outsider,outsider::text||'@example.invalid',null,'{}');
 insert into public.profiles(id,display_name,selected_categories,email_reminders,reminder_hour) values
 (a,'Same QA name',array['Fitness'],true,0),(b,'Same QA name',array['Fitness'],false,0),(outsider,'QA outsider',array['Fitness'],true,0)
 on conflict(id) do update set display_name=excluded.display_name,selected_categories=excluded.selected_categories,email_reminders=excluded.email_reminders,reminder_hour=0;
 perform set_config('request.jwt.claim.sub',a::text,true);
 batch:='[{"category":"Fitness","slot":1,"focus":"walk","target":4000,"title":"Walk 4000 steps","description":"Walk comfortably","minutes":20,"difficulty":2,"source":"curated","context":{"target_language":"ja"}}]'::jsonb;
 perform public.save_quest_slots(batch);
 select id into qid from public.ai_quests where user_id=a and status='active';
 batch:=jsonb_set(jsonb_set(batch,'{0,target}','6000'),'{0,difficulty}','3');
 perform public.save_quest_slots(batch,qid);
 insert into qa_result select 'completion exact XP and context',xp_awarded=20 and context->>'target_language'='ja' from public.ai_quests where id=qid;
 select id into qid from public.ai_quests where user_id=a and status='active';
 batch:=jsonb_set(batch,'{0,target}','8000'); perform public.save_quest_slots(batch,qid);
 insert into qa_result select 'same-day progression retained',points=45 from public.profiles where id=a;
 perform public.save_quest_slots(batch,qid);
 insert into qa_result select 'completion replay no extra XP',points=45 from public.profiles where id=a;
 select squad_id,invite_code into sid,invite from public.create_squad('QA rollback squad');
 perform set_config('request.jwt.claim.sub',b::text,true); perform public.join_squad(invite);
 state:=public.get_social_state(); select id into qid from public.squad_quests where squad_id=sid order by slot limit 1;
 perform public.confirm_squad_quest(qid);
 perform set_config('request.jwt.claim.sub',a::text,true); perform public.confirm_squad_quest(qid);
 insert into qa_result select 'multiplayer history exact award',exists(select 1 from jsonb_array_elements(public.get_activity_history()) x where x->>'source'='squad_quest' and (x->>'points')::integer=30);
 insert into qa_result select 'same-name ranking uses distinct IDs',count(distinct user_id)=2 and sum(weekly_points)=105 from public.get_squad_leaderboard(sid);
 duel:=public.create_friend_duel(b);
 perform set_config('request.jwt.claim.sub',b::text,true); perform public.close_friend_duel(duel,'decline');
 insert into qa_result select 'opponent can decline',status='declined' from public.friend_duels where id=duel;
 perform set_config('request.jwt.claim.sub',a::text,true); duel:=public.create_friend_duel(b); perform public.close_friend_duel(duel,'cancel');
 insert into qa_result select 'creator can cancel',status='cancelled' from public.friend_duels where id=duel;
 duel:=public.create_friend_duel(b); select code into invite from public.friend_duels where id=duel;
 perform set_config('request.jwt.claim.sub',b::text,true); perform public.join_friend_duel(invite); perform public.close_friend_duel(duel,'end');
 insert into qa_result select 'end preserves current day',status='active' and closed_at is not null from public.friend_duels where id=duel;
 perform set_config('request.jwt.claim.sub',outsider::text,true);
 begin perform public.close_friend_duel(duel,'end'); raise exception 'outsider accepted'; exception when others then if sqlerrm='outsider accepted' then raise; end if; end;
 insert into qa_result values('outsider rejected',true);
 update public.friend_duels set status='cancelled',closed_at=now()-interval '2 days' where id=duel;
 insert into public.duel_days(duel_id,day,title,unit,max_value) values(duel,date_trunc('week',now() at time zone 'UTC')::date-1,'QA past day','steps',50000) returning id into day_id;
 insert into public.duel_scores(day_id,user_id,value) values(day_id,b,1000);
 perform set_config('request.jwt.claim.sub',b::text,true); perform public.get_social_state(); perform public.get_social_state();
 insert into qa_result select 'closed duel still settles day and week once',sum(points)=85 from public.social_rewards where user_id=b and kind in('duel_day','duel_week');

 perform set_config('request.jwt.claim.sub',a::text,true); select points into before_xp from public.profiles where id=a; perform public.leave_squad(sid);
 insert into qa_result select 'leave keeps XP and history',points=before_xp and not exists(select 1 from public.squad_members where squad_id=sid and user_id=a) from public.profiles where id=a;
 insert into public.reminder_worker_keys(key_hash) values(encode(sha256(convert_to(worker,'UTF8')),'hex'));
 claimed:=public.claim_reminders(worker);
 insert into qa_result select 'only opted-in confirmed fixture claimed',exists(select 1 from jsonb_array_elements(claimed) x where x->>'email'=a::text||'@example.invalid') and not exists(select 1 from jsonb_array_elements(claimed) x where x->>'email' in(b::text||'@example.invalid',outsider::text||'@example.invalid'));
 select (x->>'id')::uuid into event from jsonb_array_elements(claimed) x where x->>'email'=a::text||'@example.invalid';
 perform public.finish_reminder(worker,event,'sent');
 insert into qa_result select 'no duplicate reminder claim',not exists(select 1 from jsonb_array_elements(public.claim_reminders(worker)) x where x->>'email'=a::text||'@example.invalid');
 begin perform public.claim_reminders('invalid'); raise exception 'invalid accepted'; exception when others then if sqlerrm='invalid accepted' then raise; end if; end;
 insert into qa_result values('invalid worker rejected',true);
 if exists(select 1 from qa_result where not passed or passed is null) then raise exception 'QA assertion failed'; end if;
end $$;
select * from qa_result;
rollback;

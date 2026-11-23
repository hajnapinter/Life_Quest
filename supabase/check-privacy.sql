-- Synthetic accounts only. No network, no mail. ALWAYS rolls back.
begin;
create temporary table qa_privacy(name text,passed boolean);
create temporary table qa_ids(a uuid,b uuid);
insert into qa_ids values(gen_random_uuid(),gen_random_uuid());
select set_config('qa.a',a::text,true),set_config('qa.b',b::text,true) from qa_ids;
do $$
declare a uuid:=current_setting('qa.a')::uuid;b uuid:=current_setting('qa.b')::uuid;sid bigint;pair uuid;dayid uuid;
begin
 insert into auth.users(id,email,email_confirmed_at,raw_user_meta_data) values
 (a,a::text||'@example.invalid',now(),'{}'),(b,b::text||'@example.invalid',now(),'{}');
 insert into auth.sessions(id,user_id,created_at,updated_at) values(gen_random_uuid(),a,now(),now());
 insert into auth.identities(id,provider_id,user_id,identity_data,provider,created_at,updated_at)
 values(gen_random_uuid(),a::text,a,jsonb_build_object('sub',a::text,'email',a::text||'@example.invalid'),'email',now(),now());
 insert into public.profiles(id,display_name,selected_categories) values(a,'Privacy QA A',array['Fitness']),(b,'Privacy QA B',array['Fitness']) on conflict do nothing;
 perform set_config('request.jwt.claim.sub',a::text,true);
 perform public.save_quest_slots('[{"category":"Fitness","slot":1,"focus":"walk","target":4000,"title":"Walk 4000 steps","description":"Walk comfortably","minutes":20,"difficulty":2,"source":"curated"}]'::jsonb);
 select squad_id into sid from public.create_squad('Privacy QA shared');
 insert into public.squad_members(squad_id,user_id) values(sid,b);
 pair:=public.create_friend_duel(b);
 insert into public.duel_days(duel_id,day,title,unit,max_value,settled,winner) values(pair,current_date-2,'QA walk','steps',20000,true,b) returning id into dayid;
 insert into public.duel_scores(day_id,user_id,value) values(dayid,a,100),(dayid,b,200);
 perform public.social_award(b,'duel_day',dayid,30);
 insert into qa_privacy values('authenticated cannot execute erasure',not has_function_privilege('authenticated','public.admin_erase_account(uuid,text)','execute'));
 insert into qa_privacy values('anonymous cannot execute erasure',not has_function_privilege('anon','public.admin_erase_account(uuid,text)','execute'));
 insert into qa_privacy values('service role cannot execute erasure',not has_function_privilege('service_role','public.admin_erase_account(uuid,text)','execute'));
 begin
  perform public.admin_erase_account(a,'wrong');
  insert into qa_privacy values('erasure requires exact confirmation',false);
 exception when raise_exception then insert into qa_privacy values('erasure requires exact confirmation',true);end;
end $$;
-- Switch to the REAL client role: postgres would otherwise bypass RLS.
grant select,insert on qa_privacy to authenticated;
select set_config('request.jwt.claim.sub',current_setting('qa.b'),true);
set local role authenticated;
insert into qa_privacy select 'B cannot read A profile',count(*)=0 from public.profiles where id=current_setting('qa.a')::uuid;
insert into qa_privacy select 'B cannot read A quests',count(*)=0 from public.ai_quests where user_id=current_setting('qa.a')::uuid;
insert into qa_privacy select 'B can read own profile',count(*)=1 from public.profiles where id=current_setting('qa.b')::uuid;
do $$ begin
 begin
  update public.profiles set points=9999 where id=current_setting('qa.b')::uuid;
  insert into qa_privacy values('client cannot write XP',false);
 exception when insufficient_privilege then insert into qa_privacy values('client cannot write XP',true);end;
end $$;
reset role;
do $$
declare a uuid:=current_setting('qa.a')::uuid;b uuid:=current_setting('qa.b')::uuid;earned_before timestamptz;earned_after timestamptz;
begin
 select earned_at into earned_before from public.weekly_xp_events() where user_id=b;
 perform public.admin_erase_account(a,'ERASE '||a::text);
 insert into qa_privacy select 'A Auth account removed',count(*)=0 from auth.users where id=a;
 insert into qa_privacy select 'A profile removed',count(*)=0 from public.profiles where id=a;
 insert into qa_privacy select 'A quests removed',count(*)=0 from public.ai_quests where user_id=a;
 insert into qa_privacy select 'A memberships removed',count(*)=0 from public.squad_members where user_id=a;
 insert into qa_privacy select 'A scores removed',count(*)=0 from public.duel_scores where user_id=a;
 insert into qa_privacy select 'B account and XP preserved',count(*)=1 from public.profiles where id=b and points=30;
 insert into qa_privacy select 'shared squad transferred to B',count(*)=1 from public.squads where name='Privacy QA shared' and created_by=b;
 select earned_at into earned_after from public.weekly_xp_events() where user_id=b;
 insert into qa_privacy values('B weekly reward effective date preserved',earned_after=earned_before);
 insert into qa_privacy select 'A sessions absent',count(*)=0 from auth.sessions where user_id=a;
 insert into qa_privacy select 'A identities absent',count(*)=0 from auth.identities where user_id=a;
 perform public.admin_erase_account(b,'ERASE '||b::text);
 insert into qa_privacy select 'last member squad removed',count(*)=0 from public.squads where name='Privacy QA shared';
end $$;
select * from qa_privacy order by name;
do $$ begin if exists(select 1 from qa_privacy where passed is distinct from true) then raise exception 'Privacy checks failed';end if;end $$;
rollback;

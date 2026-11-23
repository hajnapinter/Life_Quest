-- Synthetic accounts only, no email. All fixture scores/XP/accounts are rolled back.
begin;
create temporary table qa_uncapped(name text,passed boolean);
select set_config('qa.owner',gen_random_uuid()::text,true),set_config('qa.friend',gen_random_uuid()::text,true),set_config('qa.outsider',gen_random_uuid()::text,true),set_config('qa.day',gen_random_uuid()::text,true),set_config('qa.pair',gen_random_uuid()::text,true);
do $$
declare uid uuid;
begin
 foreach uid in array array[current_setting('qa.owner')::uuid,current_setting('qa.friend')::uuid,current_setting('qa.outsider')::uuid] loop
  insert into auth.users(id,email,email_confirmed_at,raw_user_meta_data) values(uid,uid::text||'@example.invalid',now(),'{}');
  insert into public.profiles(id,display_name,selected_categories) values(uid,'Uncapped QA',array['Fitness']) on conflict do nothing;
 end loop;
 insert into public.friend_duels(id,creator,opponent,status) values(current_setting('qa.pair')::uuid,current_setting('qa.owner')::uuid,current_setting('qa.friend')::uuid,'active');
 insert into public.duel_days(id,duel_id,day,title,unit,max_value) values(current_setting('qa.day')::uuid,current_setting('qa.pair')::uuid,(now() at time zone 'UTC')::date,'QA reading','pages',300);
end $$;
grant select,insert on qa_uncapped to authenticated;
select set_config('request.jwt.claim.sub',current_setting('qa.owner'),true);
set local role authenticated;
do $$
declare q uuid:=current_setting('qa.day')::uuid;n numeric;
begin
 foreach n in array array[0::numeric,301,50001,2147483648,9007199254740993,1234567890123456789012345678901234567890] loop
  perform public.record_duel_score(q,n);
  insert into qa_uncapped values('client can save exact total '||n::text,true);
 end loop;
 foreach n in array array[-1::numeric,1.5,'NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric,null::numeric] loop
  begin
   perform public.record_duel_score(q,n);
   raise exception 'invalid score accepted';
  exception when raise_exception then
   if sqlerrm='invalid score accepted' then raise;end if;
   insert into qa_uncapped values('invalid total rejected '||coalesce(n::text,'null'),true);
  end;
 end loop;
end $$;
reset role;
insert into qa_uncapped select 'stored large total is exact',value=1234567890123456789012345678901234567890 from public.duel_scores where day_id=current_setting('qa.day')::uuid and user_id=current_setting('qa.owner')::uuid;
select set_config('request.jwt.claim.sub',current_setting('qa.outsider'),true);
set local role authenticated;
do $$ begin
 begin
  perform public.record_duel_score(current_setting('qa.day')::uuid,999);
  raise exception 'outsider accepted';
 exception when raise_exception then if sqlerrm='outsider accepted' then raise;end if;insert into qa_uncapped values('outsider rejected',true);end;
end $$;
reset role;
-- Same rule for every legacy category ceiling, including already-created quests.
do $$
declare old_cap integer;
begin
 perform set_config('request.jwt.claim.sub',current_setting('qa.owner'),true);
 foreach old_cap in array array[300,50000,200,5,10] loop
  update public.duel_days set max_value=old_cap where id=current_setting('qa.day')::uuid;
  perform public.record_duel_score(current_setting('qa.day')::uuid,old_cap+1);
  insert into qa_uncapped select 'legacy ceiling ignored '||old_cap,value=old_cap+1 from public.duel_scores where day_id=current_setting('qa.day')::uuid and user_id=current_setting('qa.owner')::uuid;
 end loop;
 update public.duel_days set settled=true where id=current_setting('qa.day')::uuid;
 begin perform public.record_duel_score(current_setting('qa.day')::uuid,301);raise exception 'closed day accepted';exception when raise_exception then if sqlerrm='closed day accepted' then raise;end if;insert into qa_uncapped values('settled day rejected',true);end;
 update public.duel_days set settled=false,day=(now() at time zone 'UTC')::date-1 where id=current_setting('qa.day')::uuid;
 begin perform public.record_duel_score(current_setting('qa.day')::uuid,301);raise exception 'past day accepted';exception when raise_exception then if sqlerrm='past day accepted' then raise;end if;insert into qa_uncapped values('past day rejected',true);end;
 -- Settlement compares huge totals without overflowing and keeps fixed win/participation XP.
 update public.duel_scores set value=123456789012345678901234567890 where day_id=current_setting('qa.day')::uuid;
 insert into public.duel_scores(day_id,user_id,value) values(current_setting('qa.day')::uuid,current_setting('qa.friend')::uuid,123456789012345678901234567891);
 perform public.settle_friend_duel(current_setting('qa.pair')::uuid);
 insert into qa_uncapped select 'larger total wins without integer overflow',winner=current_setting('qa.friend')::uuid from public.duel_days where id=current_setting('qa.day')::uuid;
 insert into qa_uncapped select 'winner daily XP remains 35',points=35 from public.social_rewards where user_id=current_setting('qa.friend')::uuid and kind='duel_day' and source_id=current_setting('qa.day')::uuid;
 perform public.settle_friend_duel(current_setting('qa.pair')::uuid);
 insert into qa_uncapped select 'settlement remains idempotent',count(*)=2 and sum(points)=50 from public.social_rewards where kind='duel_day' and source_id=current_setting('qa.day')::uuid;
 insert into qa_uncapped values('anonymous RPC access denied',not has_function_privilege('anon','public.record_duel_score(uuid,numeric)','execute'));
end $$;
select * from qa_uncapped order by name;
do $$ begin if exists(select 1 from qa_uncapped where passed is distinct from true) then raise exception 'Uncapped competition checks failed';end if;end $$;
rollback;

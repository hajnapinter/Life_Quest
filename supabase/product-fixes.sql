-- Apply after security-hardening.sql. Atomic, repeatable; preserves existing history.
begin;
alter table public.ai_quests add column if not exists xp_awarded integer;
alter table public.ai_quests add column if not exists context jsonb not null default '{}'::jsonb;
alter table public.friend_duels add column if not exists closed_at timestamptz;
alter table public.friend_duels drop constraint if exists friend_duels_status_check;
alter table public.friend_duels add constraint friend_duels_status_check check(status in('pending','active','cancelled','declined'));

-- Reconstruct the former 20-completion daily XP cap for historical rows.
with awards as (
 select id,row_number() over(partition by user_id,(completed_at at time zone 'UTC')::date order by completed_at,id) n
 from public.ai_quests where status='completed'
) update public.ai_quests q set xp_awarded=case when a.n<=20 then 10+5*q.difficulty else 0 end
from awards a where q.id=a.id and q.xp_awarded is null;

do $$ begin
 if to_regprocedure('public.save_quest_slots_original(jsonb,uuid,text,boolean)') is null then
  alter function public.save_quest_slots(jsonb,uuid,text,boolean) rename to save_quest_slots_original;
 end if;
end $$;
revoke all on function public.save_quest_slots_original(jsonb,uuid,text,boolean) from public,anon,authenticated;

create or replace function public.save_quest_slots(quest_rows jsonb,finished_id uuid default null,rating text default 'just_right',skip boolean default false)
returns integer language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid(); old public.ai_quests; before_xp integer; after_xp integer; item jsonb;
begin
 if uid is null then raise exception 'Authentication required'; end if;
 select points into before_xp from public.profiles where id=uid for update;
 if not found then raise exception 'Profile required'; end if;
 if finished_id is not null then
  select * into old from public.ai_quests where id=finished_id and user_id=uid for update;
  if not found then raise exception 'Quest not found'; end if;
  if old.status<>'active' then return before_xp; end if;
 end if;
 after_xp:=public.save_quest_slots_original(quest_rows,finished_id,rating,skip);
 if finished_id is not null then
  update public.ai_quests set xp_awarded=case when skip then 0 else after_xp-before_xp end where id=finished_id;
 end if;
 for item in select value from jsonb_array_elements(quest_rows) loop
  if item ? 'context' and jsonb_typeof(item->'context')='object' and length((item->'context')::text)<=2048 then
   update public.ai_quests set context=item->'context' where user_id=uid and category=item->>'category'
    and slot=(item->>'slot')::integer and status='active';
  end if;
 end loop;
 return after_xp;
end $$;
revoke all on function public.save_quest_slots(jsonb,uuid,text,boolean) from public,anon;
grant execute on function public.save_quest_slots(jsonb,uuid,text,boolean) to authenticated;

create or replace function public.get_activity_history()
returns jsonb language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid(); result jsonb;
begin
 if uid is null then raise exception 'Authentication required'; end if;
 perform public.get_social_state();
 select coalesce(jsonb_agg(jsonb_build_object('id',r.source_id,'category',case when r.kind='squad_quest' then 'Squad' else 'Competition' end,
 'title',case when r.kind='squad_quest' then coalesce(q.title,'Shared squad quest')
              when r.kind='duel_day' then coalesce(d.title,'Daily competition') else 'Weekly competition bonus' end,
 'status','completed','completed_at',r.awarded_at,'points',r.points,'source',r.kind,
 'counts_as_quest',r.kind<>'duel_week') order by r.awarded_at),'[]'::jsonb)
 into result from public.social_rewards r left join public.squad_quests q on r.kind='squad_quest' and q.id=r.source_id
 left join public.duel_days d on r.kind='duel_day' and d.id=r.source_id where r.user_id=uid;
 return result;
end $$;
revoke all on function public.get_activity_history() from public,anon;
grant execute on function public.get_activity_history() to authenticated;

create or replace function public.get_squad_leaderboard(squad_id_input bigint)
returns table(user_id uuid,display_name text,weekly_points bigint,quests_completed bigint)
language plpgsql security definer set search_path=public as $$
begin
 if auth.uid() is null or not exists(select 1 from public.squad_members m where m.squad_id=squad_id_input and m.user_id=auth.uid()) then
  raise exception 'Not your squad'; end if;
 return query with awards as (
 select q.user_id,coalesce(q.xp_awarded,10+5*q.difficulty) xp,1 n from public.ai_quests q
 where q.status='completed' and q.completed_at>=date_trunc('week',now() at time zone 'UTC') at time zone 'UTC'
 union all select r.user_id,r.points,case when r.kind='duel_week' then 0 else 1 end from public.social_rewards r
 where r.awarded_at>=date_trunc('week',now() at time zone 'UTC') at time zone 'UTC'
 union all select c.user_id,h.points,1 from public.completed_challenges c join public.challenges h on h.id=c.challenge_id
 where c.created_at>=date_trunc('week',now() at time zone 'UTC') at time zone 'UTC'
 ) select p.id,p.display_name,coalesce(sum(a.xp),0)::bigint,coalesce(sum(a.n),0)::bigint
 from public.squad_members m join public.profiles p on p.id=m.user_id left join awards a on a.user_id=p.id
 where m.squad_id=squad_id_input group by p.id,p.display_name order by 3 desc,4 desc,p.id;
end $$;
revoke all on function public.get_squad_leaderboard(bigint) from public,anon;
grant execute on function public.get_squad_leaderboard(bigint) to authenticated;

create or replace function public.leave_squad(squad_id_input bigint)
returns void language plpgsql security definer set search_path=public as $$
begin
 if auth.uid() is null then raise exception 'Authentication required'; end if;
 delete from public.squad_members where squad_id=squad_id_input and user_id=auth.uid();
 if not found then raise exception 'Not your squad'; end if;
end $$;
revoke all on function public.leave_squad(bigint) from public,anon;
grant execute on function public.leave_squad(bigint) to authenticated;

create or replace function public.close_friend_duel(pair_id uuid,action text)
returns void language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid(); pair public.friend_duels;
begin
 if uid is null then raise exception 'Authentication required'; end if;
 select * into pair from public.friend_duels where id=pair_id for update;
 if not found or (uid is distinct from pair.creator and uid is distinct from pair.opponent) then raise exception 'Not your competition'; end if;
 if action='decline' and pair.status='pending' and uid=pair.opponent then
  update public.friend_duels set status='declined',closed_at=now() where id=pair.id;
 elsif action='cancel' and pair.status='pending' and uid=pair.creator then
  update public.friend_duels set status='cancelled',closed_at=now() where id=pair.id;
 elsif action='end' and pair.status='active' then
  -- Today's entries still settle fairly; no new day is generated after today.
  update public.friend_duels set closed_at=coalesce(closed_at,now()) where id=pair.id;
 else raise exception 'This action is not available'; end if;
end $$;
revoke all on function public.close_friend_duel(uuid,text) from public,anon;
grant execute on function public.close_friend_duel(uuid,text) to authenticated;
create or replace function public.settle_friend_duel(pair_id uuid)
returns void language plpgsql security definer set search_path=public as $$
declare pair public.friend_duels; d public.duel_days; a integer;b integer;person uuid;w date;wa integer;wb integer;event_id uuid;
 today date:=(now() at time zone 'UTC')::date;
begin
 select * into pair from public.friend_duels where id=pair_id for update;
 if not found or pair.opponent is null or pair.status not in('active','cancelled') then return; end if;
 perform 1 from public.profiles where id in(pair.creator,pair.opponent) order by id for update;
 for d in select * from public.duel_days where duel_id=pair.id and day<today and not settled order by day for update loop
  select value into a from public.duel_scores where day_id=d.id and user_id=pair.creator;
  select value into b from public.duel_scores where day_id=d.id and user_id=pair.opponent;
  person=case when coalesce(a,0)>coalesce(b,0) then pair.creator when coalesce(b,0)>coalesce(a,0) then pair.opponent else null end;
  update public.duel_days set settled=true,winner=person where id=d.id;
  if a is not null then perform public.social_award(pair.creator,'duel_day',d.id,15+case when person=pair.creator then 20 when person is null then 10 else 0 end); end if;
  if b is not null then perform public.social_award(pair.opponent,'duel_day',d.id,15+case when person=pair.opponent then 20 when person is null then 10 else 0 end); end if;
 end loop;
 for w in select distinct date_trunc('week',day::timestamp)::date from public.duel_days
   where duel_id=pair.id and day<date_trunc('week',today::timestamp)::date loop
  if exists(select 1 from public.duel_weeks where duel_id=pair.id and week_start=w) then continue; end if;
  select count(*) filter(where winner=pair.creator),count(*) filter(where winner=pair.opponent) into wa,wb
    from public.duel_days where duel_id=pair.id and day>=w and day<w+7 and settled;
  if not exists(select 1 from public.duel_scores s join public.duel_days x on x.id=s.day_id where x.duel_id=pair.id and x.day>=w and x.day<w+7) then continue; end if;
  person=case when wa>wb then pair.creator when wb>wa then pair.opponent else null end;
  insert into public.duel_weeks(duel_id,week_start,winner,tied) values(pair.id,w,person,person is null) returning id into event_id;
  if person is not null then perform public.social_award(person,'duel_week',event_id,50);
  else
   if exists(select 1 from public.duel_scores r join public.duel_days x on x.id=r.day_id where x.duel_id=pair.id and x.day>=w and x.day<w+7 and r.user_id=pair.creator) then perform public.social_award(pair.creator,'duel_week',event_id,20); end if;
   if exists(select 1 from public.duel_scores r join public.duel_days x on x.id=r.day_id where x.duel_id=pair.id and x.day>=w and x.day<w+7 and r.user_id=pair.opponent) then perform public.social_award(pair.opponent,'duel_week',event_id,20); end if;
  end if;
 end loop;
end $$;
revoke all on function public.settle_friend_duel(uuid) from public,anon,authenticated;


create or replace function public.get_social_state()
returns jsonb language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid();s record;pair record;i integer;kind integer;candidate integer;shift integer;catalog jsonb;team_catalog jsonb;
 today date:=(now() at time zone 'UTC')::date;week date:=date_trunc('week',now() at time zone 'UTC')::date;
 squads_json jsonb;duels_json jsonb;friends_json jsonb;
begin
 if uid is null then raise exception 'Authentication required'; end if;
 -- Lock all involved profiles in one global order before settling several pairs.
 perform 1 from public.profiles where id=uid or id in(
  select creator from public.friend_duels where uid in(creator,opponent) and status in('active','cancelled')
  union select opponent from public.friend_duels where uid in(creator,opponent) and status in('active','cancelled')
 ) order by id for update;
 catalog='[{"title":"Who can walk more steps today?","unit":"steps","max":50000},{"title":"Who can read more book pages today?","unit":"pages","max":300},{"title":"Who can learn more new words today?","unit":"words","max":200},{"title":"Who can cook more new recipes today?","unit":"recipes","max":5},{"title":"Who can explore more new places today?","unit":"places","max":10}]'::jsonb;
 team_catalog='[{"title": "Explore a new place together", "description": "Meet at a new park, neighbourhood or free exhibition. At least two of you should go together."}, {"title": "Teach one another a new skill", "description": "Each person shares one practical skill, recipe, language phrase or creative technique with the group."}, {"title": "Cook a recipe from a new cuisine together", "description": "Choose a manageable recipe, divide the tasks and make a meal together within your budget."}, {"title": "Try a new sport together", "description": "Choose a free beginner activity you can all try at a comfortable pace."}, {"title": "Organise a screen-free catch-up", "description": "Meet for a board game, conversation or walk and put your phones away."}, {"title": "Visit a free exhibition together", "description": "Choose a museum, gallery or community exhibition none of you has seen before."}, {"title": "Discover a new walking route together", "description": "Pick an accessible local route that is new to the group and walk it together."}, {"title": "Join a free workshop as a squad", "description": "Find a real community class or workshop and attend it with at least one squadmate."}, {"title": "Organise a plant, book or recipe swap", "description": "Meet and exchange a cutting, a book you already own or a recipe you would recommend."}]'::jsonb;
 for s in select q.id from public.squads q join public.squad_members m on m.squad_id=q.id where m.user_id=uid order by q.id loop
  -- Coordinate concurrent first visits without locking participant profiles.
  perform 1 from public.squads where id=s.id for update;
  for i in 1..3 loop
   kind=((s.id%9)+((week-date '2026-01-05')/7)*3+i-1)%9;
   insert into public.squad_quests(squad_id,week_start,slot,title,description)
   values(s.id,week,i,team_catalog->kind->>'title',team_catalog->kind->>'description')
   on conflict do nothing;
  end loop;
 end loop;
 for pair in select * from public.friend_duels where uid in(creator,opponent) and status in('active','cancelled') order by id loop
  perform public.settle_friend_duel(pair.id);
  if pair.status<>'active' then continue; end if;
  if pair.closed_at is not null and today>(pair.closed_at at time zone 'UTC')::date then
   update public.friend_duels set status='cancelled' where id=pair.id;
   continue;
  end if;
  kind=(get_byte(decode(md5(pair.id::text),'hex'),0)+(today-date '2026-01-01'))%5;
  -- Prefer a different metric from the participants' other competitions today.
  for shift in 0..4 loop
   candidate=(kind+shift)%5;
   if not exists(select 1 from public.duel_days x join public.friend_duels p on p.id=x.duel_id
     where x.day=today and x.unit=catalog->candidate->>'unit' and x.duel_id<>pair.id
     and (p.creator in(pair.creator,pair.opponent) or p.opponent in(pair.creator,pair.opponent))) then
    kind=candidate;exit;
   end if;
  end loop;
  insert into public.duel_days(duel_id,day,title,unit,max_value)
   values(pair.id,today,catalog->kind->>'title',catalog->kind->>'unit',(catalog->kind->>'max')::integer)
   on conflict do nothing;
 end loop;
 select coalesce(jsonb_agg(jsonb_build_object('id',q.id,'name',q.name,'invite_code',q.invite_code,
  'members',(select coalesce(jsonb_agg(jsonb_build_object('id',p.id,'name',p.display_name) order by p.display_name),'[]') from public.squad_members m join public.profiles p on p.id=m.user_id where m.squad_id=q.id),
  'quests',(select coalesce(jsonb_agg(jsonb_build_object('id',x.id,'title',x.title,'description',x.description,
    'confirmed',(select coalesce(jsonb_agg(c.user_id),'[]') from public.squad_confirmations c where c.quest_id=x.id)) order by x.slot),'[]') from public.squad_quests x where x.squad_id=q.id and x.week_start=week))), '[]')
 into squads_json from public.squads q where exists(select 1 from public.squad_members m where m.squad_id=q.id and m.user_id=uid);
 select coalesce(jsonb_agg(jsonb_build_object('id',p.id,'name',p.display_name)),'[]') into friends_json from public.profiles p
 where p.id<>uid and exists(select 1 from public.squad_members a join public.squad_members b on a.squad_id=b.squad_id where a.user_id=uid and b.user_id=p.id);
 select coalesce(jsonb_agg(jsonb_build_object('id',p.id,'code',p.code,'creator',p.creator,'opponent',p.opponent,'status',p.status,'closed_at',p.closed_at,
  'creator_name',(select display_name from public.profiles where id=p.creator),'opponent_name',(select display_name from public.profiles where id=p.opponent),
  'days',(select coalesce(jsonb_agg(jsonb_build_object('id',d.id,'day',d.day,'title',d.title,'unit',d.unit,'max',d.max_value,'settled',d.settled,'winner',d.winner,
    'scores',(select coalesce(jsonb_agg(jsonb_build_object('user_id',r.user_id,'value',r.value)),'[]') from public.duel_scores r where r.day_id=d.id)) order by d.day desc),'[]') from public.duel_days d where d.duel_id=p.id and d.day>=week-7),
  'weeks',(select coalesce(jsonb_agg(jsonb_build_object('week',w.week_start,'winner',w.winner,'tied',w.tied) order by w.week_start desc),'[]') from public.duel_weeks w where w.duel_id=p.id and w.week_start>=week-28))), '[]')
 into duels_json from public.friend_duels p where uid in(p.creator,p.opponent);
 return jsonb_build_object('today',today,'week_start',week,'squads',squads_json,'duels',duels_json,'friends',friends_json,
  'points',(select points from public.profiles where id=uid));
end $$;
create or replace function public.join_friend_duel(invite text)
returns uuid language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid();pair public.friend_duels;existing uuid;
begin
 if uid is null or not exists(select 1 from public.profiles where id=uid) then raise exception 'Profile required'; end if;
 select * into pair from public.friend_duels where code=upper(trim(invite)) for update;
 if not found then raise exception 'Invitation not found'; end if;
 if pair.status not in('pending','active') then raise exception 'This invitation is closed'; end if;
 if pair.creator=uid then raise exception 'Share this invitation with a friend'; end if;
 if pair.opponent is not null and pair.opponent<>uid then raise exception 'This invitation belongs to another friend'; end if;
 select id into existing from public.friend_duels where least(creator,opponent)=least(pair.creator,uid) and greatest(creator,opponent)=greatest(pair.creator,uid) and id<>pair.id;
 if found then return existing; end if;
 update public.friend_duels set opponent=uid,status='active' where id=pair.id;
 return pair.id;
end $$;
create or replace function public.create_friend_duel(friend_id uuid default null)
returns uuid language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid();pair_id uuid;
begin
 if uid is null or not exists(select 1 from public.profiles where id=uid) then raise exception 'Profile required'; end if;
 if friend_id=uid then raise exception 'Choose another person'; end if;
 if friend_id is not null then
  if not exists(select 1 from public.squad_members a join public.squad_members b on a.squad_id=b.squad_id where a.user_id=uid and b.user_id=friend_id) then raise exception 'Use an invite code to challenge someone outside your squads'; end if;
  select id into pair_id from public.friend_duels where least(creator,opponent)=least(uid,friend_id) and greatest(creator,opponent)=greatest(uid,friend_id);
  if found then
   if exists(select 1 from public.friend_duels where id=pair_id and status in('cancelled','declined')) then
    update public.friend_duels set creator=uid,opponent=friend_id,status='pending',closed_at=null,code=upper(substr(replace(gen_random_uuid()::text,'-',''),1,12)) where id=pair_id;
   end if;
   return pair_id;
  end if;
 end if;
 if (select count(*) from public.friend_duels where creator=uid and status='pending')>=20 then raise exception 'You already have 20 pending invitations'; end if;
 insert into public.friend_duels(creator,opponent) values(uid,friend_id) returning id into pair_id;
 return pair_id;
end $$;
commit;

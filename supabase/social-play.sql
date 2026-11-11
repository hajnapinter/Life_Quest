begin;
create table if not exists public.squad_quests (
 id uuid primary key default gen_random_uuid(), squad_id bigint not null references public.squads(id) on delete cascade,
 week_start date not null, slot integer not null check(slot between 1 and 3),title text not null,description text not null,
 unique(squad_id,week_start,slot)
);
create table if not exists public.squad_confirmations (
 quest_id uuid not null references public.squad_quests(id) on delete cascade,
 user_id uuid not null references public.profiles(id) on delete cascade,
 created_at timestamptz not null default now(),primary key(quest_id,user_id)
);
create table if not exists public.friend_duels (
 id uuid primary key default gen_random_uuid(), code text not null unique default upper(substr(replace(gen_random_uuid()::text,'-',''),1,12)),
 creator uuid not null references public.profiles(id),opponent uuid references public.profiles(id),
 status text not null default 'pending' check(status in('pending','active')),
 created_at timestamptz not null default now(),check(creator<>opponent)
);
create unique index if not exists duel_unique_pair on public.friend_duels(least(creator,opponent),greatest(creator,opponent)) where opponent is not null;
create table if not exists public.duel_days (
 id uuid primary key default gen_random_uuid(), duel_id uuid not null references public.friend_duels(id) on delete cascade,
 day date not null,title text not null,unit text not null,max_value integer not null,
 settled boolean not null default false,winner uuid references public.profiles(id),unique(duel_id,day)
);
create table if not exists public.duel_scores (
 day_id uuid not null references public.duel_days(id) on delete cascade,user_id uuid not null references public.profiles(id),
 value integer not null check(value>=0),updated_at timestamptz not null default now(),primary key(day_id,user_id)
);
create table if not exists public.duel_weeks (
 id uuid primary key default gen_random_uuid(),duel_id uuid not null references public.friend_duels(id) on delete cascade,
 week_start date not null,winner uuid references public.profiles(id),tied boolean not null default false,
 unique(duel_id,week_start)
);
create table if not exists public.social_rewards (
 user_id uuid not null references public.profiles(id),kind text not null,source_id uuid not null,points integer not null check(points>0),
 awarded_at timestamptz not null default now(),primary key(user_id,kind,source_id)
);
alter table public.squad_quests enable row level security;
alter table public.squad_confirmations enable row level security;
alter table public.friend_duels enable row level security;
alter table public.duel_days enable row level security;
alter table public.duel_scores enable row level security;
alter table public.duel_weeks enable row level security;
alter table public.social_rewards enable row level security;
revoke all on public.squad_quests,public.squad_confirmations,public.friend_duels,public.duel_days,public.duel_scores,public.duel_weeks,public.social_rewards from anon,authenticated;

create or replace function public.social_award(person uuid, reward_kind text, event_id uuid, xp integer)
returns void language plpgsql security definer set search_path=public as $$
begin
 insert into public.social_rewards(user_id,kind,source_id,points) values(person,reward_kind,event_id,xp) on conflict do nothing;
 if found then update public.profiles set points=points+xp where id=person; end if;
end $$;
revoke all on function public.social_award(uuid,text,uuid,integer) from public,anon,authenticated;

create or replace function public.settle_friend_duel(pair_id uuid)
returns void language plpgsql security definer set search_path=public as $$
declare pair public.friend_duels; d public.duel_days; a integer;b integer;person uuid;w date;wa integer;wb integer;event_id uuid;
 today date:=(now() at time zone 'UTC')::date;
begin
 select * into pair from public.friend_duels where id=pair_id for update;
 if not found or pair.status<>'active' then return; end if;
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

create or replace function public.create_friend_duel(friend_id uuid default null)
returns uuid language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid();pair_id uuid;
begin
 if uid is null or not exists(select 1 from public.profiles where id=uid) then raise exception 'Profile required'; end if;
 if friend_id=uid then raise exception 'Choose another person'; end if;
 if friend_id is not null then
  if not exists(select 1 from public.squad_members a join public.squad_members b on a.squad_id=b.squad_id where a.user_id=uid and b.user_id=friend_id) then raise exception 'Use an invite code to challenge someone outside your squads'; end if;
  select id into pair_id from public.friend_duels where least(creator,opponent)=least(uid,friend_id) and greatest(creator,opponent)=greatest(uid,friend_id);
  if found then return pair_id; end if;
 end if;
 if (select count(*) from public.friend_duels where creator=uid and status='pending')>=20 then raise exception 'You already have 20 pending invitations'; end if;
 insert into public.friend_duels(creator,opponent) values(uid,friend_id) returning id into pair_id;
 return pair_id;
end $$;

create or replace function public.join_friend_duel(invite text)
returns uuid language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid();pair public.friend_duels;existing uuid;
begin
 if uid is null or not exists(select 1 from public.profiles where id=uid) then raise exception 'Profile required'; end if;
 select * into pair from public.friend_duels where code=upper(trim(invite)) for update;
 if not found then raise exception 'Invitation not found'; end if;
 if pair.creator=uid then raise exception 'Share this invitation with a friend'; end if;
 if pair.opponent is not null and pair.opponent<>uid then raise exception 'This invitation belongs to another friend'; end if;
 select id into existing from public.friend_duels where least(creator,opponent)=least(pair.creator,uid) and greatest(creator,opponent)=greatest(pair.creator,uid) and id<>pair.id;
 if found then return existing; end if;
 update public.friend_duels set opponent=uid,status='active' where id=pair.id;
 return pair.id;
end $$;

create or replace function public.record_duel_score(quest_id uuid, result_value integer)
returns void language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid();d public.duel_days;pair public.friend_duels;
begin
 if uid is null then raise exception 'Authentication required'; end if;
 select * into d from public.duel_days where id=quest_id for update;
 if not found then raise exception 'Daily quest not found'; end if;
 select * into pair from public.friend_duels where id=d.duel_id;
 if (uid is distinct from pair.creator and uid is distinct from pair.opponent) or pair.status<>'active' then raise exception 'Not your competition'; end if;
 if d.day<>(now() at time zone 'UTC')::date or d.settled then raise exception 'This day is closed'; end if;
 if result_value is null or result_value<0 or result_value>d.max_value then raise exception 'Result outside allowed range'; end if;
 insert into public.duel_scores(day_id,user_id,value) values(d.id,uid,result_value)
 on conflict(day_id,user_id) do update set value=excluded.value,updated_at=now();
end $$;

create or replace function public.confirm_squad_quest(quest_id uuid)
returns void language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid();q public.squad_quests;person uuid;
begin
 if uid is null then raise exception 'Authentication required'; end if;
 select * into q from public.squad_quests where id=quest_id for update;
 if not found or not exists(select 1 from public.squad_members where squad_id=q.squad_id and user_id=uid) then raise exception 'Not your squad quest'; end if;
 if q.week_start<>date_trunc('week',now() at time zone 'UTC')::date then raise exception 'This squad week is closed'; end if;
 insert into public.squad_confirmations(quest_id,user_id) values(q.id,uid) on conflict do nothing;
 if (select count(*) from public.squad_confirmations where squad_confirmations.quest_id=q.id)>=2 then
  perform 1 from public.profiles where id in(select user_id from public.squad_confirmations where squad_confirmations.quest_id=q.id) order by id for update;
  for person in select user_id from public.squad_confirmations where squad_confirmations.quest_id=q.id loop
   perform public.social_award(person,'squad_quest',q.id,30);
  end loop;
 end if;
end $$;

create or replace function public.get_social_state()
returns jsonb language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid();s record;pair record;i integer;kind integer;candidate integer;shift integer;catalog jsonb;team_catalog jsonb;
 today date:=(now() at time zone 'UTC')::date;week date:=date_trunc('week',now() at time zone 'UTC')::date;
 squads_json jsonb;duels_json jsonb;friends_json jsonb;
begin
 if uid is null then raise exception 'Authentication required'; end if;
 -- Lock all involved profiles in one global order before settling several pairs.
 perform 1 from public.profiles where id=uid or id in(
  select creator from public.friend_duels where uid in(creator,opponent) and status='active'
  union select opponent from public.friend_duels where uid in(creator,opponent) and status='active'
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
 for pair in select * from public.friend_duels where uid in(creator,opponent) and status='active' order by id loop
  perform public.settle_friend_duel(pair.id);
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
 select coalesce(jsonb_agg(jsonb_build_object('id',p.id,'code',p.code,'creator',p.creator,'opponent',p.opponent,'status',p.status,
  'creator_name',(select display_name from public.profiles where id=p.creator),'opponent_name',(select display_name from public.profiles where id=p.opponent),
  'days',(select coalesce(jsonb_agg(jsonb_build_object('id',d.id,'day',d.day,'title',d.title,'unit',d.unit,'max',d.max_value,'settled',d.settled,'winner',d.winner,
    'scores',(select coalesce(jsonb_agg(jsonb_build_object('user_id',r.user_id,'value',r.value)),'[]') from public.duel_scores r where r.day_id=d.id)) order by d.day desc),'[]') from public.duel_days d where d.duel_id=p.id and d.day>=week-7),
  'weeks',(select coalesce(jsonb_agg(jsonb_build_object('week',w.week_start,'winner',w.winner,'tied',w.tied) order by w.week_start desc),'[]') from public.duel_weeks w where w.duel_id=p.id and w.week_start>=week-28))), '[]')
 into duels_json from public.friend_duels p where uid in(p.creator,p.opponent);
 return jsonb_build_object('today',today,'week_start',week,'squads',squads_json,'duels',duels_json,'friends',friends_json,
  'points',(select points from public.profiles where id=uid));
end $$;

revoke all on function public.create_friend_duel(uuid),public.join_friend_duel(text),public.record_duel_score(uuid,integer),public.confirm_squad_quest(uuid),public.get_social_state() from public,anon;
grant execute on function public.create_friend_duel(uuid),public.join_friend_duel(text),public.record_duel_score(uuid,integer),public.confirm_squad_quest(uuid),public.get_social_state() to authenticated;

create or replace function public.get_weekly_leaderboard()
returns table(display_name text,weekly_points bigint,quests_completed bigint)
language sql stable security definer set search_path=public as $$
 with awards as (
  select cc.user_id,c.points,1 as quests from public.completed_challenges cc join public.challenges c on c.id=cc.challenge_id where cc.completed_on>=date_trunc('week',current_date)::date
  union all select user_id,10+5*difficulty,1 from public.ai_quests where status='completed' and completed_at>=date_trunc('week',now())
  union all select user_id,points,case when kind='squad_quest' then 1 else 0 end from public.social_rewards where awarded_at>=date_trunc('week',now())
 ) select p.display_name,sum(a.points)::bigint,sum(a.quests)::bigint from awards a join public.profiles p on p.id=a.user_id
 group by p.id,p.display_name order by 2 desc,3 desc,1 asc limit 50;
$$;

-- Refresh existing experience quests without changing history, completion or XP.
update public.ai_quests set title='Try a sport you have never tried',description='Choose a beginner activity you have not tried. Move at a comfortable pace.',target=1,source='curated' where status='active' and category='Fitness' and focus='new_sport';
update public.ai_quests set title='Try a beginner yoga class',description='Use a beginner video or a free community session. Adapt poses to your comfort.',target=1,source='curated' where status='active' and category='Fitness' and focus='yoga';
update public.ai_quests set title='Listen to an episode about investing basics',description='Pick an educational source. Write down one idea; this quest does not involve buying investments.',target=1,source='curated' where status='active' and category='Finance' and focus='financial_learning';
update public.ai_quests set title='Try a hobby you have never tried',description='Try drawing, origami, writing or another hobby using materials you already have.',target=1,source='curated' where status='active' and category='Personal Growth' and focus='new_hobby';
update public.ai_quests set title='Explore a new place nearby',description='Choose a public place that genuinely interests you.',target=1,source='curated' where status='active' and category='Adventure' and focus='new_place';
update public.ai_quests set title='Try a different walking route',description='Choose a safe, accessible route you have not tried before.',target=1,source='curated' where status='active' and category='Adventure' and focus='new_route';
update public.ai_quests set title='Find a free local event you would like to attend',description='Check the real date and availability, then pick an event that fits you.',target=1,source='curated' where status='active' and category='Adventure' and focus='local_event';
update public.ai_quests set title='Try a recipe from a cuisine you have never cooked',description='Choose a manageable recipe or technique and use ingredients within your budget.',target=1,source='curated' where status='active' and category='Adventure' and focus='new_experience';
update public.ai_quests set title='Get a new plant or swap a cutting with a friend',description='A free plant swap or a public garden counts. Pick the option that interests you.',target=1,source='curated' where status='active' and category='Adventure' and focus='nature';
commit;

-- Apply after product-fixes.sql and reminders.sql. No historical prizes before activation.
begin;
create table if not exists public.leaderboard_seasons (
 singleton boolean primary key default true check(singleton), starts_on date not null
);
insert into public.leaderboard_seasons(singleton,starts_on)
 values(true,date_trunc('week',now() at time zone 'UTC')::date) on conflict do nothing;
create table if not exists public.leaderboard_weeks (
 week_start date primary key, settled_at timestamptz not null default now()
);
create table if not exists public.leaderboard_prizes (
 week_start date not null references public.leaderboard_weeks(week_start),user_id uuid not null references public.profiles(id),
 place integer not null check(place between 1 and 3),points integer not null check(points in(100,50,25)),
 event_id uuid not null default gen_random_uuid(),primary key(week_start,user_id),unique(week_start,place)
);
alter table public.leaderboard_seasons enable row level security;
alter table public.leaderboard_weeks enable row level security;
alter table public.leaderboard_prizes enable row level security;
revoke all on public.leaderboard_seasons,public.leaderboard_weeks,public.leaderboard_prizes from anon,authenticated;

create or replace function public.weekly_xp_events()
returns table(user_id uuid,earned_at timestamptz,xp integer,quests integer)
language sql stable security definer set search_path=public as $$
 select q.user_id,q.completed_at,coalesce(q.xp_awarded,10+5*q.difficulty),1 from public.ai_quests q where q.status='completed'
 union all
 select r.user_id,case when r.kind='duel_day' then (d.day::timestamp+interval '23 hours 59 minutes') at time zone 'UTC'
                      when r.kind='duel_week' then ((w.week_start+6)::timestamp+interval '23 hours 59 minutes') at time zone 'UTC'
                      else r.awarded_at end,r.points,case when r.kind='duel_week' then 0 else 1 end
 from public.social_rewards r left join public.duel_days d on r.kind='duel_day' and d.id=r.source_id
 left join public.duel_weeks w on r.kind='duel_week' and w.id=r.source_id where r.kind<>'leaderboard_week'
 union all select c.user_id,c.created_at,h.points,1 from public.completed_challenges c join public.challenges h on h.id=c.challenge_id;
$$;
revoke all on function public.weekly_xp_events() from public,anon,authenticated;

create or replace function public.settle_all_social()
returns void language plpgsql security definer set search_path=public as $$
declare pair record;
begin
 perform 1 from public.profiles order by id for update;
 for pair in select id from public.friend_duels where opponent is not null and status in('active','cancelled') order by id loop
  perform public.settle_friend_duel(pair.id);
 end loop;
end $$;
revoke all on function public.settle_all_social() from public,anon,authenticated;

create or replace function public.settle_weekly_leaderboard()
returns void language plpgsql security definer set search_path=public as $$
declare w date; start_day date; current_week date:=date_trunc('week',now() at time zone 'UTC')::date; person record; prize integer; prize_event uuid;
begin
 -- Caller settles social XP and locks profiles in one order first.
 perform pg_advisory_xact_lock(hashtext('lifequest-weekly-podium'));
 select starts_on into start_day from public.leaderboard_seasons where singleton;
 for w in select generate_series(start_day,current_week-7,interval '7 days')::date loop
  insert into public.leaderboard_weeks(week_start) values(w) on conflict do nothing;
  if not found then continue; end if;
  for person in
   with totals as (select e.user_id,sum(e.xp) xp,sum(e.quests) quests,max(e.earned_at) reached_at
      from public.weekly_xp_events() e where e.earned_at>=w::timestamp at time zone 'UTC'
      and e.earned_at<(w+7)::timestamp at time zone 'UTC' group by e.user_id having sum(e.xp)>0)
   select *,row_number() over(order by xp desc,quests desc,reached_at,user_id)::integer place from totals
   order by xp desc,quests desc,reached_at,user_id limit 3 loop
    prize:=case person.place when 1 then 100 when 2 then 50 else 25 end;
    insert into public.leaderboard_prizes(week_start,user_id,place,points) values(w,person.user_id,person.place,prize)
     returning event_id into prize_event;
    perform public.social_award(person.user_id,'leaderboard_week',prize_event,prize);
   end loop;
 end loop;
end $$;
revoke all on function public.settle_weekly_leaderboard() from public,anon,authenticated;

create or replace function public.get_global_weekly_ranking()
returns jsonb language plpgsql security definer set search_path=public as $$
declare w date:=date_trunc('week',now() at time zone 'UTC')::date; result jsonb;
begin
 if auth.uid() is null then raise exception 'Authentication required'; end if;
 perform public.settle_all_social();
 perform public.settle_weekly_leaderboard();
 with totals as (select e.user_id,sum(e.xp) xp,sum(e.quests) quests,max(e.earned_at) reached_at
  from public.weekly_xp_events() e where e.earned_at>=w::timestamp at time zone 'UTC'
  and e.earned_at<(w+7)::timestamp at time zone 'UTC' group by e.user_id),
 ranked as (select p.id,p.display_name,coalesce(t.xp,0) xp,coalesce(t.quests,0) quests,
  row_number() over(order by coalesce(t.xp,0) desc,coalesce(t.quests,0) desc,t.reached_at nulls last,p.id) place,
  case when length(u.raw_user_meta_data->'lifequest_profile'->>'photo')<=20000
       then u.raw_user_meta_data->'lifequest_profile'->>'photo' else null end photo
  from public.profiles p left join totals t on t.user_id=p.id left join auth.users u on u.id=p.id)
 select coalesce(jsonb_agg(jsonb_build_object('user_id',id,'name',display_name,'points',xp,'quests',quests,'place',place,'photo',photo) order by place),'[]'::jsonb)
 into result from ranked;
 return jsonb_build_object('week_start',w,'rows',result,'your_total',(select points from public.profiles where id=auth.uid()),'prizes',(
  select coalesce(jsonb_agg(jsonb_build_object('week',x.week_start,'place',x.place,'points',x.points)),'[]')
  from public.leaderboard_prizes x where x.user_id=auth.uid() and x.week_start>=w-28));
end $$;
revoke all on function public.get_global_weekly_ranking() from public,anon;
grant execute on function public.get_global_weekly_ranking() to authenticated;

-- Preserve the existing limited worker credential and scheduling contract.
do $$ begin
 if to_regprocedure('public.settle_due_competitions_original(text)') is null then
  alter function public.settle_due_competitions(text) rename to settle_due_competitions_original;
 end if;
end $$;
revoke all on function public.settle_due_competitions_original(text) from public,anon,authenticated;
create or replace function public.settle_due_competitions(worker_key text)
returns void language plpgsql security definer set search_path=public as $$
begin
 perform public.check_reminder_worker(worker_key);
 perform public.settle_all_social();
 perform public.settle_due_competitions_original(worker_key);
 perform public.settle_weekly_leaderboard();
end $$;
revoke all on function public.settle_due_competitions(text) from public,authenticated;
grant execute on function public.settle_due_competitions(text) to anon;

-- Keep original timestamps/category semantics for the Recap; bonuses never count as quests.
create or replace function public.get_activity_history()
returns jsonb language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid(); result jsonb;
begin
 if uid is null then raise exception 'Authentication required'; end if;
 perform public.get_social_state();
 select coalesce(jsonb_agg(jsonb_build_object('id',r.source_id,
 'category',case when r.kind='squad_quest' then 'Squad' when r.kind='leaderboard_week' then 'Leaderboard' else 'Competition' end,
 'title',case when r.kind='squad_quest' then coalesce(q.title,'Shared squad quest') when r.kind='duel_day' then coalesce(d.title,'Daily competition')
              when r.kind='leaderboard_week' then 'Weekly leaderboard reward' else 'Weekly competition bonus' end,
 'status','completed','completed_at',r.awarded_at,'points',r.points,'source',r.kind,
 'counts_as_quest',r.kind not in('duel_week','leaderboard_week')) order by r.awarded_at),'[]'::jsonb)
 into result from public.social_rewards r left join public.squad_quests q on r.kind='squad_quest' and q.id=r.source_id
 left join public.duel_days d on r.kind='duel_day' and d.id=r.source_id where r.user_id=uid;
 return result;
end $$;

create or replace function public.join_friend_duel(invite text)
returns uuid language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid(); pair public.friend_duels; existing public.friend_duels;
begin
 if uid is null or not exists(select 1 from public.profiles where id=uid) then raise exception 'Profile required'; end if;
 select * into pair from public.friend_duels where code=regexp_replace(upper(trim(invite)),'[[:space:]-]','','g');
 if not found then raise exception 'Invitation not found'; end if;
 if pair.creator=uid then raise exception 'Share this invitation with a friend'; end if;
 if pair.status not in('pending','active') or pair.closed_at is not null then raise exception 'This invitation is closed'; end if;
 if pair.opponent is not null and pair.opponent<>uid then raise exception 'This invitation belongs to another friend'; end if;
 perform 1 from public.profiles where id in(uid,pair.creator) order by id for update;
 select * into pair from public.friend_duels where id=pair.id for update;
 if pair.status not in('pending','active') or pair.closed_at is not null then raise exception 'This invitation is closed'; end if;
 if pair.opponent is not null and pair.opponent<>uid then raise exception 'This invitation belongs to another friend'; end if;
 select * into existing from public.friend_duels where least(creator,opponent)=least(pair.creator,uid)
  and greatest(creator,opponent)=greatest(pair.creator,uid) and id<>pair.id for update;
 if found then
  if existing.status in('cancelled','declined') then
   update public.friend_duels set status='active',closed_at=null where id=existing.id;
  end if;
  if pair.status='pending' then update public.friend_duels set status='cancelled',closed_at=now() where id=pair.id; end if;
  return existing.id;
 end if;
 update public.friend_duels set opponent=uid,status='active' where id=pair.id;
 return pair.id;
end $$;

create or replace function public.get_squad_leaderboard(squad_id_input bigint)
returns table(user_id uuid,display_name text,weekly_points bigint,quests_completed bigint)
language plpgsql security definer set search_path=public as $$
begin
 if auth.uid() is null or not exists(select 1 from public.squad_members m where m.squad_id=squad_id_input and m.user_id=auth.uid()) then raise exception 'Not your squad';end if;
 return query select p.id,p.display_name,coalesce(sum(e.xp),0)::bigint,coalesce(sum(e.quests),0)::bigint
 from public.squad_members m join public.profiles p on p.id=m.user_id left join public.weekly_xp_events() e
 on e.user_id=p.id and e.earned_at>=date_trunc('week',now() at time zone 'UTC') at time zone 'UTC'
 where m.squad_id=squad_id_input group by p.id,p.display_name order by 3 desc,4 desc,p.id;
end $$;
commit;

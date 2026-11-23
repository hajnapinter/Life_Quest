-- Apply AFTER weekly-leaderboard.sql. Installs an administrator-only procedure.
-- This migration does NOT delete any account. Never grant this function to clients.
begin;

-- A deleted opponent's match must not remove the surviving user's weekly XP.
create or replace function public.weekly_xp_events()
returns table(user_id uuid,earned_at timestamptz,xp integer,quests integer)
language sql stable security definer set search_path=public as $$
 select q.user_id,q.completed_at,coalesce(q.xp_awarded,10+5*q.difficulty),1 from public.ai_quests q where q.status='completed'
 union all
 select r.user_id,case when r.kind='duel_day' then coalesce((d.day::timestamp+interval '23 hours 59 minutes') at time zone 'UTC',r.awarded_at)
                      when r.kind='duel_week' then coalesce(((w.week_start+6)::timestamp+interval '23 hours 59 minutes') at time zone 'UTC',r.awarded_at)
                      else r.awarded_at end,r.points,case when r.kind='duel_week' then 0 else 1 end
 from public.social_rewards r left join public.duel_days d on r.kind='duel_day' and d.id=r.source_id
 left join public.duel_weeks w on r.kind='duel_week' and w.id=r.source_id where r.kind<>'leaderboard_week'
 union all select c.user_id,c.created_at,h.points,1 from public.completed_challenges c join public.challenges h on h.id=c.challenge_id;
$$;
revoke all on function public.weekly_xp_events() from public,anon,authenticated;

create or replace function public.admin_erase_account(subject uuid,confirmation text)
returns void language plpgsql security definer set search_path=public as $$
declare team record; successor uuid;
begin
 if subject is null or confirmation is distinct from 'ERASE '||subject::text then
  raise exception 'Explicit account confirmation required';
 end if;
 -- Same lock order as reward settlement. No client may call this function.
 perform 1 from public.profiles order by id for update;
 if not exists(select 1 from auth.users where id=subject) then raise exception 'Account not found'; end if;
 for team in select id from public.squads where created_by=subject order by id for update loop
  select user_id into successor from public.squad_members where squad_id=team.id and user_id<>subject order by joined_at,user_id limit 1;
  if successor is null then delete from public.squads where id=team.id;
  else update public.squads set created_by=successor where id=team.id; end if;
 end loop;
 -- Preserve the original effective dates of other participants' earned rewards.
 update public.social_rewards r set awarded_at=(d.day::timestamp+interval '23 hours 59 minutes') at time zone 'UTC'
 from public.duel_days d join public.friend_duels f on f.id=d.duel_id
 where r.kind='duel_day' and r.source_id=d.id and r.user_id<>subject and subject in(f.creator,f.opponent);
 update public.social_rewards r set awarded_at=((w.week_start+6)::timestamp+interval '23 hours 59 minutes') at time zone 'UTC'
 from public.duel_weeks w join public.friend_duels f on f.id=w.duel_id
 where r.kind='duel_week' and r.source_id=w.id and r.user_id<>subject and subject in(f.creator,f.opponent);
 delete from public.friend_duels where subject in(creator,opponent);
 -- Defensive cleanup for legacy data whose participant references were inconsistent.
 delete from public.duel_scores where user_id=subject;
 update public.duel_days set winner=null where winner=subject;
 update public.duel_weeks set winner=null where winner=subject;
 delete from public.social_rewards where user_id=subject;
 delete from public.leaderboard_prizes where user_id=subject;
 update public.ai_quests set parent_id=null where user_id<>subject and parent_id in(select id from public.ai_quests where user_id=subject);
 delete from public.profiles where id=subject;
 delete from auth.users where id=subject;
end;
$$;
revoke all on function public.admin_erase_account(uuid,text) from public,anon,authenticated,service_role;
commit;

-- Run once in the project's SQL editor. Existing quests and data are preserved.
begin;
create table if not exists public.ai_quests (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references public.profiles(id) on delete cascade,
 category text not null check (category in ('Adventure','Finance','Fitness','Health','Languages','Personal Growth','Social')),
 title text not null check (char_length(title) between 1 and 100),
 description text not null check (char_length(description) between 1 and 1200),
 minutes integer not null check (minutes between 5 and 45),
 difficulty integer not null check (difficulty between 1 and 5),
 status text not null default 'active' check (status in ('active','completed','skipped')),
 feedback text check (feedback in ('too_easy','just_right','too_hard','not_for_me')),
 created_at timestamptz not null default now(),
 completed_at timestamptz,
 unique(user_id,category,title)
);
create unique index if not exists ai_one_active_per_pillar on public.ai_quests(user_id,category) where status='active';
alter table public.ai_quests enable row level security;
drop policy if exists "Read own AI quests" on public.ai_quests;
create policy "Read own AI quests" on public.ai_quests for select to authenticated using (user_id=auth.uid());
drop policy if exists "Create own AI quests" on public.ai_quests;
create policy "Create own AI quests" on public.ai_quests for insert to authenticated with check (
 user_id=auth.uid() and status='active' and completed_at is null and feedback is null
 and exists (select 1 from public.profiles p where p.id=auth.uid() and category=any(p.selected_categories))
);
grant select,insert on public.ai_quests to authenticated;
revoke update,delete on public.ai_quests from authenticated,anon;

create or replace function public.finish_ai_quest(quest_id uuid, rating text, skip boolean default false)
returns integer language plpgsql security definer set search_path=public as $$
declare q public.ai_quests; total integer;
begin
 if auth.uid() is null then raise exception 'Authentication required'; end if;
 if rating is null or rating not in ('too_easy','just_right','too_hard','not_for_me') then raise exception 'Invalid rating'; end if;
 -- Serialize awards and make repeated submissions idempotent.
 perform 1 from public.profiles where id=auth.uid() for update;
 select * into q from public.ai_quests where id=quest_id and user_id=auth.uid() for update;
 if not found then raise exception 'Quest not found'; end if;
 if q.status='active' then
  update public.ai_quests set status=case when skip then 'skipped' else 'completed' end,
    feedback=rating,completed_at=now() where id=q.id;
  if not skip then
   update public.profiles set points=points+10+5*q.difficulty where id=auth.uid();
  end if;
 end if;
 select points into total from public.profiles where id=auth.uid();
 return total;
end;
$$;
revoke all on function public.finish_ai_quest(uuid,text,boolean) from public,anon;
grant execute on function public.finish_ai_quest(uuid,text,boolean) to authenticated;
-- Include private AI quest awards in the existing public aggregate leaderboard.
create or replace function public.get_weekly_leaderboard()
returns table(display_name text, weekly_points bigint, quests_completed bigint)
language sql stable security definer set search_path=public as $$
 with awards as (
  select cc.user_id, c.points as points
  from public.completed_challenges cc join public.challenges c on c.id=cc.challenge_id
  where cc.completed_on >= date_trunc('week',current_date)::date
  union all
  select q.user_id, 10+5*q.difficulty from public.ai_quests q
  where q.status='completed' and q.completed_at >= date_trunc('week',now())
 )
 select p.display_name, sum(a.points)::bigint, count(*)::bigint
 from awards a join public.profiles p on p.id=a.user_id
 group by p.id,p.display_name order by 2 desc,3 desc,1 asc limit 50;
$$;
revoke all on function public.get_weekly_leaderboard() from public,anon;
grant execute on function public.get_weekly_leaderboard() to authenticated;
commit;

-- Security hardening (findings from docs/security-audit.md).
-- Run once in the Supabase SQL Editor, AFTER protect-profile-points.sql.
-- Safe to run more than once. Everything runs in one transaction: all or nothing.

begin;

-- H1. Squads can only be created / joined through create_squad and join_squad
--     (which check the invite code). Before this, anyone could insert themselves
--     into any squad's member list through the REST API.
drop policy if exists "Authenticated users can create squads" on public.squads;
drop policy if exists "Users can join squads as themselves" on public.squad_members;
revoke insert, update, delete on public.squads, public.squad_members from authenticated, anon;

-- M1. At most 5 squads per creator, so squad XP cannot be farmed with many squads.
create or replace function public.limit_squads_per_creator()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if (select count(*) from public.squads where created_by = new.created_by) >= 5 then
    raise exception 'You can create at most 5 squads.';
  end if;
  return new;
end $$;
revoke all on function public.limit_squads_per_creator() from public, anon, authenticated;
drop trigger if exists limit_squads_per_creator on public.squads;
create trigger limit_squads_per_creator before insert on public.squads
  for each row execute function public.limit_squads_per_creator();

-- H2. Quest XP: at most 20 XP-earning completions per user per UTC day, so a script
--     cannot loop complete + replace for unlimited XP. Identical to the version in
--     five-quest-slots.sql except for the marked lines.
create or replace function public.save_quest_slots(quest_rows jsonb, finished_id uuid default null, rating text default 'just_right', skip boolean default false)
returns integer language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid(); old public.ai_quests; item jsonb; total integer; done_today integer;  -- changed: done_today
begin
 if uid is null then raise exception 'Authentication required'; end if;
 perform 1 from public.profiles where id=uid for update;
 if not found then raise exception 'Profile required'; end if;
 if quest_rows is null or jsonb_typeof(quest_rows)<>'array' or jsonb_array_length(quest_rows) not between 1 and 5 then raise exception 'Invalid quest batch'; end if;
 if rating is null or rating not in ('just_right','too_easy','too_hard','not_for_me') then raise exception 'Invalid rating'; end if;
 if finished_id is not null then
  select * into old from public.ai_quests where id=finished_id and user_id=uid for update;
  if not found then raise exception 'Quest not found'; end if;
  if old.status<>'active' then
   select points into total from public.profiles where id=uid;
   return total;
  end if;
  if jsonb_array_length(quest_rows)<>1 or (quest_rows->0->>'category')<>old.category or (quest_rows->0->>'slot')::integer<>old.slot then raise exception 'Replacement must keep the same slot'; end if;
  update public.ai_quests set status=case when skip then 'skipped' else 'completed' end,feedback=rating,completed_at=now() where id=old.id;
  if not skip then
   -- changed: daily cap on XP-earning completions
   select count(*) into done_today from public.ai_quests
    where user_id=uid and status='completed' and id<>old.id and completed_at>=date_trunc('day', now());
   if done_today<20 then update public.profiles set points=points+10+5*old.difficulty where id=uid; end if;
  end if;
 end if;
 for item in select value from jsonb_array_elements(quest_rows) loop
  if not exists(select 1 from public.profiles where id=uid and (item->>'category')=any(selected_categories)) then raise exception 'Pillar not selected'; end if;
  if not (item ?& array['slot','focus','target','category','title','description','minutes','difficulty','source'])
    or (item->>'slot') is null or (item->>'slot')::integer not between 1 and 5
    or (item->>'target') is null or (item->>'target')::integer not between 1 and 20000   -- changed: upper bound
    or (item->>'source') is null or (item->>'source') not in ('ai','curated') then raise exception 'Invalid quest'; end if;
  insert into public.ai_quests(user_id,category,slot,focus,target,title,description,minutes,difficulty,source,parent_id)
  values(uid,item->>'category',(item->>'slot')::integer,left(item->>'focus',40),(item->>'target')::integer,item->>'title',item->>'description',(item->>'minutes')::integer,(item->>'difficulty')::integer,item->>'source',finished_id)
  on conflict(user_id,category,slot) where status='active' do nothing;
 end loop;
 select points into total from public.profiles where id=uid;
 return total;
end;
$$;
revoke all on function public.save_quest_slots(jsonb,uuid,text,boolean) from public,anon;
grant execute on function public.save_quest_slots(jsonb,uuid,text,boolean) to authenticated;

-- H2 (cont.). The older completion function is no longer used by the app.
revoke all on function public.finish_ai_quest(uuid,text,boolean) from public, anon, authenticated;

-- L1. Completed challenges are only written by complete_challenge (security definer),
--     so users cannot insert back- or future-dated rows to inflate the leaderboard.
drop policy if exists "Users can complete challenges for themselves" on public.completed_challenges;
revoke insert, update, delete on public.completed_challenges from authenticated, anon;

-- L2. Database-side limits (NOT VALID: existing rows are kept, new writes are checked).
alter table public.profiles drop constraint if exists profiles_display_name_length;
alter table public.profiles add constraint profiles_display_name_length
  check (char_length(btrim(display_name)) between 1 and 30) not valid;
alter table public.profiles drop constraint if exists profiles_location_length;
alter table public.profiles add constraint profiles_location_length
  check (location is null or char_length(location) <= 120) not valid;
alter table public.profiles drop constraint if exists profiles_known_pillars;
alter table public.profiles add constraint profiles_known_pillars
  check (selected_categories <@ array['Adventure','Finance','Fitness','Health','Languages','Personal Growth','Social']::text[]
         and cardinality(selected_categories) <= 7) not valid;

-- L4. Functions from schema.sql: signed-in users only.
revoke all on function public.complete_challenge(bigint) from public, anon;
revoke all on function public.create_squad(text) from public, anon;
revoke all on function public.join_squad(text) from public, anon;
revoke all on function public.get_my_squad() from public, anon;
revoke all on function public.get_weekly_leaderboard() from public, anon;
grant execute on function public.complete_challenge(bigint), public.create_squad(text), public.join_squad(text),
  public.get_my_squad(), public.get_weekly_leaderboard() to authenticated;

commit;

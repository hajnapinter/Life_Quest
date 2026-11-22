-- Upgrade existing AI quests to five independent renewable slots per pillar.
begin;
alter table public.profiles add column if not exists email_reminders boolean not null default false;
alter table public.ai_quests add column if not exists slot integer;
alter table public.ai_quests add column if not exists focus text;
alter table public.ai_quests add column if not exists target integer;
alter table public.ai_quests add column if not exists source text not null default 'ai';
alter table public.ai_quests add column if not exists parent_id uuid references public.ai_quests(id);
-- Preserve history, but retire old unstructured active tasks without awarding XP.
with numbered as (
 select id,row_number() over(partition by user_id,category order by created_at,id) as n
 from public.ai_quests where status='active' and slot is null
) update public.ai_quests q set slot=numbered.n from numbered where q.id=numbered.id;
update public.ai_quests set status='skipped',feedback='not_for_me',completed_at=coalesce(completed_at,now())
where status='active' and focus is null;
alter table public.ai_quests drop constraint if exists ai_quests_user_id_category_title_key;
alter table public.ai_quests drop constraint if exists ai_quests_minutes_check;
alter table public.ai_quests add constraint ai_quests_minutes_check check(minutes between 1 and 120);
alter table public.ai_quests drop constraint if exists ai_quests_slot_check;
alter table public.ai_quests add constraint ai_quests_slot_check check(slot between 1 and 5);
drop index if exists public.ai_one_active_per_pillar;
create unique index if not exists ai_active_slot on public.ai_quests(user_id,category,slot) where status='active';
-- All slot writes go through a transaction that serialises on the user's profile.
drop policy if exists "Create own AI quests" on public.ai_quests;
revoke insert on public.ai_quests from authenticated;
create or replace function public.save_quest_slots(quest_rows jsonb, finished_id uuid default null, rating text default 'just_right', skip boolean default false)
returns integer language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid(); old public.ai_quests; item jsonb; total integer;
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
  if not skip then update public.profiles set points=points+10+5*old.difficulty where id=uid; end if;
 end if;
 for item in select value from jsonb_array_elements(quest_rows) loop
  if not exists(select 1 from public.profiles where id=uid and (item->>'category')=any(selected_categories)) then raise exception 'Pillar not selected'; end if;
  if not (item ?& array['slot','focus','target','category','title','description','minutes','difficulty','source'])
    or (item->>'slot') is null or (item->>'slot')::integer not between 1 and 5
    or (item->>'target') is null or (item->>'target')::integer<1
    or (item->>'source') is null or (item->>'source') not in ('ai','curated') then raise exception 'Invalid quest'; end if;
  insert into public.ai_quests(user_id,category,slot,focus,target,title,description,minutes,difficulty,source,parent_id)
  values(uid,item->>'category',(item->>'slot')::integer,item->>'focus',(item->>'target')::integer,item->>'title',item->>'description',(item->>'minutes')::integer,(item->>'difficulty')::integer,item->>'source',finished_id)
  on conflict(user_id,category,slot) where status='active' do nothing;
 end loop;
 select points into total from public.profiles where id=uid;
 return total;
end;
$$;
revoke all on function public.save_quest_slots(jsonb,uuid,text,boolean) from public,anon;
grant execute on function public.save_quest_slots(jsonb,uuid,text,boolean) to authenticated;
commit;

-- Apply last, after privacy.sql and weekly-leaderboard.sql. Existing scores are preserved.
begin;
alter table public.duel_scores alter column value type numeric using value::numeric;
alter table public.duel_scores drop constraint if exists duel_scores_whole_result;
alter table public.duel_scores add constraint duel_scores_whole_result
 check (value::text not in('NaN','Infinity','-Infinity') and value>=0 and value=trunc(value));

-- One signature avoids ambiguous PostgREST overloads; old JSON integer clients still work.
drop function if exists public.record_duel_score(uuid,integer);
create or replace function public.record_duel_score(quest_id uuid, result_value numeric)
returns void language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid();d public.duel_days;pair public.friend_duels;
begin
 if uid is null then raise exception 'Authentication required'; end if;
 select * into d from public.duel_days where id=quest_id for update;
 if not found then raise exception 'Daily quest not found'; end if;
 select * into pair from public.friend_duels where id=d.duel_id;
 if (uid is distinct from pair.creator and uid is distinct from pair.opponent) or pair.status<>'active' then raise exception 'Not your competition'; end if;
 if d.day<>(now() at time zone 'UTC')::date or d.settled
    or (pair.closed_at is not null and d.day>(pair.closed_at at time zone 'UTC')::date) then
  raise exception 'This day is closed';
 end if;
 if result_value is null or result_value::text in('NaN','Infinity','-Infinity')
    or result_value<0 or result_value<>trunc(result_value) then
  raise exception 'A non-negative whole number is required';
 end if;
 insert into public.duel_scores(day_id,user_id,value) values(d.id,uid,trunc(result_value))
 on conflict(day_id,user_id) do update set value=excluded.value,updated_at=now();
end $$;
revoke all on function public.record_duel_score(uuid,numeric) from public,anon;
grant execute on function public.record_duel_score(uuid,numeric) to authenticated;

-- Large totals must also compare correctly when days/weeks are settled. XP rules stay unchanged.
create or replace function public.settle_friend_duel(pair_id uuid)
returns void language plpgsql security definer set search_path=public as $$
declare pair public.friend_duels; d public.duel_days; a public.duel_scores.value%type;b public.duel_scores.value%type;person uuid;w date;wa integer;wb integer;event_id uuid;
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


notify pgrst, 'reload schema';
commit;

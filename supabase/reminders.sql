-- Scheduled reminders: a narrowly scoped worker credential, no service-role key.
begin;
alter table public.profiles add column if not exists reminder_hour integer not null default 9 check(reminder_hour between 0 and 23);
alter table public.profiles add column if not exists reminder_timezone text not null default 'UTC';
grant update(reminder_hour,reminder_timezone) on public.profiles to authenticated;
create or replace function public.validate_reminder_timezone()
returns trigger language plpgsql set search_path=public as $$
begin
 if not exists(select 1 from pg_timezone_names where name=new.reminder_timezone) then raise exception 'Unknown time zone'; end if;
 return new;
end $$;
drop trigger if exists validate_reminder_timezone on public.profiles;
create trigger validate_reminder_timezone before insert or update of reminder_timezone on public.profiles
 for each row execute function public.validate_reminder_timezone();

create table if not exists public.reminder_worker_keys (
 key_hash text primary key,enabled boolean not null default true,last_seen timestamptz
);
create table if not exists public.reminder_outbox (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references public.profiles(id) on delete cascade,
 local_day date not null,status text not null check(status in('sending','sent','failed','uncertain')),
 attempts integer not null default 1,last_attempt timestamptz not null default now(),sent_at timestamptz,
 unique(user_id,local_day)
);
alter table public.reminder_worker_keys enable row level security;
alter table public.reminder_outbox enable row level security;
revoke all on public.reminder_worker_keys,public.reminder_outbox from anon,authenticated;

create or replace function public.check_reminder_worker(worker_key text)
returns boolean language plpgsql security definer set search_path=public as $$
begin
 if worker_key is null or length(worker_key)<32 then raise exception 'Invalid worker credential'; end if;
 update public.reminder_worker_keys set last_seen=now()
 where enabled and key_hash=encode(sha256(convert_to(worker_key,'UTF8')),'hex');
 if not found then raise exception 'Invalid worker credential'; end if;
 return true;
end $$;

create or replace function public.claim_reminders(worker_key text)
returns jsonb language plpgsql security definer set search_path=public as $$
declare p record; event_id uuid; result jsonb:='[]'; daily_total integer;
begin
 perform public.check_reminder_worker(worker_key);
 -- Serialize workers. Keep room within Brevo's free 300/day allowance for auth mail.
 perform pg_advisory_xact_lock(hashtext('lifequest-reminders'));
 select count(*) into daily_total from public.reminder_outbox
 where last_attempt>=date_trunc('day',now() at time zone 'UTC') at time zone 'UTC' and status in('sent','sending','uncertain');
 for p in select u.id,u.email,pf.display_name,pf.reminder_timezone,
       coalesce(u.raw_user_meta_data->>'lifequest_language','en') language,
       (now() at time zone pf.reminder_timezone)::date local_day
   from public.profiles pf join auth.users u on u.id=pf.id
   where pf.email_reminders and u.email is not null and u.email_confirmed_at is not null
   and extract(hour from now() at time zone pf.reminder_timezone)>=pf.reminder_hour
   and not exists(select 1 from public.reminder_outbox r where r.user_id=pf.id and r.sent_at>now()-interval '20 hours')
   and not exists(select 1 from public.reminder_outbox r where r.user_id=pf.id
     and r.local_day=(now() at time zone pf.reminder_timezone)::date
     and not (r.status='failed' and r.attempts<3 and r.last_attempt<now()-interval '30 minutes'))
   order by pf.id limit 50 loop
  exit when daily_total>=250;
  event_id:=null;
  insert into public.reminder_outbox(user_id,local_day,status) values(p.id,p.local_day,'sending')
  on conflict(user_id,local_day) do update set status='sending',attempts=reminder_outbox.attempts+1,last_attempt=now()
   where reminder_outbox.status='failed' and reminder_outbox.attempts<3 and reminder_outbox.last_attempt<now()-interval '30 minutes'
  returning id into event_id;
  if event_id is not null then
   result:=result||jsonb_build_array(jsonb_build_object('id',event_id,'email',p.email,'name',p.display_name,'language',p.language));
   daily_total:=daily_total+1;
  end if;
 end loop;
 return result;
end $$;

create or replace function public.finish_reminder(worker_key text,event_id uuid,outcome text)
returns void language plpgsql security definer set search_path=public as $$
begin
 perform public.check_reminder_worker(worker_key);
 if outcome not in('sent','failed','uncertain') then raise exception 'Invalid reminder outcome'; end if;
 update public.reminder_outbox set status=outcome,sent_at=case when outcome='sent' then now() else null end
 where id=event_id and status='sending';
end $$;

create or replace function public.settle_due_competitions(worker_key text)
returns void language plpgsql security definer set search_path=public as $$
declare pair record; today date:=(now() at time zone 'UTC')::date;
begin
 perform public.check_reminder_worker(worker_key);
 perform pg_advisory_xact_lock(hashtext('lifequest-competition-settlement'));
 perform 1 from public.profiles where id in(
   select creator from public.friend_duels where status in('active','cancelled')
   union select opponent from public.friend_duels where status in('active','cancelled')) order by id for update;
 for pair in select * from public.friend_duels where status in('active','cancelled') order by id loop
  perform public.settle_friend_duel(pair.id);
  if pair.closed_at is not null and (pair.closed_at at time zone 'UTC')::date<today then
   update public.friend_duels set status='cancelled' where id=pair.id;
  end if;
 end loop;
end $$;

create or replace function public.get_reminder_status()
returns jsonb language plpgsql security definer set search_path=public as $$
begin
 if auth.uid() is null then raise exception 'Authentication required'; end if;
 return (select jsonb_build_object('configured',count(*)>0,'last_check',max(last_seen),
           'healthy',coalesce(max(last_seen)>now()-interval '3 hours',false)) from public.reminder_worker_keys where enabled);
end $$;
revoke all on function public.check_reminder_worker(text),public.claim_reminders(text),public.finish_reminder(text,uuid,text),public.settle_due_competitions(text) from public;
grant execute on function public.check_reminder_worker(text),public.claim_reminders(text),public.finish_reminder(text,uuid,text),public.settle_due_competitions(text) to anon;
revoke all on function public.get_reminder_status() from public,anon;
grant execute on function public.get_reminder_status() to authenticated;
commit;

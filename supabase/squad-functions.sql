create or replace function public.create_squad(squad_name_input text)
returns table (squad_id bigint, invite_code text)
language plpgsql
security definer
set search_path = public
as $$
declare
    current_user_id uuid := auth.uid();
    new_squad_id bigint;
    new_invite_code text;
begin
    if current_user_id is null then
        raise exception 'Authentication required';
    end if;
    if char_length(trim(squad_name_input)) < 2 then
        raise exception 'Squad name is too short';
    end if;

    new_invite_code := upper(substr(md5(random()::text || clock_timestamp()::text), 1, 8));
    insert into public.squads (name, invite_code, created_by)
    values (trim(squad_name_input), new_invite_code, current_user_id)
    returning id, squads.invite_code into new_squad_id, new_invite_code;

    insert into public.squad_members (squad_id, user_id)
    values (new_squad_id, current_user_id);

    return query select new_squad_id, new_invite_code;
end;
$$;

create or replace function public.join_squad(invite_code_input text)
returns table (squad_id bigint, squad_name text)
language plpgsql
security definer
set search_path = public
as $$
declare
    current_user_id uuid := auth.uid();
    selected_squad_id bigint;
    selected_squad_name text;
begin
    if current_user_id is null then
        raise exception 'Authentication required';
    end if;

    select id, name into selected_squad_id, selected_squad_name
    from public.squads
    where invite_code = upper(trim(invite_code_input));

    if selected_squad_id is null then
        raise exception 'Squad not found';
    end if;

    insert into public.squad_members (squad_id, user_id)
    values (selected_squad_id, current_user_id)
    on conflict do nothing;

    return query select selected_squad_id, selected_squad_name;
end;
$$;

create or replace function public.get_my_squad()
returns table (
    squad_id bigint,
    squad_name text,
    invite_code text,
    display_name text,
    member_points integer
)
language sql
stable
security definer
set search_path = public
as $$
    select
        s.id,
        s.name,
        s.invite_code,
        p.display_name,
        p.points
    from public.squads s
    join public.squad_members own_members on own_members.squad_id = s.id
    join public.squad_members members on members.squad_id = s.id
    join public.profiles p on p.id = members.user_id
    where own_members.user_id = auth.uid()
    order by p.points desc, p.display_name asc;
$$;

grant execute on function public.create_squad(text) to authenticated;
grant execute on function public.join_squad(text) to authenticated;
grant execute on function public.get_my_squad() to authenticated;

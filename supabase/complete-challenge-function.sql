create or replace function public.complete_challenge(challenge_id_input bigint)
returns table (new_points integer)
language plpgsql
security definer
set search_path = public
as $$
declare
    current_user_id uuid := auth.uid();
    challenge_points integer;
    updated_points integer;
begin
    if current_user_id is null then
        raise exception 'Authentication required';
    end if;

    select points into challenge_points
    from public.challenges
    where id = challenge_id_input and is_active = true;

    if challenge_points is null then
        raise exception 'Challenge not found';
    end if;

    if exists (
        select 1 from public.completed_challenges
        where user_id = current_user_id and challenge_id = challenge_id_input
    ) then
        raise exception 'Challenge already completed';
    end if;

    insert into public.completed_challenges (user_id, challenge_id)
    values (current_user_id, challenge_id_input);

    update public.profiles
    set points = points + challenge_points
    where id = current_user_id
    returning points into updated_points;

    return query select updated_points;
end;
$$;

grant execute on function public.complete_challenge(bigint) to authenticated;

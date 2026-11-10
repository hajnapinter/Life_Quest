create or replace function public.get_weekly_leaderboard()
returns table (
    display_name text,
    weekly_points bigint,
    quests_completed bigint
)
language sql
stable
security definer
set search_path = public
as $$
    select
        p.display_name,
        sum(c.points)::bigint as weekly_points,
        count(cc.id)::bigint as quests_completed
    from public.completed_challenges cc
    join public.profiles p on p.id = cc.user_id
    join public.challenges c on c.id = cc.challenge_id
    where cc.completed_on >= date_trunc('week', current_date)::date
    group by p.id, p.display_name
    order by weekly_points desc, quests_completed desc, p.display_name asc
    limit 50;
$$;

grant execute on function public.get_weekly_leaderboard() to authenticated;

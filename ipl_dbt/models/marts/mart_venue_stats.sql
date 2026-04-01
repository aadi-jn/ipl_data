-- Toss and match outcome stats per venue.
-- Grain: one row per (city, venue).
select
    city,
    venue,
    count(*)                                                            as total_matches,
    sum(case when toss_decision = 'field' then 1 else 0 end)           as chose_field,
    sum(case when toss_decision = 'bat'   then 1 else 0 end)           as chose_bat,
    round(
        sum(case when toss_decision = 'field' then 1 else 0 end) * 100.0
        / nullif(count(*), 0), 1
    )                                                                   as chose_field_pct,
    sum(case when winner = toss_winner then 1 else 0 end)              as toss_winner_won,
    round(
        sum(case when winner = toss_winner then 1 else 0 end) * 100.0
        / nullif(count(*), 0), 1
    )                                                                   as toss_win_pct,
    -- batting first vs fielding first wins (of completed matches)
    sum(case
        when winner is not null and toss_decision = 'bat'  and winner = toss_winner then 1
        when winner is not null and toss_decision = 'field' and winner != toss_winner then 1
        else 0
    end)                                                                as bat_first_wins,
    sum(case
        when winner is not null and toss_decision = 'field' and winner = toss_winner then 1
        when winner is not null and toss_decision = 'bat'  and winner != toss_winner then 1
        else 0
    end)                                                                as field_first_wins
from {{ ref('fct_matches') }}
where city is not null
group by city, venue

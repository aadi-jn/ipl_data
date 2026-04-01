-- Thin select over raw matches: rename nothing, cast types, filter nulls.
-- Materialized as view — no storage cost, always fresh.
select
    filename,
    cast(season as varchar)                              as season,
    cast(match_number as integer)                        as match_number,
    try(date_parse(date, '%Y-%m-%d'))                    as match_date,
    date                                                 as match_date_str,
    team1,
    team2,
    city,
    venue,
    cast(neutral_venue as boolean)                       as neutral_venue,
    toss_winner,
    toss_decision,
    winner,
    win_type,
    cast(win_margin as integer)                          as win_margin,
    result,
    method,
    eliminator,
    player_of_match,
    umpire1,
    umpire2
from {{ source('ipl_cricket', 'matches') }}
where filename is not null

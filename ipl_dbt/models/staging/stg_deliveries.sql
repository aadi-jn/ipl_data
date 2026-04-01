-- Thin select over raw deliveries: cast types, derive phase.
select
    match_id,
    try(date_parse(date, '%Y-%m-%d'))   as match_date,
    date                                as match_date_str,
    venue,
    city,
    team1,
    team2,
    cast(season as varchar)             as season,
    cast(innings as integer)            as innings,
    batting_team,
    bowling_team,
    cast(over as integer)               as over,
    cast(ball as integer)               as ball,
    batter,
    bowler,
    non_striker,
    cast(batter_runs as integer)        as batter_runs,
    cast(extras_total as integer)       as extras_total,
    cast(total_runs as integer)         as total_runs,
    cast(wides as integer)              as wides,
    cast(noballs as integer)            as noballs,
    cast(byes as integer)               as byes,
    cast(legbyes as integer)            as legbyes,
    cast(penalty as integer)            as penalty,
    cast(is_wicket as boolean)          as is_wicket,
    player_out,
    dismissal_kind,
    fielder,
    case
        when cast(over as integer) between 1 and 6  then 'Powerplay'
        when cast(over as integer) between 7 and 15 then 'Middle'
        when cast(over as integer) between 16 and 20 then 'Death'
        else 'Unknown'
    end                                 as phase
from {{ source('ipl_cricket', 'deliveries') }}
where match_id is not null

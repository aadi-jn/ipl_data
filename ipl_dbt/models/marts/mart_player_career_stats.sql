-- Player batting stats aggregated by season.
-- Grain: one row per (batter, season).
with innings_stats as (
    select
        match_id,
        season,
        innings,
        batting_team,
        batter,
        sum(batter_runs)                                     as runs,
        count(case when wides = 0 then 1 end)                as balls_faced,
        sum(case when batter_runs = 4 then 1 else 0 end)     as fours,
        sum(case when batter_runs = 6 then 1 else 0 end)     as sixes,
        max(case when is_wicket and player_out = batter then 1 else 0 end) as dismissed
    from {{ ref('fct_deliveries') }}
    group by match_id, season, innings, batting_team, batter
)
select
    batter,
    season,
    count(*)                                                 as innings_played,
    count(distinct match_id)                                 as matches,
    sum(runs)                                                as total_runs,
    max(runs)                                                as highest_score,
    sum(balls_faced)                                         as total_balls,
    sum(fours)                                               as fours,
    sum(sixes)                                               as sixes,
    sum(dismissed)                                           as dismissals,
    round(sum(runs) * 100.0 / nullif(sum(balls_faced), 0), 2) as strike_rate,
    round(sum(runs) * 1.0  / nullif(sum(dismissed),  0), 2) as batting_average,
    count(case when runs >= 50  then 1 end)                  as fifties,
    count(case when runs >= 100 then 1 end)                  as hundreds
from innings_stats
group by batter, season

-- Batting stats by match phase (Powerplay / Middle / Death) per team per season.
-- Grain: one row per (season, phase, batting_team).
select
    season,
    phase,
    batting_team,
    count(distinct match_id)                                                        as matches,
    sum(total_runs)                                                                 as total_runs,
    sum(case
        when is_wicket
         and dismissal_kind not in ('run out', 'retired hurt', 'obstructing the field')
        then 1 else 0
    end)                                                                            as wickets,
    -- economy: runs per over from legal deliveries
    round(
        sum(total_runs) * 6.0
        / nullif(count(case when wides = 0 and noballs = 0 then 1 end), 0), 2
    )                                                                               as run_rate,
    sum(case when batter_runs = 4 then 1 else 0 end)                               as fours,
    sum(case when batter_runs = 6 then 1 else 0 end)                               as sixes,
    round(
        sum(case when batter_runs = 6 then 1 else 0 end) * 100.0
        / nullif(count(case when wides = 0 then 1 end), 0), 1
    )                                                                               as six_rate_pct
from {{ ref('fct_deliveries') }}
group by season, phase, batting_team

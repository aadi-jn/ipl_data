-- Team win/loss record per season.
-- Uses UNION to count both team1 and team2 appearances.
-- Grain: one row per (team, season).
with team1_records as (
    select
        season,
        team1                                                   as team,
        count(*)                                                as matches_played,
        sum(case when winner = team1 then 1 else 0 end)         as wins,
        sum(case when winner != team1 and winner is not null and result != 'no result' then 1 else 0 end) as losses,
        sum(case when result = 'no result' then 1 else 0 end)   as no_results
    from {{ ref('fct_matches') }}
    group by season, team1
),
team2_records as (
    select
        season,
        team2                                                   as team,
        count(*)                                                as matches_played,
        sum(case when winner = team2 then 1 else 0 end)         as wins,
        sum(case when winner != team2 and winner is not null and result != 'no result' then 1 else 0 end) as losses,
        sum(case when result = 'no result' then 1 else 0 end)   as no_results
    from {{ ref('fct_matches') }}
    group by season, team2
),
combined as (
    select * from team1_records
    union all
    select * from team2_records
)
select
    season,
    team,
    sum(matches_played)  as matches_played,
    sum(wins)            as wins,
    sum(losses)          as losses,
    sum(no_results)      as no_results,
    round(sum(wins) * 100.0 / nullif(sum(wins) + sum(losses), 0), 1) as win_pct
from combined
group by season, team

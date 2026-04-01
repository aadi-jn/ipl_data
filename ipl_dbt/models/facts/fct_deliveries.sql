-- One row per delivery, with team names and city normalised.
-- Full refresh — Athena rewrites Parquet quickly at this scale (~1M rows).
select
    d.match_id,
    d.match_date,
    d.match_date_str,
    d.venue,
    coalesce(vc.canonical_city, d.city)                  as city,
    d.season,
    d.innings,
    coalesce(bt.canonical_name, d.batting_team)          as batting_team,
    coalesce(bwt.canonical_name, d.bowling_team)         as bowling_team,
    d.over,
    d.ball,
    d.phase,
    d.batter,
    d.bowler,
    d.non_striker,
    d.batter_runs,
    d.extras_total,
    d.total_runs,
    d.wides,
    d.noballs,
    d.byes,
    d.legbyes,
    d.penalty,
    d.is_wicket,
    d.player_out,
    d.dismissal_kind,
    d.fielder
from {{ ref('stg_deliveries') }} d
left join {{ ref('dim_teams') }} bt  on d.batting_team = bt.raw_name
left join {{ ref('dim_teams') }} bwt on d.bowling_team = bwt.raw_name
left join {{ ref('dim_venues') }} vc
    on d.city = vc.raw_city and d.venue = vc.venue

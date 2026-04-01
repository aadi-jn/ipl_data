-- One row per match, with team names and city normalised to canonical values.
-- Full refresh — dataset is small (< 1,500 rows) so incremental adds no value.
select
    m.filename,
    m.season,
    m.match_number,
    m.match_date,
    m.match_date_str,
    coalesce(t1.canonical_name, m.team1)                 as team1,
    coalesce(t2.canonical_name, m.team2)                 as team2,
    coalesce(vc.canonical_city, m.city)                  as city,
    m.venue,
    m.neutral_venue,
    coalesce(tw.canonical_name, m.toss_winner)           as toss_winner,
    m.toss_decision,
    coalesce(w.canonical_name, m.winner)                 as winner,
    m.win_type,
    m.win_margin,
    m.result,
    m.method,
    m.eliminator,
    m.player_of_match,
    m.umpire1,
    m.umpire2
from {{ ref('stg_matches') }} m
left join {{ ref('dim_teams') }} t1 on m.team1 = t1.raw_name
left join {{ ref('dim_teams') }} t2 on m.team2 = t2.raw_name
left join {{ ref('dim_teams') }} tw on m.toss_winner = tw.raw_name
left join {{ ref('dim_teams') }} w  on m.winner = w.raw_name
left join {{ ref('dim_venues') }} vc
    on m.city = vc.raw_city and m.venue = vc.venue

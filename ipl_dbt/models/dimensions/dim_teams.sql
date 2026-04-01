-- All team names that appear in match history, with canonical name via aliases seed.
-- Used by fact models to normalise franchise renames (e.g. Delhi Daredevils → Delhi Capitals).
with teams_raw as (
    select distinct team1 as team_name from {{ ref('stg_matches') }}
    union
    select distinct team2 as team_name from {{ ref('stg_matches') }}
)
select
    t.team_name                                          as raw_name,
    coalesce(a.canonical_name, t.team_name)              as canonical_name
from teams_raw t
left join {{ ref('dim_team_aliases') }} a
    on t.team_name = a.alias_name

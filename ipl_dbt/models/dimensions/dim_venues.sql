-- All venue/city combinations, with canonical city via aliases seed.
-- Handles city renames like Mohali → Chandigarh, Bangalore → Bengaluru.
with venues_raw as (
    select distinct
        venue,
        city
    from {{ ref('stg_matches') }}
    where venue is not null
)
select
    v.venue,
    v.city                                               as raw_city,
    coalesce(a.canonical_city, v.city)                   as canonical_city
from venues_raw v
left join {{ ref('dim_venue_aliases') }} a
    on v.city = a.alias_city

# Cricsheet Data Format Reference

**Sources:**
- YAML spec: [cricsheet.org/format/yaml](https://cricsheet.org/format/yaml/) (v0.92)
- JSON spec: [cricsheet.org/format/json](https://cricsheet.org/format/json/) (v1.1.0)
- Actual IPL JSON file analysis (1,170 matches)

**Last verified:** 2026-03-30

---

# Section 1 — YAML-Documented Fields

**Source:** [cricsheet.org/format/yaml](https://cricsheet.org/format/yaml/) (v0.92)

These fields are documented in the YAML format specification.

## Top-Level Structure

```
{
  "meta": { ... },
  "info": { ... },
  "innings": [ ... ]
}
```

## 1. `meta` — File Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data_version` | string | Yes | Semantic version of the data format (e.g., `"0.92"`) |
| `created` | string | Yes | Date the file was created (YYYY-MM-DD) |
| `revision` | integer | Yes | Revision number; starts at 1, increments on updates |

## 2. `info` — Match Metadata

### 2.1 Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `balls_per_over` | integer | Yes | Balls per over (typically 6). Added in v0.91. |
| `city` | string | No | City where the match was played |
| `competition` | string | No | Competition name (e.g., IPL, T20 Blast, The Hundred) |
| `dates` | array of strings | Yes | Match date(s) in YYYY-MM-DD. Always an array even for single-day matches. |
| `gender` | string | Yes | `"male"` or `"female"` |
| `match_type` | string | Yes | `"Test"`, `"ODI"`, `"T20"`, `"IT20"`, `"ODM"`, or `"MDM"` |
| `match_type_number` | integer | No | Sequential match number for this match type |
| `neutral_venue` | integer | No | Value `1` if played at a neutral ground |
| `overs` | integer | No | Maximum overs per innings (e.g., 20 for T20, 50 for ODI). Absent for Tests. |
| `player_of_match` | array of strings | No | Player(s) of the match. Array even for a single player. |
| `teams` | array of strings | Yes | Two team names |
| `venue` | string | No | Full venue/ground name |

### 2.2 Players & Registry

**`info.players`** — Mapping of team name to array of player names (includes playing XI plus substitutes). Added in v0.91.

```json
"players": {
  "Team A": ["Player 1", "Player 2", ...],
  "Team B": ["Player 1", "Player 2", ...]
}
```

**`info.registry.people`** — Mapping of person name to 8-character lowercase hex ID. Same person has the same ID across all matches. Added in v0.91.

```json
"registry": {
  "people": {
    "Player Name": "abcd1234"
  }
}
```

### 2.3 Supersubs

**`info.supersubs`** — Mapping of team name to supersub player name. Added in v0.9.

### 2.4 Toss

**Path:** `info.toss`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `winner` | string | Yes | Team that won the toss |
| `decision` | string | Yes | `"bat"` or `"field"` |
| `uncontested` | string | No | `"yes"` if toss was uncontested. Added in v0.92. |

### 2.5 Umpires

**Path:** `info.umpires`

Array of umpire names (minimum 2 if present).

### 2.6 Outcome

**Path:** `info.outcome`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `winner` | string | Conditional | Winning team. Absent if draw, tie, or no result. |
| `by` | object | Conditional | Victory margin. Only present if a team won. |
| `by.runs` | integer | Conditional | Won by X runs |
| `by.wickets` | integer | Conditional | Won by X wickets |
| `by.innings` | integer | Conditional | Won by an innings (value `1`). Multi-innings formats only. |
| `result` | string | Conditional | `"tie"`, `"draw"`, or `"no result"` |
| `method` | string | No | `"D/L"`, `"VJD"`, `"Awarded"`, `"1st innings score"`, `"Lost fewer wickets"` |
| `eliminator` | string | No | Team that won a super over tiebreaker |
| `bowl_out` | string | No | Team that won a bowl-out tiebreaker |

### 2.7 Bowl-Out Data

**Path:** `info.bowl_out`

Array of objects, only present for matches decided by bowl-out.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bowler` | string | Yes | Bowler name |
| `outcome` | string | Yes | `"hit"` or `"miss"` |

## 3. `innings` — Ball-by-Ball Match Data

Array of innings in chronological order.

### 3.1 Innings Container

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `team` | string | Yes | Batting team name |
| `deliveries` | array | Conditional | Ball-by-ball data. Absent if innings forfeited. |
| `absent_hurt` | array of strings | No | Players unable to bat due to injury |
| `penalty_runs` | object | No | Penalty runs for the innings. Added in v0.8. |
| `penalty_runs.pre` | integer | No | Penalty runs awarded before innings start |
| `penalty_runs.post` | integer | No | Penalty runs awarded after innings end |
| `declared` | string | No | `"yes"` if innings declared |
| `forfeited` | string | No | `"yes"` if innings forfeited. Added in v0.92. |

### 3.2 Delivery Object

Each delivery is keyed by over.ball notation (e.g., `"0.1"`, `"23.5"`).

**Caution:** Overs with 10+ deliveries (due to extras) use notation like `"23.10"`. Some YAML parsers read this as `23.1`, overwriting the first ball.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `batsman` | string | Yes | Striker's name |
| `bowler` | string | Yes | Bowler's name |
| `non_striker` | string | Yes | Non-striker's name |
| `runs` | object | Yes | Run breakdown |
| `extras` | object | No | Extra runs breakdown. Absent if no extras. |
| `wicket` | object or array | No | Dismissal(s). Single object or array if multiple on one ball. |
| `replacements` | object | No | Player substitutions before this delivery. Added in v0.9. |

### 3.3 Runs

**Path:** `delivery.runs`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `batsman` | integer | Yes | Runs scored by batter |
| `extras` | integer | Yes | Extra runs on this delivery |
| `total` | integer | Yes | Total runs = `batsman` + `extras` |
| `non_boundary` | integer | No | Value `1` if batter scored 4 or 6 but NOT via hitting the boundary rope (all-run or overthrows) |

### 3.4 Extras

**Path:** `delivery.extras`

Only the extras that occurred on this delivery are included as keys.

| Field | Type | Description |
|-------|------|-------------|
| `byes` | integer | Bye runs |
| `legbyes` | integer | Leg-bye runs |
| `noballs` | integer | No-ball runs |
| `penalty` | integer | Penalty runs |
| `wides` | integer | Wide runs |

### 3.5 Wicket

**Path:** `delivery.wicket` (single object or array)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `player_out` | string | Yes | Name of dismissed player |
| `kind` | string | Yes | Dismissal type (see below) |
| `fielders` | array of strings | No | Fielder name(s) involved. Absent for bowled, LBW. |

**Dismissal types:** `bowled`, `caught`, `caught and bowled`, `lbw`, `stumped`, `run out`, `hit wicket`, `retired hurt`, `obstructing the field`, `hit the ball twice`, `handled the ball`, `timed out`

### 3.6 Replacements

**Path:** `delivery.replacements` (added in v0.9)

#### Match replacements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `in` | string | Yes | Player entering the match |
| `out` | string | Yes | Player leaving the match |
| `reason` | string | Yes | See below |
| `team` | string | Yes | Team making the substitution |

**Reasons:** `concussion_substitute`, `covid_replacement`, `injury_substitute`, `national_callup`, `national_release`, `supersub`, `tactical_substitute`, `unknown`

#### Role replacements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `in` | string | Yes | Player taking over the role |
| `out` | string | No | Player leaving the role |
| `reason` | string | Yes | `injury`, `too many overs`, `excluded - excessive short-pitched deliveries`, `excluded - high full pitched balls`, `excluded - running on the pitch`, `unknown` |
| `role` | string | Yes | `"bowler"` or `"batter"` |

---

# Section 2 — JSON-Only Fields

**Source:** [cricsheet.org/format/json](https://cricsheet.org/format/json/) (v1.1.0)

These fields are documented in the JSON format specification but NOT in the YAML specification. The JSON format also renames some YAML fields and restructures deliveries.

## Naming & Structural Changes from YAML

| YAML | JSON | Change |
|------|------|--------|
| `batsman` | `batter` | Renamed |
| `runs.batsman` | `runs.batter` | Renamed |
| `runs.non_boundary` (integer) | `runs.non_boundary` (boolean) | Type changed |
| `wicket` (object or array) | `wickets` (always array) | Renamed, always array |
| `fielders` (array of strings) | `fielders` (array of objects with `name` field) | Structural change |
| `info.umpires` (array) | `info.officials.umpires` (array) | Moved under `officials` |
| `toss.uncontested` (string `"yes"`) | `toss.uncontested` (boolean) | Type changed |
| `declared` (string `"yes"`) | `declared` (boolean) | Type changed |
| `forfeited` (string `"yes"`) | `forfeited` (boolean) | Type changed |
| Deliveries keyed by over.ball (`"0.1"`) | Deliveries nested under `overs[].deliveries[]` | Structural change |

## Additional `info` Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event` | object | No | Competition context |
| `event.name` | string | Yes (if event) | Competition name |
| `event.match_number` | integer | No | Match number within competition |
| `event.group` | string | No | Group identifier |
| `event.stage` | string | No | Stage name (e.g., `"Final"`, `"Super 10"`) |
| `missing` | array | No | Details on what data is missing (strings or objects) |
| `season` | string | Yes | Season identifier (e.g., `"2018"`, `"2011/12"`) |
| `team_type` | string | Yes | `"international"` or `"club"` |

### Officials

**Path:** `info.officials` (replaces YAML's `info.umpires`)

| Field | Type | Description |
|-------|------|-------------|
| `umpires` | array of strings | On-field umpires |
| `match_referees` | array of strings | Match referees |
| `reserve_umpires` | array of strings | Reserve/4th umpires |
| `tv_umpires` | array of strings | TV/third umpires |

## Additional `innings` Fields

### Overs Structure

In JSON, deliveries are grouped under overs instead of using flat over.ball keys.

```json
{
  "over": 0,
  "deliveries": [ ... ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `over` | integer | Yes | Over number (0-indexed) |
| `deliveries` | array | Yes | Array of delivery objects in this over |

### Other Innings Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `super_over` | boolean | No | `true` if this is a super over innings |
| `powerplays` | array | No | Powerplay phases |
| `target` | object | No | Chase target (chasing innings only) |
| `miscounted_overs` | object | No | Overs where wrong number of balls were bowled |

#### Powerplays

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from` | number | Yes | Start delivery (e.g., `0.1`) |
| `to` | number | Yes | End delivery (e.g., `5.6`) |
| `type` | string | Yes | `"mandatory"`, `"batting"`, or `"fielding"` |

#### Target

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `overs` | integer | Yes | Maximum overs available for chase |
| `runs` | integer | Yes | Runs required to win |

#### Miscounted Overs

Keyed by over number string. Each entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `balls` | number | Yes | Actual deliveries bowled |
| `umpire` | string | No | Umpire name |

## Additional Delivery Fields

### Review (DRS)

**Path:** `delivery.review`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `by` | string | Yes | Reviewing team name |
| `batter` | string | Yes | Batter under review |
| `decision` | string | Yes | `"struck down"` or `"upheld"` |
| `umpire` | string | No | Umpire whose decision was reviewed |
| `umpires_call` | boolean | No | `true` if struck down via umpire's call |

## Version History (JSON)

| Version | Key Additions |
|---------|---------------|
| 1.1.0 | `toss.uncontested` (boolean), `innings.forfeited` (boolean) |
| 1.0.0 | Initial JSON version |

---

# Section 3 — Undocumented (Found in Actual IPL Data)

These fields and behaviors were discovered by inspecting 1,170 actual IPL JSON files and are **not documented** in either the YAML or JSON format specifications.

## Fields

| Field | Path | Type | Notes |
|-------|------|------|-------|
| `fielders[].substitute` | `delivery.wickets[].fielders[]` | boolean | `true` when a substitute fielder (not in playing XI) takes a catch or effects a run out |
| `impact_player` | `replacements.match[].reason` | string | IPL's tactical substitute reason string (from 2023 season). The YAML spec documents `tactical_substitute`; actual IPL data uses `impact_player` instead. |
| `retired out` | `delivery.wickets[].kind` | string | Strategic voluntary retirement (counted as a dismissal, unlike `retired hurt`) |

## Season Type Inconsistency

The `season` field alternates between string and integer types across files:

| IPL Season | `season` value | Type |
|------------|---------------|------|
| 2008 | `"2007/08"` | string |
| 2009 | `"2009"` | string |
| 2010 | `"2009/10"` | string |
| 2020 | `"2020/21"` | string |
| 2012-2019 | e.g. `2017` | string or integer (varies per file) |
| 2021-2025 | e.g. `"2025"` | string |

**Recommendation:** Always cast `season` to string.

## Data Quality Notes

1. **Player name variations:** Same person may appear with slightly different names across seasons. Always use `registry.people` hex ID as the canonical identifier.

2. **Missing fields in older matches:** Some 2008-2010 matches lack `officials`, `registry`, `players`, or `powerplays`.

3. **Impact player timing:** The `replacements.match` entry for impact players appears on the delivery AFTER the substitution, not before.

4. **Retired hurt vs retired out:** `"retired hurt"` (injury) is not a true dismissal for batting average purposes. `"retired out"` (strategic) is counted as a dismissal. Both appear in the `wickets` array.

5. **Super over edge cases:**
   - When `result: "tie"` AND `eliminator` is present, the match was tied in regulation and decided by super over. The `winner` field is NOT set.
   - Double super overs are possible (6 innings total). Example: Match 1216517 (KXIP vs MI, 2020).

6. **Powerplay `to` field:** Can exceed `X.6` when extras extend an over (e.g., `5.7`).

7. **Wides edge case:** On a wide, `runs.batter` is always `0`. A wide + 1 bye = `extras.wides: 2`, `runs.extras: 2`, `runs.total: 2`.

8. **No-ball edge case:** Batter CAN score off a no-ball. `extras.noballs: 1` + `runs.batter: 4` = `runs.total: 5`.

9. **Boundary detection:** To count boundaries, check `runs.batter == 4 or 6` AND `runs.non_boundary` is absent. If `non_boundary` is present, runs were all-run or overthrows.

---

## External Data: Cricsheet People Register

**Download:** `people.csv` from [cricsheet.org/register/](https://cricsheet.org/register/)

17,834 unique people with 27,538 identifiers across 12 sources.

### people.csv fields

| Field | Description | Count |
|-------|-------------|-------|
| Cricsheet ID | 8-char hex (matches `registry.people`) | — |
| Name | Primary name used in match data | — |
| Unique name | Disambiguated version | — |
| `key_cricinfo` | ESPNcricinfo player ID | 17,965 |
| `key_cricketarchive` | CricketArchive ID | 4,509 |
| `key_bcci` | BCCI ID | 1,329 |
| `key_pulse` | ICC Pulse ID | 2,023 |
| `key_nvplay` | NV Play ID | 1,006 |
| `key_bigbash` | Big Bash League ID | 296 |
| `key_cricingif` | Cricingif ID | 130 |
| `key_cricketworld` | Cricketworld ID | 127 |
| `key_crichq` | CricHQ ID | 24 |
| `key_cricbuzz` | Cricbuzz ID | 22 |
| `key_opta` | Opta ID | 68 |

### names.csv

Lists alternate names for players across different sources and name changes.

**Use case:** Join Cricsheet IDs to ESPNcricinfo player IDs to fetch player profiles, photos, and career stats.

---

## IPL Download Links

| Format | URL | Matches |
|--------|-----|---------|
| JSON | `https://cricsheet.org/downloads/ipl_json.zip` | 1,170 |
| YAML | `https://cricsheet.org/downloads/ipl.zip` | 1,170 |
| People register | `https://cricsheet.org/register/` → `people.csv` | 17,834 people |

**Recommendation:** Use JSON format. It avoids the YAML ball-notation parsing bug, uses cleaner field names (`batter` not `batsman`), and has proper array structures.

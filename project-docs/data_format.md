# Cricsheet Data Format Reference

**Source:** [cricsheet.org/format/yaml](https://cricsheet.org/format/yaml/) + actual IPL JSON file analysis (1,170 matches)
**Current data version:** 1.0.0 (JSON files), 0.92 (YAML spec docs — docs lag behind actual data)
**Last verified:** 2026-03-29

> The YAML docs are incomplete. This document supplements them with fields discovered in actual IPL JSON files. Fields marked with `*` are **undocumented** — found only by inspecting real data.

---

## Top-Level Structure

```
{
  "meta": { ... },
  "info": { ... },
  "innings": [ ... ]
}
```

---

## 1. `meta` — File Metadata

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `data_version` | string | Yes | Semantic version of the data format | `"1.0.0"` |
| `created` | string | Yes | Date the file was created (YYYY-MM-DD) | `"2017-04-06"` |
| `revision` | integer | Yes | Revision number; starts at 1, increments on updates | `1` |

---

## 2. `info` — Match Metadata

### 2.1 Core Fields

| Field | Type | Required | Description | Edge Cases / Notes |
|-------|------|----------|-------------|--------------------|
| `balls_per_over` | integer | Yes | Balls per over | Always `6` in IPL. Added in v0.91. Exists for historical matches where overs were 8 balls. |
| `city` | string | No | City where the match was played | May be absent for neutral venues or incomplete data. Example: `"Hyderabad"` |
| `dates` | array of strings | Yes | Match date(s) in YYYY-MM-DD | Always an array even for single-day matches. IPL = always 1 date. Multi-day Tests can have 5 entries. |
| `gender` | string | Yes | Player gender | `"male"` for all IPL matches. Other values: `"female"`. |
| `match_type` | string | Yes | Match classification | `"T20"` for all IPL. Others: `"Test"`, `"ODI"`, `"IT20"` (International T20), `"ODM"`, `"MDM"`. |
| `overs` | integer | No | Maximum overs per innings | `20` for all IPL. `50` for ODIs. Absent for Tests. |
| `teams` | array of strings | Yes | Team names (2 entries) | Order matches batting order (first entry bats first). |
| `venue` | string | No | Full venue name | Can include sub-location: `"Rajiv Gandhi International Stadium, Uppal"`, `"MA Chidambaram Stadium, Chepauk"` |

### 2.2 Event & Season Fields *

| Field | Type | Required | Description | Edge Cases / Notes |
|-------|------|----------|-------------|--------------------|
| `event` * | object | No | Competition context | **Undocumented in YAML spec.** Present in all IPL JSON files. |
| `event.name` * | string | Yes (if event) | Competition name | `"Indian Premier League"` for all IPL files |
| `event.match_number` * | integer | Yes (if event) | Match number within competition | Sequential within a season. Example: `1`, `36`, `66` |
| `season` * | string or integer | No | Season identifier | **Format varies!** Can be: `"2007/08"`, `"2009"`, `"2020/21"`, `2017` (integer), `"2025"` (string). Split-year format used when IPL spans calendar years. Must handle both string and integer types. |
| `team_type` * | string | No | Type of teams | `"club"` for all IPL. Other leagues may have `"international"`. |
| `competition` | string | No | Competition name (YAML format) | Documented in YAML spec. May overlap with `event.name` in JSON format. |

### 2.3 Toss

**Path:** `info.toss`

| Field | Type | Required | Description | Edge Cases / Notes |
|-------|------|----------|-------------|--------------------|
| `winner` | string | Yes | Team that won the toss | Must match a team in `info.teams` |
| `decision` | string | Yes | Toss winner's choice | `"bat"` or `"field"` |
| `uncontested` | string | No | Whether toss was uncontested | Value `"yes"`. Added in v0.92. Mainly County Championship 2016-2019. Not seen in IPL data. |

### 2.4 Outcome

**Path:** `info.outcome`

| Field | Type | Required | Description | Edge Cases / Notes |
|-------|------|----------|-------------|--------------------|
| `winner` | string | Conditional | Winning team | Absent if draw, tie, or no result |
| `by` | object | Conditional | Victory margin | Only present if a team won |
| `by.runs` | integer | Conditional | Won by X runs | Used when batting-first team wins |
| `by.wickets` | integer | Conditional | Won by X wickets | Used when chasing team wins |
| `by.innings` | integer | Conditional | Won by an innings | Value `1`. Only in multi-innings formats (Tests). Not in IPL. |
| `result` | string | Conditional | Non-win result | `"tie"`, `"draw"`, `"no result"` |
| `method` | string | No | Special method used | `"D/L"` (Duckworth-Lewis-Stern), `"VJD"` (Jayadevan), `"Awarded"`, `"1st innings score"`, `"Lost fewer wickets"` |
| `eliminator` | string | No | Super over winner | Team name. Present when match was a tie decided by super over. |
| `bowl_out` | string | No | Bowl-out winner | Team name. Extremely rare — only early IPL (2008-2009 era). |

**Important edge case for super overs:** When `result: "tie"` AND `eliminator` is present, the match was tied in regulation and decided by super over. The `eliminator` is the team that won the super over. The `winner` field is NOT set — the match result is officially a "tie" with an eliminator.

### 2.5 Officials *

**Path:** `info.officials` (JSON) or `info.umpires` (YAML)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `umpires` | array of strings | No | On-field umpires (usually 2) |
| `tv_umpires` * | array of strings | No | Third umpire |
| `reserve_umpires` * | array of strings | No | Reserve/4th umpire |
| `match_referees` * | array of strings | No | Match referee |

> In YAML format, `umpires` is a direct child of `info`. In JSON format, all officials are nested under `info.officials`. The JSON structure is more comprehensive.

### 2.6 Players & Registry

**Path:** `info.players`

Mapping of team name → array of player names (strings). Includes the playing XI plus any substitutes (impact players, concussion subs, injury subs).

```json
"players": {
  "Sunrisers Hyderabad": ["DA Warner", "S Dhawan", ...],
  "Royal Challengers Bangalore": ["CH Gayle", "Mandeep Singh", ...]
}
```

**Edge cases:**
- Player names use initials + surname format: `"V Kohli"`, `"MS Dhoni"`
- Some players have single names: `"Rashid Khan"`, `"Yuvraj Singh"`, `"Sachin Baby"`
- Name consistency is NOT guaranteed across seasons — the registry ID is the stable identifier
- Impact player substitutes ARE included in the players list even before they enter the match

**Path:** `info.registry.people`

Mapping of player/official name → 8-character hex ID. Same person has the same ID across all matches.

```json
"registry": {
  "people": {
    "V Kohli": "abcd1234",
    "MS Dhoni": "ef567890"
  }
}
```

**Edge cases:**
- IDs are 8 chars, lowercase hex (0-9, a-f)
- Includes ALL people in the file: batters, bowlers, fielders, umpires, referees
- Can be joined with Cricsheet's `people.csv` register file for external IDs (ESPNcricinfo, CricketArchive, BCCI, etc.)

### 2.7 Other Info Fields

| Field | Type | Required | Description | Edge Cases / Notes |
|-------|------|----------|-------------|--------------------|
| `player_of_match` | array of strings | No | Player(s) of the match award | Array even for single player. Can have multiple winners (rare). Absent if no award given. |
| `match_type_number` | integer | No | Ordinal match number of this type | Example: the 2404th T20 match ever. Not always present in IPL data. |
| `neutral_venue` | integer | No | Whether venue is neutral | Value `1` if neutral. Absent if not neutral. Relevant for IPL matches played at neutral venues (e.g., during COVID). |
| `supersubs` | object | No | Supersub player mapping | Pre-impact-player era rule. Team name → player name. Very rare in IPL. |

### 2.8 Bowl-Out Data

**Path:** `info.bowl_out`

Array of objects, only present for matches decided by bowl-out (extremely rare — early IPL only).

```json
"bowl_out": [
  {"bowler": "JE Taylor", "outcome": "miss"},
  {"bowler": "SE Bond", "outcome": "hit"}
]
```

---

## 3. `innings` — Ball-by-Ball Match Data

Array of innings objects. Typical IPL match has 2. Super over matches have 4+ (2 regulation + 2 per super over).

### 3.1 Innings Container

| Field | Type | Required | Description | Edge Cases / Notes |
|-------|------|----------|-------------|--------------------|
| `team` | string | Yes | Batting team name | Matches a team in `info.teams` |
| `overs` | array | Conditional | Ball-by-ball data grouped by over | Absent if innings forfeited |
| `super_over` * | boolean | No | Whether this is a super over innings | `true` for super over innings. Absent (not `false`) for regulation innings. |
| `powerplays` * | array | No | Powerplay phases | See below. Not in YAML docs. Present in JSON. |
| `target` * | object | No | Chase target | Only on 2nd innings (and super over chase innings). See below. |
| `declared` | string | No | Innings declared | `"yes"`. Not applicable in T20/IPL. |
| `forfeited` | string | No | Innings forfeited | `"yes"`. Added v0.92. Extremely rare. |
| `absent_hurt` | array | No | Players unable to bat | Array of player names who were absent hurt. |
| `penalty_runs` | object | No | Penalty runs | `pre` and/or `post` integer fields. Very rare. |

### 3.2 Powerplays *

**Path:** `innings[].powerplays`

```json
"powerplays": [
  {"from": 0.1, "to": 5.6, "type": "mandatory"}
]
```

| Field | Type | Description | Edge Cases |
|-------|------|-------------|------------|
| `from` | float | Start ball (over.ball notation) | Usually `0.1` for mandatory powerplay |
| `to` | float | End ball | Usually `5.6` but can be `5.7` or more if extras extend the over |
| `type` | string | Powerplay type | `"mandatory"` is the only type seen in IPL. Other formats may have `"batting"`, `"bowling"`. |

**Edge case:** The `to` value can exceed `X.6` when wides/no-balls extend an over. For example, `5.7` means the powerplay ended after 7 deliveries in the 6th over (one was a wide/no-ball).

### 3.3 Target *

**Path:** `innings[].target`

Only present on chasing innings (2nd innings or super over chase).

```json
"target": {"overs": 20, "runs": 207}
```

| Field | Type | Description |
|-------|------|-------------|
| `overs` | integer | Maximum overs available for chase |
| `runs` | integer | Runs required to win |

**Edge case:** In DLS-affected matches, `overs` may be less than 20 and `runs` may be a revised target.

### 3.4 Overs Structure (JSON format)

**Path:** `innings[].overs`

Array of over objects. Each over contains:

```json
{
  "over": 0,
  "deliveries": [ ... ]
}
```

| Field | Type | Description | Edge Cases |
|-------|------|-------------|------------|
| `over` | integer | Over number (0-indexed) | Over 0 = first over, over 19 = last regulation over |
| `deliveries` | array | Array of delivery objects in this over | Can have >6 deliveries if wides/no-balls |

> **YAML vs JSON structure difference:** In YAML format, deliveries are flat with keys like `"0.1"`, `"0.2"`, `"23.10"`. In JSON format (v1.0.0), deliveries are nested under `overs[].deliveries` — each delivery is just an object in order (no ball-number key). The over number + array index gives you the ball number.

> **YAML gotcha:** In YAML, deliveries like `23.10` (10th ball of an over due to extras) may be parsed as `23.1` by some YAML parsers, overwriting the first ball. This is fixed in JSON format v1.0.0.

### 3.5 Delivery Object

**Path:** `innings[].overs[].deliveries[]`

| Field | Type | Required | Description | Edge Cases |
|-------|------|----------|-------------|------------|
| `batter` | string | Yes | Striker's name | JSON uses `batter`. YAML uses `batsman` (to be updated). |
| `bowler` | string | Yes | Bowler's name | |
| `non_striker` | string | Yes | Non-striker's name | |
| `runs` | object | Yes | Run breakdown | See below |
| `extras` | object | No | Extra runs breakdown | Absent if no extras on this delivery |
| `wickets` | array | No | Dismissal(s) on this delivery | **JSON uses `wickets` (array). YAML uses `wicket` (object or array).** Can have multiple dismissals on one ball (extremely rare — e.g., run out of non-striker while completing a catch). |
| `replacements` | object | No | Player substitutions before this delivery | Impact player subs, injury subs, concussion subs. See below. |

### 3.6 Runs

**Path:** `delivery.runs`

| Field | Type | Required | Description | Edge Cases |
|-------|------|----------|-------------|------------|
| `batter` | integer | Yes | Runs scored by batter | `0` if dot ball or extras-only. JSON uses `batter`. YAML uses `batsman`. |
| `extras` | integer | Yes | Extra runs on this delivery | `0` if no extras |
| `total` | integer | Yes | Total runs off this delivery | Always = `batter` + `extras` |
| `non_boundary` | integer | No | Indicates runs were NOT from a boundary | Value `1`. Present when batter scored 4 or 6 via running/overthrows, not hitting the boundary rope. Absence when `batter` = 4 or 6 means it WAS a boundary hit. |

**Key insight for analytics:** To count boundaries (4s and 6s), check `runs.batter == 4 or runs.batter == 6` AND `runs.non_boundary` is absent. If `non_boundary` = 1, the runs were all-run or overthrows.

### 3.7 Extras

**Path:** `delivery.extras`

Only the extras that occurred on this delivery are included as keys. If no extras, the entire `extras` object is absent.

| Field | Type | Description | Edge Cases |
|-------|------|-------------|------------|
| `wides` | integer | Wide ball runs | Usually `1`, but can be more if batter runs on a wide (e.g., `2` = wide + 1 run) |
| `noballs` | integer | No-ball runs | Usually `1`. Batter runs are counted separately in `runs.batter`. |
| `byes` | integer | Bye runs | Runs taken without bat contact, not off the bowler's delivery |
| `legbyes` | integer | Leg-bye runs | Off the batter's body, not the bat |
| `penalty` | integer | Penalty runs | 5-run penalties. Extremely rare. |

**Wides edge case:** On a wide, `runs.batter` is always `0` (batter can't score off a wide). All runs go to `extras`. A wide + 1 bye = `extras.wides: 2` (the wide run + the bye), `runs.extras: 2`, `runs.total: 2`.

**No-ball edge case:** On a no-ball, the batter CAN score runs. So `extras.noballs: 1` + `runs.batter: 4` (if they hit a four) = `runs.total: 5`. The no-ball run goes to extras, the four goes to the batter.

### 3.8 Wickets

**Path:** `delivery.wickets` (JSON) / `delivery.wicket` (YAML)

Array of wicket objects (usually 1, can be 2 in very rare scenarios).

| Field | Type | Required | Description | Edge Cases |
|-------|------|----------|-------------|------------|
| `player_out` | string | Yes | Name of dismissed player | Can be the non-striker (run out) |
| `kind` | string | Yes | Dismissal type | See values below |
| `fielders` | array | No | Fielders involved | See below. Absent for bowled, LBW. |

**Dismissal types found in IPL data:**
- `"bowled"` — no fielders
- `"caught"` — 1 fielder (the catcher)
- `"caught and bowled"` — no fielders array (bowler is the catcher)
- `"lbw"` — no fielders
- `"stumped"` — 1 fielder (the wicketkeeper)
- `"run out"` — 1+ fielders (thrower, sometimes multiple)
- `"hit wicket"` — no fielders
- `"retired hurt"` — no fielders, not technically a dismissal (batter can return)

**Other dismissal types (not seen in IPL but possible):**
- `"obstructing the field"`
- `"hit the ball twice"`
- `"handled the ball"` (now merged with obstructing the field in Laws)
- `"timed out"`
- `"retired out"` — batter voluntarily retires (strategic, unlike retired hurt)

### 3.9 Fielders

**Path:** `delivery.wickets[].fielders`

Array of fielder objects.

```json
"fielders": [
  {"name": "T Stubbs"}
]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Fielder's name |
| `substitute` | boolean | No | Whether fielder was a substitute | `true` if substitute fielder. Absent if regular player. |

**Edge case:** A substitute fielder can take a catch or effect a run out even though they're not in the playing XI. The `substitute: true` flag indicates this.

### 3.10 Replacements

**Path:** `delivery.replacements`

Substitutions that happened BEFORE this delivery was bowled.

#### Match replacements (player swaps)

```json
"replacements": {
  "match": [
    {
      "in": "TU Deshpande",
      "out": "AT Rayudu",
      "team": "Chennai Super Kings",
      "reason": "impact_player"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `in` | string | Player entering the match |
| `out` | string | Player leaving the match |
| `team` | string | Team making the substitution |
| `reason` | string | Reason for substitution |

**Replacement reasons seen in IPL:**
- `"impact_player"` — IPL's tactical substitute rule (from 2023 season onwards). Each team can substitute one player during the match.
- `"concussion_substitute"` — Player replaced due to concussion
- `"injury_substitute"` — Player replaced due to injury (rare, strict rules)

**Other reasons (non-IPL):**
- `"covid_replacement"`, `"national_callup"`, `"national_release"`, `"supersub"`, `"tactical_substitute"`, `"unknown"`

#### Role replacements (mid-over changes)

```json
"replacements": {
  "role": [
    {"in": "BCJ Cutting", "reason": "injury", "role": "bowler"}
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `in` | string | Player taking over the role |
| `out` | string | Player leaving the role (may be absent for bowler replacements) |
| `role` | string | `"bowler"` or `"batter"` |
| `reason` | string | See below |

**Role replacement reasons:** `"injury"`, `"excluded - excessive short-pitched deliveries"`, `"excluded - high full pitched balls"`, `"excluded - running on the pitch"`, `"too many overs"`, `"unknown"`

---

## 4. Super Over Structure

Super overs appear as additional innings entries with `super_over: true`.

**Typical super over match (4 innings):**
```
innings[0]: { team: "Team A", powerplays: [...] }                    # Regulation 1st innings
innings[1]: { team: "Team B", powerplays: [...], target: {...} }     # Regulation 2nd innings
innings[2]: { team: "Team A", super_over: true }                     # Super over - Team A bats
innings[3]: { team: "Team B", super_over: true }                     # Super over - Team B bats
```

**Double super over (6 innings):** If the first super over is also tied, a second super over is played:
```
innings[0-1]: Regulation
innings[2-3]: First super over (tied)
innings[4-5]: Second super over (decisive)
```

**IPL example:** Match 1216517 (KXIP vs MI, 2020) — the famous double super over match — has 6 innings.

**Outcome for super over matches:**
```json
"outcome": {
  "result": "tie",
  "eliminator": "Kings XI Punjab"
}
```
- `result` is always `"tie"` (the regulation match tied)
- `eliminator` is the team that won the super over

---

## 5. Season Format Variations

The `season` field has inconsistent formatting across IPL history:

| IPL Season | `season` value | Type | Notes |
|------------|---------------|------|-------|
| 2008 | `"2007/08"` | string | First IPL, started in early 2008 but season spans 2007/08 |
| 2009 | `"2009"` | string | Held in South Africa |
| 2010 | `"2009/10"` | string | |
| 2011 | `"2011"` | string | |
| 2012-2019 | `"2012"` ... `"2019"` | string or integer | **Type varies!** Some files use integer, some string |
| 2020 | `"2020/21"` | string | COVID-delayed season in UAE |
| 2021-2025 | `"2021"` ... `"2025"` | string | |

**Must handle:** Both `int` and `str` types, plus split-year format (`"2007/08"`, `"2020/21"`).

---

## 6. External Data: Cricsheet People Register

**Download:** `people.csv` from [cricsheet.org/register/](https://cricsheet.org/register/)

**17,834 unique people** with **27,538 identifiers** across 12 sources.

### people.csv fields:
| Field | Description |
|-------|-------------|
| Cricsheet ID | 8-char hex identifier (matches `registry.people` values) |
| Name | Primary name used in match data |
| Unique name | Disambiguated version (for people with same name) |
| `key_cricinfo` | ESPNcricinfo player ID (17,965 mapped) |
| `key_cricketarchive` | CricketArchive ID (4,509 mapped) |
| `key_bcci` | BCCI ID (1,329 mapped) |
| `key_pulse` | ICC Pulse ID (2,023 mapped) |
| `key_nvplay` | NV Play ID (1,006 mapped) |
| `key_bigbash` | Big Bash League ID (296 mapped) |
| `key_cricingif` | Cricingif ID (130 mapped) |
| `key_cricketworld` | Cricketworld ID (127 mapped) |
| `key_crichq` | CricHQ ID (24 mapped) |
| `key_cricbuzz` | Cricbuzz ID (22 mapped) |
| `key_opta` | Opta ID (68 mapped) |

### names.csv fields:
Lists alternate names for players across different sources and name changes.

**Use case:** Join Cricsheet IDs to ESPNcricinfo player IDs → fetch player profiles, photos, career stats from CricInfo.

---

## 7. Data Quality Notes & Known Issues

1. **YAML ball notation overflow:** Deliveries like `23.10` (10+ balls in an over due to extras) may be parsed as `23.1` by YAML parsers. Fixed in JSON v1.0.0 by using array indexing instead of float keys. **Recommendation: Use JSON format, not YAML.**

2. **Field naming inconsistency:** YAML uses `batsman`, JSON v1.0.0 uses `batter`. YAML uses `wicket` (object/array), JSON uses `wickets` (always array).

3. **Season type inconsistency:** `season` field alternates between string and integer across files. Always cast to string.

4. **Player name variations:** The same person may appear with slightly different names across seasons (e.g., initials may change). Always use the `registry.people` hex ID as the canonical identifier, not the name string.

5. **Missing data:** Some older matches (2008-2010) may lack `officials`, `registry`, `players`, or `powerplays` fields.

6. **Impact player timing:** The `replacements.match` entry for impact players appears on the delivery AFTER which the substitution happened. The substituted player appears in `info.players` for both teams regardless.

7. **Retired hurt vs retired out:** `"retired hurt"` means injury — the batter can potentially return. This is NOT a dismissal for batting average purposes. `"retired out"` (strategic retirement) IS counted as a dismissal. Both appear in the `wickets` array despite "retired hurt" not being a true wicket.

8. **Powerplay `to` field:** Can exceed `X.6` when extras extend an over. For example, `5.7` means 7 deliveries were bowled in the 6th over. Don't assume powerplay ends at ball 6 of over 5.

9. **Super over innings don't have powerplays or target** (unlike regulation innings).

   **Correction from actual data:** Super over innings may or may not have target fields. The chasing super over innings typically does NOT have a target object — the target is simply whatever was scored in the previous super over innings + 1.

10. **Outcome.winner is absent for super over matches.** The match result is `"tie"` with an `"eliminator"`. Don't assume every match has a `winner` field.

---

## 8. IPL-Specific Download Links

| Format | URL | Size | Matches |
|--------|-----|------|---------|
| JSON | `https://cricsheet.org/downloads/ipl_json.zip` | ~3.9 MB | 1,170 |
| YAML | `https://cricsheet.org/downloads/ipl.zip` | ~3.7 MB | 1,170 |
| People register | `https://cricsheet.org/register/` → `people.csv` | — | 17,834 people |

**Recommendation:** Use JSON format. It's v1.0.0 (newer), avoids the YAML ball-notation parsing bug, uses cleaner field names (`batter` not `batsman`), and has proper array structures for wickets.

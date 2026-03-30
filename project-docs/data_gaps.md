# Data Gaps: What Cricsheet Doesn't Have

A systematic mapping of use cases → data requirements → what's missing from Cricsheet.

**Legend:**
- **Derivable** = can be computed from existing Cricsheet ball-by-ball data
- **Missing** = not in Cricsheet at all, needs an external source
- **Partially derivable** = some aspects computable, others need external data

---

## 1. Player Profile Data (Missing)

**Needed by use cases:** #25-36 (player matchups/form), #62-67 (player in context), #124-132 (leaderboards), #245-251 (age/style analysis), and almost every AI narrative use case.

| Data Point | Status | Why It's Needed | Potential Source |
|-----------|--------|-----------------|-----------------|
| Date of birth / age | Missing | Age curve analysis (#245), retirement prediction (#250), "at age X" comparisons (#251) | ESPNcricinfo player pages (joinable via Cricsheet registry → `key_cricinfo`) |
| Nationality / country | Missing | Overseas slot analysis (#41), nationality-based analysis (#248), overseas player value (#198) | ESPNcricinfo |
| Batting hand (left/right) | Missing | Left-arm spinner vs right-hander matchups (#28), batting style evolution (#249) | ESPNcricinfo |
| Bowling style (RF, LF, OB, LB, SLA, LWS, etc.) | Missing | Spin vs pace venue analysis (#17), bowling variety comparison (#40), matchup matrices (#247) | ESPNcricinfo |
| Primary role (batter/bowler/allrounder/keeper) | Missing | Team composition analysis (#37-42), batting depth comparison (#39), keeper identification | ESPNcricinfo |
| Player photo URL | Missing | UI player cards, comparison visuals, social shareable content (#212, #270) | ESPNcricinfo (via player ID) |
| Career span / debut date | Missing | "IPL Legends" narratives (#151), career timeline, experience level | ESPNcricinfo |

**Impact:** This is the single biggest gap. Without player profiles, we can't do matchup analysis by bowling type, overseas vs domestic splits, or age-based analytics. These power a huge chunk of high-value use cases.

**Resolution path:** Download Cricsheet `people.csv` → join via `key_cricinfo` → scrape/API ESPNcricinfo player profiles for ~500 IPL players. One-time effort, cache locally.

---

## 2. Live / Real-Time Match Data (Missing)

**Needed by use cases:** #52-90 (entire "During the Match" scenario), #58-61 (live win probability).

| Data Point | Status | Why It's Needed | Potential Source |
|-----------|--------|-----------------|-----------------|
| Ball-by-ball live feed | Missing | Real-time insights, live win probability (#58-61), momentum tracking (#77-81) | CricAPI, ESPNcricinfo API, or web scraping |
| Current match state | Missing | "Match is happening now" context for the website | Same as above |
| Live commentary text | Missing | AI-augmented live commentary (#179) | ESPNcricinfo ball-by-ball commentary |

**Impact:** Without live data, the site is historical-only during matches. This kills the "real-time AI insights" differentiator.

**Resolution path:** Evaluate CricAPI or similar paid APIs. Alternative: scrape ESPNcricinfo match pages. Cricsheet files are published post-match only. This is the hardest gap to fill.

**Workaround:** For MVP, focus on pre-match previews and post-match analysis (both work with historical data). Add live features in a later phase if a reliable data source is found.

---

## 3. Venue & Playing Conditions (Missing)

**Needed by use cases:** #12-20 (venue analysis), #17 (spin vs pace), #18 (dew factor), #19 (boundary size), #152 (venue encyclopedia), #191 (venue swap analysis).

| Data Point | Status | Why It's Needed | Potential Source |
|-----------|--------|-----------------|-----------------|
| Ground dimensions / boundary lengths | Missing | "Big-hitting ground vs placement ground" (#19), venue personality (#152) | Manual curation, Wikipedia, Cricbuzz venue pages |
| Pitch type / conditions per match | Missing | Spin-friendly vs pace-friendly analysis (#17), tactical suggestions | Not available in structured form. Could extract from CricInfo match reports via AI. |
| Weather (temperature, humidity, wind) | Missing | Conditions impact on scoring, dew factor (#18) | Weather APIs (historical: Open-Meteo; live: OpenWeatherMap) — join on date + city |
| Dew factor | Missing | Second-innings advantage analysis (#18, #90) | Not directly available. Proxy: compare 1st vs 2nd innings economy rates at each venue in evening matches. |
| Altitude | Missing | Ball carry, scoring rates at high-altitude grounds | Manual curation (only ~15 IPL venues) |

**Impact:** Venue analysis is derivable in aggregate from ball-by-ball data (average scores, win % batting first, spin/pace economy). The gaps are about *explaining why* — conditions, dimensions, dew. AI narratives need this context.

**Resolution path:**
- Aggregate venue stats (avg score, bat-first win %, economy by phase): **Derivable from Cricsheet**
- Boundary lengths, altitude: Manual lookup for ~15 venues, store as a small reference table
- Weather: Open-Meteo free historical API, join on date + city
- Pitch/dew: Use CricInfo match summaries as AI context (Phase 2 enrichment)

---

## 4. Auction & Financial Data (Missing)

**Needed by use cases:** #160-165 (auction value), #231-238 (ROI analysis), #154 (auction cohort analysis).

| Data Point | Status | Why It's Needed | Potential Source |
|-----------|--------|-----------------|-----------------|
| Player auction price per season | Missing | ROI analysis (#160-161), "auction steal/bust" (#232-233), cost per run/wicket (#161) | IPL official website, Wikipedia auction pages, Kaggle datasets |
| Base price | Missing | Context for how much a player was expected vs actual price | Same as above |
| Retained vs bought | Missing | Retention value analysis (#164) | Same |
| Team salary cap / purse | Missing | Salary cap efficiency (#165, #238) | IPL official website |
| Unsold players | Missing | "Hidden gem" analysis for future auctions (#241) | Same |

**Impact:** Auction data unlocks the entire "value" narrative — which players are overpaid/underpaid. Very shareable content on LinkedIn. But it's a nice-to-have, not core.

**Resolution path:** Kaggle has IPL auction datasets. Alternatively, scrape Wikipedia's IPL auction pages (well-structured tables). ~200 players per mega auction. Manual effort: medium.

---

## 5. Points Table & Tournament Structure (Partially Derivable)

**Needed by use cases:** #48-50 (playoff stakes), #105-110 (standings impact), #119-123 (standings race).

| Data Point | Status | Why It's Needed | Potential Source |
|-----------|--------|-----------------|-----------------|
| Points per win/loss/tie/NR | Derivable (known rules) | Points table calculation | IPL rules: 2 points for win, 1 for NR, 0 for loss. Apply to match outcomes. |
| Net Run Rate (NRR) | Derivable | Standings tiebreaker | Compute from ball-by-ball: total runs scored / overs faced vs total runs conceded / overs bowled. DLS-affected matches need special handling. |
| Season schedule / fixtures | Missing | "Remaining fixtures difficulty" (#122), upcoming match context | IPL official website, ESPNcricinfo |
| Playoff format | Missing | Qualification scenarios (#108-109), elimination math (#110) | Known rules (top 4 qualify, Qualifier 1/2, Eliminator, Final). Encode as business logic. |
| Match stage (league/qualifier/final) | Partially derivable | Pressure situations, "must-win" context (#51) | Can infer from match_number + season. Finals are typically last 4 matches. |

**Impact:** Points table is fully derivable. Missing pieces are schedule (for forward-looking analysis) and match stage classification.

**Resolution path:** Build points table from match outcomes (straightforward). Scrape current season schedule from ESPNcricinfo. Encode playoff rules as logic.

---

## 6. Written Match Summaries & Commentary (Missing)

**Needed by use cases:** #91 (AI match narrative), #175-178 (narrative generation), #227-230 (data-enriched narratives), #257-260 (journalist tools).

| Data Point | Status | Why It's Needed | Potential Source |
|-----------|--------|-----------------|-----------------|
| Match summary / report text | Missing | Richer AI narratives that capture qualitative factors (#227), context the data can't show (#228) | ESPNcricinfo match pages, Wikipedia |
| Ball-by-ball text commentary | Missing | AI commentary style (#179), extracting pitch/weather mentions (#228) | ESPNcricinfo ball-by-ball commentary pages |
| Expert post-match analysis | Missing | Contrast AI analysis with expert opinion, validate insights | CricInfo editorial content |

**Impact:** AI narratives built purely from numerical data will be good but miss qualitative context (pitch crumbling in 2nd innings, dew making the ball slippery, key dropped catch not in the data). Written summaries fill this gap.

**Resolution path:** Scrape ESPNcricinfo match pages using `key_cricinfo` match IDs. Store as text blobs. Feed to AI alongside numerical data for richer narratives. ~1,170 matches to scrape.

---

## 7. Fielding & Advanced Performance Data (Partially Derivable / Missing)

**Needed by use cases:** #85 (field placement), #100 (unsung hero), #218-226 (ball-by-ball visualizations).

| Data Point | Status | Why It's Needed | Potential Source |
|-----------|--------|-----------------|-----------------|
| Catches taken per player | Derivable | Fielding leaderboard, "unsung hero" (#100) | Count from `wickets[].fielders` where `kind == "caught"` |
| Run-outs effected | Derivable | Same | Count from `wickets[].fielders` where `kind == "run out"` |
| Stumpings | Derivable | Keeper stats | Count from `wickets[].fielders` where `kind == "stumped"` |
| Dropped catches | **Missing** | Turning point analysis (#92), fielding quality | Not in any structured source. Mentioned in commentary only. |
| Fielding position per delivery | **Missing** | Field placement analysis (#85), wagon wheel (#218) | Hawk-Eye / ball tracking data. Not publicly available. |
| Shot direction / wagon wheel | **Missing** | Batter scoring zones, "80% runs on off side" (#67) | Hawk-Eye data. Not publicly available. |
| Ball speed (kph) | **Missing** | Pace analysis, "average speed dropped 5 kph" (#184) | Hawk-Eye / broadcast data. Not publicly available. |
| Ball pitch location (line & length) | **Missing** | Pitch maps (#219), bowler variation analysis (#223) | Hawk-Eye data. Not publicly available. |
| Swing / seam / spin data | **Missing** | Bowling analysis depth | Hawk-Eye data. Not publicly available. |

**Impact:** Basic fielding stats (catches, run-outs, stumpings) are derivable. But ball-tracking data (wagon wheels, pitch maps, ball speed) is NOT available publicly. This limits the depth of bowling/batting analysis to what we can infer from outcomes (runs scored, dot balls, wickets).

**Resolution path:** Derive what we can. Accept that Hawk-Eye level analysis is out of scope. For "shot direction" type insights, AI can infer tendencies from matchup patterns (e.g., "this batter scores faster against spin") but can't show actual wagon wheels.

---

## 8. DRS / Review Data (Missing)

**Needed by use cases:** #146 (umpiring controversy tracker), #194 (DRS counterfactual).

| Data Point | Status | Why It's Needed | Potential Source |
|-----------|--------|-----------------|-----------------|
| Reviews used per team per match | Missing | DRS strategy analysis, umpiring accuracy | CricInfo match scorecards |
| Review outcomes (overturned/upheld/umpire's call) | Missing | Controversy tracking (#146) | CricInfo |
| Remaining reviews | Missing | Tactical context during live match | CricInfo |

**Impact:** Low priority. DRS analysis is niche content, not a core use case.

---

## 9. Team & Franchise Metadata (Missing)

**Needed by use cases:** #133-140 (team analysis), #153 (team dynasty), #164 (retention analysis).

| Data Point | Status | Why It's Needed | Potential Source |
|-----------|--------|-----------------|-----------------|
| Team name changes over seasons | Missing | Historical consistency (Delhi Daredevils → Delhi Capitals, etc.) | Manual curation (~5 team name changes in IPL history) |
| Home venue per season | Missing | Home vs away analysis (#136) | Manual curation or scrape from Wikipedia |
| Captain per match | Missing | Captaincy analysis (#145), "captain's decisions" | CricInfo match scorecards |
| Team colors / logo URLs | Missing | UI/visualization branding | Manual curation for ~14 IPL teams |
| Franchise ownership history | Missing | Narrative context | Wikipedia |

**Impact:** Team name mapping is essential for historical analysis (must merge Delhi Daredevils + Delhi Capitals). Captain and home venue are high-value for narrative richness.

**Resolution path:**
- Team name mapping: small manual lookup table (~5 entries)
- Home venues: manual lookup per season (~18 seasons × ~10 teams)
- Captain: derivable from CricInfo match data, or maintain a small table
- Colors/logos: manual curation for UI

---

## 10. Fantasy Cricket Data (Missing)

**Needed by use cases:** #155-159 (fantasy recommendations), #261-266 (fantasy optimization).

| Data Point | Status | Why It's Needed | Potential Source |
|-----------|--------|-----------------|-----------------|
| Fantasy scoring rules | Missing | Points calculation, optimization | Dream11 / other platform rules (publicly available) |
| Player ownership % | Missing | Differential picks (#157) | Platform APIs or community data |
| Fantasy points per player per match | Derivable (with rules) | Leaderboard, projections | Compute from ball-by-ball + scoring rules |

**Impact:** Fantasy content drives massive engagement in India. Fantasy points are derivable once we define scoring rules. Ownership data needs a platform integration.

**Resolution path:** Encode Dream11 scoring rules as logic. Compute fantasy points from ball-by-ball data. Ownership % is out of scope unless a data source is found.

---

## 11. Cross-League T20 Data (Available but Separate)

**Needed by use cases:** #206 (cross-league comparison), #239-244 (league comparisons).

| Data Point | Status | Why It's Needed | Potential Source |
|-----------|--------|-----------------|-----------------|
| BBL, PSL, CPL, SA20, The Hundred match data | Available (Cricsheet) | Cross-league player comparison (#239), league difficulty index (#240) | Cricsheet has all these leagues in the same format |
| Player identity linking across leagues | Available (registry) | Same player in IPL vs BBL | Cricsheet registry IDs are consistent across leagues |

**Impact:** Nice-to-have. Enriches player profiles but not core to IPL analysis.

**Resolution path:** Download additional league ZIPs from Cricsheet. Same format, same processing pipeline. Low effort, high enrichment.

---

## Summary: Priority-Ordered Gap List

### Must-Have (blocks core use cases)

| # | Gap | Use Cases Blocked | Effort | Source |
|---|-----|-------------------|--------|--------|
| 1 | **Player profiles** (age, nationality, batting/bowling hand, role, bowling style) | Matchup analysis, overseas splits, team composition, leaderboard filtering, AI narratives | Medium — scrape ~500 players from ESPNcricinfo via registry join | ESPNcricinfo |
| 2 | **Team name mapping** (historical name changes) | Any cross-season analysis breaks without this | Trivial — 5-entry lookup table | Manual |
| 3 | **Season schedule / fixtures** (current season) | Pre-match previews, remaining difficulty, playoff math | Low — scrape one page per season | ESPNcricinfo / IPL site |

### High Value (significantly enriches the product)

| # | Gap | Use Cases Blocked | Effort | Source |
|---|-----|-------------------|--------|--------|
| 4 | **Live / real-time match data** | Entire "during match" scenario, real-time AI insights | High — needs API or scraping pipeline + polling | CricAPI / ESPNcricinfo |
| 5 | **Captain per match** | Captaincy analysis, tactical decision attribution | Low-medium — scrape from scorecards or maintain table | ESPNcricinfo |
| 6 | **Home venue per team per season** | Home vs away analysis, venue context | Low — manual table, ~180 entries | Wikipedia / manual |
| 7 | **Written match summaries** | Rich AI narratives, qualitative context | Medium — scrape 1,170 match pages | ESPNcricinfo / Wikipedia |
| 8 | **Historical weather data** | Dew analysis, conditions context | Low — free API (Open-Meteo), join on date + city | Open-Meteo API |

### Medium Value (good for depth and engagement)

| # | Gap | Use Cases Blocked | Effort | Source |
|---|-----|-------------------|--------|--------|
| 9 | **Auction / player price data** | ROI analysis, value narratives, salary cap | Medium — scrape Wikipedia auction tables or Kaggle | Wikipedia / Kaggle |
| 10 | **Fantasy scoring rules** | Fantasy recommendations, fantasy leaderboards | Trivial — encode known rules | Dream11 rules (public) |
| 11 | **Cross-league T20 data** | Cross-league comparisons, hidden gems | Low — same Cricsheet format, just download more ZIPs | Cricsheet |

### Out of Scope (not publicly available)

| # | Gap | Why | Alternative |
|---|-----|-----|-------------|
| 12 | Ball tracking / Hawk-Eye (speed, line, length, trajectory) | Proprietary data, not publicly available | Infer tendencies from outcomes (economy, dot %, boundary %) |
| 13 | Dropped catches | Only in commentary text, not structured | Mention in AI narratives if match summary text is available |
| 14 | Fielding positions per delivery | Proprietary broadcast data | Skip — not critical |
| 15 | Player ownership % (fantasy) | Platform-specific, no public API | Skip or manual sampling |
| 16 | DRS review details | Not in structured form | Low priority, skip for now |

---

## Derivable Data Points (no external source needed)

These are NOT gaps — they can be computed from Cricsheet ball-by-ball data but are worth calling out because they require non-trivial computation:

| Data Point | Derivation Method | Complexity |
|-----------|-------------------|------------|
| Batting order per innings | Order of first appearance of each batter | Simple |
| Batting strike rate by phase (PP/middle/death) | Group deliveries by over range, compute runs/balls per batter | Medium |
| Bowling economy by phase | Same, grouped by bowler | Medium |
| Dot ball % per bowler/batter | Count deliveries where `runs.total == 0` | Simple |
| Boundary count (4s/6s) per player | `runs.batter == 4 or 6` AND `non_boundary` absent | Simple |
| Partnership data | Track runs between consecutive wickets | Medium |
| Powerplay performance | Filter deliveries in overs 0-5 | Simple |
| Death overs performance | Filter deliveries in overs 16-19 | Simple |
| Points table / standings | Apply scoring rules to match outcomes | Medium (DLS/NR edge cases) |
| Net Run Rate | Total runs scored/overs faced vs conceded/bowled | Medium (incomplete innings handling) |
| Catches / run-outs / stumpings per player | Count from `wickets[].fielders` by dismissal type | Simple |
| Win/loss streaks per team | Sequence match outcomes chronologically | Simple |
| Head-to-head records | Filter matches by team pair | Simple |
| Venue aggregate stats | Group matches by venue, compute averages | Simple |
| Player milestones | Cumulative sums across matches | Medium |
| Impact player usage patterns | Extract from `replacements.match` where `reason == "impact_player"` | Simple |

# IPL Data Pipeline

## What this is

A fully automated daily pipeline that:
1. Fetches new IPL match data from Cricsheet
2. Transforms it into clean, queryable tables via dbt
3. Publishes pre-match analysis to the live website

Everything runs on a cron schedule in GitHub Actions at **00:30 UTC (06:00 IST)** daily.

---

## Architecture overview

```
Cricsheet (cricsheet.org)
    │
    ▼
AWS Lambda: ipl-ingestion          ← runs daily, downloads new match data
    │
    ▼
S3: ipl-processed-data             ← raw Parquet files (source of truth)
    │  matches/match_info.parquet
    │  deliveries/ball_by_ball.parquet
    │  batter_scorecard/batter_scorecard.parquet
    │  csv/match_info.csv
    │
    ▼
AWS Glue Catalog: ipl_cricket      ← metadata layer (table schemas)
    │  ipl_cricket.matches
    │  ipl_cricket.deliveries
    │  ipl_cricket.batter_scorecard
    │
    ▼
dbt (runs in GitHub Actions)       ← transforms raw → clean tables
    │
    ▼
Glue Catalog: dbt_prod             ← transformed tables
    │  staging views (stg_*)
    │  dimension tables (dim_*)
    │  fact tables (fct_*)
    │  mart tables (mart_*)
    │
    ▼
generate_prematch.py               ← reads match_info.csv, builds analysis JSON
    │
    ▼
S3: ipl-frontend                   ← static file hosting
    │  prematch.json
    │
    ▼
CloudFront CDN                     ← serves the React frontend
    └─ https://d35f2okpod3reh.cloudfront.net
```

---

## Daily pipeline steps (GitHub Actions)

Workflow file: `.github/workflows/daily_pipeline.yml`
Trigger: `cron: '30 0 * * *'` (00:30 UTC) + manual dispatch

### Step 1 — Ingest new match data (Lambda)

**What**: Invokes `ipl-ingestion` Lambda synchronously and waits for it to finish.

**What the Lambda does** (`lambda/ingestion/handler.py`):
- Downloads the Cricsheet YAML zip (~15 MB) from cricsheet.org
- Compares filenames against existing `match_info.parquet` in S3
- Parses only **new** YAML files into match rows
- Appends new rows → writes `matches/match_info.parquet` + `csv/match_info.csv` to S3
- Downloads the Cricsheet JSON zip for ball-by-ball data
- Appends new delivery rows → writes `deliveries/ball_by_ball.parquet` to S3
- Generates batter scorecards for new match IDs only → writes `batter_scorecard/batter_scorecard.parquet`

All three datasets are **incremental** — only new matches are processed each run. On a typical day with 1–2 new matches, the Lambda finishes in under 60 seconds.

**Lambda config**: 1 GB memory, 5 min timeout, 1 GB ephemeral storage (for zip downloads).

---

### Step 2 — Transform data (dbt)

**What**: Runs the full dbt model DAG against Athena. All models are full-refresh tables (the data is small enough that this is faster and simpler than incremental).

**dbt project**: `ipl_dbt/`

#### Model layers

```
ipl_cricket.{matches,deliveries,batter_scorecard}   ← Glue source tables (raw S3 Parquet)
        │
        ▼
staging/ (views — no storage, always fresh)
  stg_matches           type-casts + date parse on raw matches
  stg_deliveries        type-casts + phase label (Powerplay/Middle/Death)
  stg_batter_scorecard  type-casts on batter scorecard
        │
        ▼
dimensions/ (tables)
  dim_teams     maps old franchise names → canonical current names
                e.g. "Delhi Daredevils" → "Delhi Capitals"
  dim_venues    maps city aliases → canonical city names
                e.g. "Mohali" → "Chandigarh"
        │
        ▼
facts/ (tables)
  fct_matches     one row per match, names normalised via dim_teams + dim_venues
  fct_deliveries  one row per ball, teams/city normalised, phase label attached
        │
        ▼
marts/ (tables — business-ready aggregations)
  mart_player_career_stats   runs, SR, average, 50s, 100s by (batter, season)
  mart_team_season_stats     wins, losses, win% by (team, season)
  mart_venue_stats           toss stats, bat-first vs field-first win rate by venue
  mart_phase_stats           runs, wickets, run-rate by (phase, team, season)
```

**Seeds** (static lookup CSVs checked into the repo):
- `dim_team_aliases.csv` — franchise rename map
- `dim_venue_aliases.csv` — city alias map

**dbt test results (as of first run)**:
- 30 PASS, 2 WARN (known source data gaps), 0 ERROR
- Warnings: 2 Cricsheet venues with no city recorded; 15 old matches with no season field

---

### Step 3 — Pre-match analysis

**What**: Downloads the fresh `match_info.csv` from S3 (updated by Lambda in Step 1), then runs `generate_prematch.py` locally inside the GitHub Actions runner.

`generate_prematch.py` reads `data_sources/ipl_2026_matches.csv` (schedule, committed to repo) and `data_modeling/match_info.csv` (history, downloaded from S3), and outputs `frontend/public/prematch.json` containing:
- Head-to-head record (all-time + last 5)
- Each team's venue record
- Toss analysis at the venue
- Recent form for each team (last 5 matches)

---

### Step 4 — Publish

- Uploads `prematch.json` to S3 frontend bucket
- Creates a CloudFront invalidation for `/prematch.json` so the CDN serves the new file immediately

---

## AWS resources

| Resource | Name | Purpose |
|---|---|---|
| Lambda | `ipl-ingestion` | Daily data fetch from Cricsheet |
| Lambda | `ipl-query-runner` | Runs user SQL queries from the frontend |
| S3 | `ipl-processed-data-814871720600` | Parquet + CSV data files |
| S3 | `ipl-frontend-814871720600` | React app + prematch.json |
| S3 | `ipl-athena-results-814871720600` | Athena query results + dbt staging |
| Glue DB | `ipl_cricket` | Schema for raw source tables |
| Glue DB | `dbt_prod` | Schema for dbt-transformed tables |
| Glue DB | `dbt_dev` | Schema for local dbt development |
| Athena workgroup | `ipl-workgroup` | Query execution config |
| CloudFront | `E3OPF5PBRU90E9` | CDN for the frontend |
| IAM role | `ipl-github-actions-role` | OIDC role assumed by GitHub Actions |

---

## Auth

GitHub Actions authenticates to AWS via **OIDC** (no hardcoded keys). The `ipl-github-actions-role` IAM role has a trust policy restricted to `repo:aadi-jn/ipl_data:*`. The role ARN is stored as the `AWS_ROLE_ARN` GitHub Actions secret.

---

## Local development

### Run dbt locally (dev target → writes to `dbt_dev` Glue database)

```bash
# One-time setup
cp ipl_dbt/profiles.yml.example ~/.dbt/profiles.yml

# Commands (must use miniconda dbt, not dbt-fusion)
/Users/aadi/miniconda3/bin/dbt seed --target dev
/Users/aadi/miniconda3/bin/dbt run --target dev
/Users/aadi/miniconda3/bin/dbt test --target dev
```

### Run ingestion locally

```bash
# Update match_info
python3 data_sources/update_match_info.py
aws s3 cp data_modeling/match_info.parquet s3://ipl-processed-data-814871720600/matches/match_info.parquet
aws s3 cp data_modeling/match_info.csv s3://ipl-processed-data-814871720600/csv/match_info.csv

# Generate prematch JSON
python3 data_sources/generate_prematch.py

# Deploy frontend
cd frontend && npm run build
aws s3 sync dist/ s3://ipl-frontend-814871720600/ --delete
aws cloudfront create-invalidation --distribution-id E3OPF5PBRU90E9 --paths "/*"
```

### Trigger the daily pipeline manually

Go to: https://github.com/aadi-jn/ipl_data/actions → "Daily IPL Pipeline" → "Run workflow"

---

## Known limitations / future work

- `generate_prematch.py` still reads local CSVs (Step 6 deferred) — in future it should query `mart_*` tables from Athena directly
- `ipl_2026_matches.csv` (schedule) is committed to the repo and updated manually; could be automated via CricAPI (`fetch_matches.py`) with a `CRICAPI_KEY` GitHub secret
- dbt models are full-refresh; if the delivery dataset grows significantly, `fct_deliveries` could be made incremental with date partitioning
- The `ipl-ingestion` Lambda requires Docker at CDK deploy time (for Python dependency bundling)

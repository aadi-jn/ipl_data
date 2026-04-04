# Architecture Decisions & Deployed Resources

## Decisions

### 2026-03-28: Project Initialization
- **CDK Language**: Python — keeps the entire project in one language
- **Region**: ap-south-1 (Mumbai) — closest to IPL audience, supports Bedrock
- **IaC Tool**: AWS CDK over raw CloudFormation for higher-level abstractions and faster iteration

### 2026-03-29: Frontend
- **React + Vite over CRA**: Vite is significantly faster to build; CRA is effectively deprecated
- **Inline styles alongside Tailwind**: Used inline styles for the custom hex colors (#1a1a2e, #e2b714) to avoid arbitrary Tailwind value issues at build time
- **CloudFront in front of S3 website endpoint**: Used `HttpOrigin` pointing at the S3 website URL (not OAC) because the bucket is already public. Simple and sufficient for now
- **Manual S3 sync instead of BucketDeployment**: Kept infra and app builds separate — CDK handles AWS resources, `aws s3 sync` handles static asset uploads
- **CloudFront `PRICE_CLASS_ALL`**: Ensures Indian users get served from Mumbai edge nodes

### 2026-03-29: Backend API
- **Lambda over container**: Simple Python 3.12 Lambda (256 MB, 60s timeout) — no dependencies beyond boto3, no Docker needed
- **SQL validation in Lambda**: Regex-based SELECT-only guard + auto-append `LIMIT 50` if missing — keeps queries safe and cheap
- **Athena polling**: Exponential backoff (1s → 8s max) with 55s hard deadline, leaving headroom before Lambda timeout
- **API Gateway usage plan**: 10 rps / 1000 per day — prevents accidental cost spikes during development
- **CORS wide-open for now**: `allow_origins=*` — will restrict to frontend origin once frontend is deployed

### 2026-03-28: Data Layer Infrastructure
- **Storage format**: Parquet with Snappy compression — columnar format ideal for analytical queries
- **Glue tables defined explicitly** (no crawler) — deterministic schemas, faster deploys, no runtime cost
- **Athena workgroup**: Enforced config so all queries use the designated results bucket
- **S3 bucket names**: Suffixed with account ID to ensure global uniqueness
- **RemovalPolicy.DESTROY**: All buckets set to auto-delete for easy teardown during development

### 2026-03-31: Data Pipeline & Pre-Match Analysis
- **Local pipeline over AWS cron**: The daily data update (Cricsheet zip download, YAML parsing, Parquet generation) runs locally — Lambda's 15-min timeout + heavy dependencies (pyyaml, pandas, pyarrow) make it overkill for a single-user daily job. Can move to ECS Fargate later if needed.
- **Three-script pipeline**: Separated concerns — `fetch_matches.py` (CricAPI schedule), `update_match_info.py` (Cricsheet historical data), `generate_prematch.py` (pre-computed analysis). Each is idempotent and can run independently.
- **Static JSON for pre-match data**: Pre-computed analysis served as `prematch.json` from CloudFront instead of running Athena queries on tab load. Zero additional Athena cost, instant load time, data only changes once/day anyway.
- **Team name normalization**: Franchise renames (Delhi Daredevils→Capitals, Kings XI Punjab→Punjab Kings, RCB Bangalore→Bengaluru) handled in `generate_prematch.py` with alias dicts. City aliases too (Mohali/Chandigarh/New Chandigarh all map to Chandigarh).
- **Tab-based frontend**: Added "Today's Match" as default landing tab with dropdown for double-header days. "Query Engine" tab retains all existing SQL functionality.

### 2026-04-01: dbt Layer & Automated Pipeline
- **dbt-core + dbt-athena-community**: Full model stack (staging → dimensions → facts → marts) running against Athena/Glue. dbt-athena uses `database: AwsDataCatalog` (the Athena catalog name) and `schema: dbt_dev|dbt_prod` (Glue database name). This mapping is not intuitive — `database` ≠ Glue database.
- **Full-refresh over incremental**: All fact/mart tables are `materialized: table` (full refresh). At ~278K deliveries and ~1,200 matches, Athena CTAS rebuilds the entire dataset in under 7 seconds per model. Incremental with dbt-athena requires Iceberg tables — unnecessary complexity at this scale.
- **Docker container Lambda**: The ingestion Lambda packages pandas + pyarrow + pyyaml (~300 MB unzipped), exceeding Lambda's 250 MB zip limit. Switched from `Code.from_asset` with bundling to `DockerImageFunction` using ECR. CDK builds and pushes the image automatically during deploy.
- **S3 path separation**: CSV and Parquet files must be in different S3 prefixes. Athena scans all files in a table's `LOCATION` — a CSV in a Parquet table's folder causes `HIVE_BAD_DATA: Malformed Parquet file`. match_info.csv lives at `csv/match_info.csv`, Parquet at `matches/match_info.parquet`.
- **GitHub Actions OIDC**: No hardcoded AWS keys. GitHub OIDC provider + IAM role with trust policy restricted to `repo:aadi-jn/ipl_data:*`. Only one secret needed: `AWS_ROLE_ARN`.
- **dbt-fusion vs dbt-core**: The system has `dbt-fusion` (a separate product) at `/Users/aadi/.local/bin/dbt`. dbt-core + dbt-athena-community is in miniconda at `/Users/aadi/miniconda3/bin/dbt`. GitHub Actions installs dbt-core fresh, so no conflict in CI.
- **Team/venue normalization via dbt seeds**: Extracted the alias dicts from `generate_prematch.py` into `dim_team_aliases.csv` and `dim_venue_aliases.csv` as dbt seeds. The `dim_teams` and `dim_venues` models join raw names to canonical names, and all downstream facts/marts use normalized values.

## Deployed Resources

### S3 Buckets
| Bucket | Name | Purpose |
|--------|------|---------|
| Raw Data | `ipl-raw-data-814871720600` | Upload original YAML cricket files |
| Processed Data | `ipl-processed-data-814871720600` | Parquet files (matches/, match_players/, deliveries/) |
| Frontend | `ipl-frontend-814871720600` | Static website hosting |
| Athena Results | `ipl-athena-results-814871720600` | Athena query output |

**Frontend URL**: http://ipl-frontend-814871720600.s3-website.ap-south-1.amazonaws.com

### Glue
- **Database**: `ipl_cricket` — 3 raw source tables
- **Database**: `dbt_prod` — 11 dbt-transformed tables (production pipeline)
- **Database**: `dbt_dev` — 11 dbt-transformed tables (local development)
- **Database**: `dbt_prod_seeds` / `dbt_dev_seeds` — seed lookup tables

| Glue Table | Database | S3 Location | Rows |
|------------|----------|-------------|------|
| `matches` | `ipl_cricket` | `matches/match_info.parquet` | 1,172 |
| `deliveries` | `ipl_cricket` | `deliveries/ball_by_ball.parquet` | 278,205 |
| `batter_scorecard` | `ipl_cricket` | `batter_scorecard/batter_scorecard.parquet` | ~15,000 |
| `stg_matches` | `dbt_prod` | (view) | — |
| `stg_deliveries` | `dbt_prod` | (view) | — |
| `stg_batter_scorecard` | `dbt_prod` | (view) | — |
| `dim_teams` | `dbt_prod` | `dbt/` | 19 |
| `dim_venues` | `dbt_prod` | `dbt/` | 63 |
| `fct_matches` | `dbt_prod` | `dbt/` | 1,172 |
| `fct_deliveries` | `dbt_prod` | `dbt/` | 278,205 |
| `mart_player_career_stats` | `dbt_prod` | `dbt/` | 2,783 |
| `mart_team_season_stats` | `dbt_prod` | `dbt/` | 15 |
| `mart_venue_stats` | `dbt_prod` | `dbt/` | 59 |
| `mart_phase_stats` | `dbt_prod` | `dbt/` | 468 |

### Athena
- **Workgroup**: `ipl-workgroup` → results at `s3://ipl-athena-results-814871720600/results/`

### Athena Query Results (2026-03-29)
- Total matches: **1169**
- Top 5 winners: Mumbai Indians (153), Chennai Super Kings (142), Kolkata Knight Riders (136), Rajasthan Royals (116), Royal Challengers Bangalore (116)
- Most played matchup: Chennai Super Kings vs Mumbai Indians (23 games)

### Lambda
- **Function**: `ipl-query-runner` (Python 3.12, 256 MB, 60s timeout)
  - Code: `lambda/query_runner/handler.py`
  - IAM: Athena query execution, S3 read (processed) + read/write (results), Glue catalog read
- **Function**: `ipl-ingestion` (Docker container via ECR, 1024 MB, 5 min timeout, 1 GB /tmp)
  - Code: `lambda/ingestion/handler.py` + `Dockerfile`
  - IAM: S3 read/write on processed data bucket
  - Dependencies: pandas, pyarrow, pyyaml, boto3

### ECR
- **Repository**: `cdk-hnb659fds-container-assets-814871720600-ap-south-1` (CDK-managed)
- Contains Docker image for `ipl-ingestion` Lambda

### IAM (manual, not in CDK)
- **Role**: `ipl-github-actions-role`
- **Trust**: GitHub OIDC (`token.actions.githubusercontent.com`), restricted to `repo:aadi-jn/ipl_data:*`
- **Permissions**: Athena execute, S3 read/write (processed + results + frontend), Glue catalog read/write, CloudFront invalidation, Lambda invoke (`ipl-ingestion`)

### GitHub Actions
- **Workflow**: `.github/workflows/daily_pipeline.yml`
- **Schedule**: `cron: '30 0 * * *'` (00:30 UTC / 06:00 IST daily)
- **Secret**: `AWS_ROLE_ARN` — ARN of `ipl-github-actions-role`
- **Steps**: Invoke Lambda → dbt seed/run/test → download CSV → generate_prematch.py → upload prematch.json → CloudFront invalidation

### API Gateway
- **API**: `ipl-api` (REST, stage: `prod`)
- **Endpoint**: `POST https://k9s4lfemfe.execute-api.ap-south-1.amazonaws.com/prod/query`
- **Request**: `{ "query": "SELECT ..." }`
- **Response**: `{ "columns": [...], "data": [...], "row_count": N, "query": "..." }`
- **Usage plan**: 10 rps burst, 1000 requests/day
- **CORS**: All origins (to be restricted after frontend deployed)

### Frontend
- **Framework**: React 18 + Vite 5 + Tailwind CSS 3
- **Source**: `frontend/src/App.jsx` (single-component SPA)
- **Build**: `frontend/dist/` → synced to `s3://ipl-frontend-814871720600/`
- **Features**: Three tabs — "Today's Match" (pre-match analysis with H2H, venue, toss, form), "Latest Match" (full batting/bowling scorecard from Athena deliveries), and "Query Engine" (SQL editor, sortable results table, 8 example queries, collapsible schema reference)

### CloudFront
- **Distribution ID**: `E3OPF5PBRU90E9`
- **URL**: `https://d35f2okpod3reh.cloudfront.net` ← **Live site**
- **Origin**: S3 website endpoint (`ipl-frontend-814871720600.s3-website.ap-south-1.amazonaws.com`)
- **Price class**: All (includes Mumbai edge nodes)
- **SPA routing**: 404/403 → `index.html` via error response config

### CloudFormation
- **Stack**: `IplStack` (arn:aws:cloudformation:ap-south-1:814871720600:stack/IplStack/6b6e2b80-2ab7-11f1-ba4e-0a7b269a06b5)

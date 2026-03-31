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
- **Database**: `ipl_cricket`
- **Tables**: `matches` (9 columns: filename, team1, team2, date, winner, win_type, win_margin, method, parsed_date)
- `match_players` and `deliveries` tables removed (to be added when data is ready)
- All tables point to `s3://ipl-processed-data-814871720600/<table_name>/`

### Data Uploaded
| File | S3 Path | Rows |
|------|---------|------|
| match_info.csv → match_info.parquet | `s3://ipl-processed-data-814871720600/matches/match_info.parquet` | 1172 (2008-2026) |

### Athena
- **Workgroup**: `ipl-workgroup` → results at `s3://ipl-athena-results-814871720600/results/`

### Athena Query Results (2026-03-29)
- Total matches: **1169**
- Top 5 winners: Mumbai Indians (153), Chennai Super Kings (142), Kolkata Knight Riders (136), Rajasthan Royals (116), Royal Challengers Bangalore (116)
- Most played matchup: Chennai Super Kings vs Mumbai Indians (23 games)

### Lambda
- **Function**: `ipl-query-runner` (Python 3.12, 256 MB, 60s timeout)
- **Code**: `lambda/query_runner/handler.py`
- **IAM**: Athena query execution, S3 read (processed) + read/write (results), Glue catalog read

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
- **Features**: Two tabs — "Today's Match" (pre-match analysis with H2H, venue, toss, form) and "Query Engine" (SQL editor, sortable results table, 8 example queries, collapsible schema reference)

### CloudFront
- **Distribution ID**: `E3OPF5PBRU90E9`
- **URL**: `https://d35f2okpod3reh.cloudfront.net` ← **Live site**
- **Origin**: S3 website endpoint (`ipl-frontend-814871720600.s3-website.ap-south-1.amazonaws.com`)
- **Price class**: All (includes Mumbai edge nodes)
- **SPA routing**: 404/403 → `index.html` via error response config

### CloudFormation
- **Stack**: `IplStack` (arn:aws:cloudformation:ap-south-1:814871720600:stack/IplStack/6b6e2b80-2ab7-11f1-ba4e-0a7b269a06b5)

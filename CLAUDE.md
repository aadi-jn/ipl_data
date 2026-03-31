# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Serverless IPL cricket analytics platform: users write SQL queries against IPL match data via a web UI, which runs them through Lambda → Athena → Parquet on S3. Deployed in `ap-south-1` (Mumbai). Live at https://d35f2okpod3reh.cloudfront.net.

## Architecture

```
React SPA (Vite + Tailwind) → CloudFront → API Gateway (POST /query) → Lambda (Python 3.12) → Athena → Parquet in S3
```

- **CDK stack**: `ipl/ipl_stack.py` — all AWS resources (S3 buckets, Glue catalog, Athena workgroup, Lambda, API Gateway, CloudFront)
- **CDK entry**: `app.py` — instantiates `IplStack`, hardcoded to `ap-south-1`
- **Lambda**: `lambda/query_runner/handler.py` — SQL validation (SELECT-only, regex-based), auto-appends `LIMIT 50`, polls Athena with exponential backoff
- **Frontend**: `frontend/src/App.jsx` — two-tab SPA: "Today's Match" (pre-match analysis) and "Query Engine" (SQL editor)
- **Data**: Parquet files in S3, queried via Glue table `ipl_cricket.matches` (1,172 rows, 2008-2026)
- **Data pipeline**: Local Python scripts in `data_sources/` — run daily to fetch schedule, update match history, and generate pre-match analysis

## Commands

### Infrastructure (CDK)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cdk synth          # synthesize CloudFormation template
cdk diff           # preview changes
cdk deploy         # deploy stack
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # local dev server (Vite)
npm run build      # production build → dist/
```

### Deploy frontend to S3 + invalidate CloudFront
```bash
cd frontend && npm run build
aws s3 sync dist/ s3://ipl-frontend-814871720600/ --delete
aws cloudfront create-invalidation --distribution-id E3OPF5PBRU90E9 --paths "/*"
```

### Daily Data Pipeline (run locally)
```bash
python3 data_sources/fetch_matches.py          # IPL 2026 schedule from CricAPI → data_sources/ipl_2026_matches.csv
python3 data_sources/update_match_info.py      # New match results from Cricsheet → data_modeling/match_info.csv + .parquet
python3 data_sources/generate_prematch.py      # Pre-match analysis → frontend/public/prematch.json
aws s3 cp data_modeling/match_info.parquet s3://ipl-processed-data-814871720600/matches/match_info.parquet
```

### Tests
```bash
pytest                              # all tests
pytest tests/unit/test_ipl_stack.py # single test file
```

## Key Details

- **API throttling**: 10 rps burst, 1000 requests/day via API Gateway usage plan
- **Lambda timeout**: 60s, with 55s internal polling deadline for Athena queries
- **All S3 buckets** have `RemovalPolicy.DESTROY` — development-mode teardown
- **Glue tables are defined explicitly** in the CDK stack (no crawler)
- **Frontend API URL** is hardcoded in `frontend/src/App.jsx` (`API_URL` constant)
- **CSS theming**: CricInfo-inspired design using CSS custom properties (defined in `frontend/src/index.css`), not Tailwind theme extension
- **Data pipeline**: Three scripts in `data_sources/` run daily: `fetch_matches.py` (CricAPI schedule), `update_match_info.py` (Cricsheet YAML → CSV/Parquet), `generate_prematch.py` (pre-match analysis JSON)
- **Pre-match data**: `frontend/public/prematch.json` — static JSON loaded by frontend, regenerated daily. Includes H2H, venue record, toss analysis, recent form
- **Team name normalization**: `generate_prematch.py` handles franchise renames (Delhi Daredevils→Capitals, Kings XI Punjab→Punjab Kings, etc.) and city aliases (Mohali/Chandigarh/New Chandigarh)

## Project Docs

- `PROJECT.md` — full project plan, phases, architecture target state
- `NOTES.md` — architecture decisions log and deployed resource inventory
- `project-docs/weekly_plan.md` — week-by-week breakdown
- `project-docs/data_format.md` — raw data format reference (Cricsheet YAML/JSON)
- `project-docs/data_gaps.md` — known data quality issues

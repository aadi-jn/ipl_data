# IPL Cricket Query Engine

A serverless web app for querying IPL cricket match data with plain SQL.

**Live:** https://d35f2okpod3reh.cloudfront.net

---

## Architecture

```
Browser
  │
  │  HTTPS
  ▼
CloudFront (d35f2okpod3reh.cloudfront.net)
  │
  ├──► S3 (ipl-frontend-*)          React + Vite SPA (static files)
  │
  └──► API Gateway (POST /query)
         │
         ▼
       Lambda (ipl-query-runner, Python 3.12)
         │  validates SQL, adds LIMIT if missing
         ▼
       Athena (ipl-workgroup)
         │  queries Parquet files via Glue catalog
         ├──► S3 (ipl-processed-data-*)   match_info.parquet (1,169 rows)
         └──► S3 (ipl-athena-results-*)   query results output
```

---

## Data

| Table     | Rows  | Location                                          |
|-----------|-------|---------------------------------------------------|
| `matches` | 1,169 | `s3://ipl-processed-data-814871720600/matches/`   |

**Schema:**

| Column       | Type    | Notes                                      |
|--------------|---------|--------------------------------------------|
| filename     | string  | Source YAML file                           |
| team1        | string  | First-listed team                          |
| team2        | string  | Second-listed team                         |
| date         | string  | YYYY-MM-DD                                 |
| winner       | string  | Winning team                               |
| win_type     | string  | "runs", "wickets", "super over", "bowl out"|
| win_margin   | bigint  | Runs or wickets                            |
| method       | string  | "D/L" or null                              |
| parsed_date  | string  | YYYY-MM-DD                                 |

---

## API

**Endpoint:** `POST https://k9s4lfemfe.execute-api.ap-south-1.amazonaws.com/prod/query`

**Request:**
```json
{ "query": "SELECT winner, COUNT(*) as wins FROM matches GROUP BY winner ORDER BY wins DESC LIMIT 5" }
```

**Response:**
```json
{
  "columns": ["winner", "wins"],
  "data": [["Mumbai Indians", "153"], ["Chennai Super Kings", "142"]],
  "row_count": 5,
  "query": "SELECT winner, COUNT(*) as wins FROM matches GROUP BY winner ORDER BY wins DESC LIMIT 5"
}
```

**Rules:** SELECT only · LIMIT 50 auto-appended if missing · 55s timeout

---

## Project Structure

```
ipl/
  ipl_stack.py          CDK stack (S3, Glue, Athena, Lambda, API GW, CloudFront)
app.py                  CDK app entry point
lambda/
  query_runner/
    handler.py          Lambda function (SQL validation + Athena execution)
frontend/
  src/App.jsx           React SPA (single component)
  src/main.jsx
  index.html
  vite.config.js
  tailwind.config.js
```

---

## Setup

### Prerequisites

- AWS CLI configured for `ap-south-1`
- Node.js 20+ and Python 3.12+
- AWS CDK CLI: `npm install -g aws-cdk`

### Deploy infrastructure

```bash
# Create and activate Python venv
python3 -m venv .venv
source .venv/bin/activate

# Install CDK dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy
cdk deploy
```

### Build and upload frontend

```bash
cd frontend
npm install
npm run build
aws s3 sync dist/ s3://ipl-frontend-<account-id>/ --delete
```

### Re-deploy after code changes

```bash
# Lambda changes: cdk deploy handles bundling automatically
cdk deploy

# Frontend changes: rebuild and re-sync
cd frontend && npm run build
aws s3 sync dist/ s3://ipl-frontend-<account-id>/ --delete
aws cloudfront create-invalidation --distribution-id E3OPF5PBRU90E9 --paths "/*"
```

---

## AWS Resources

| Resource             | Name / ID                                              |
|----------------------|--------------------------------------------------------|
| CloudFront           | `E3OPF5PBRU90E9` — d35f2okpod3reh.cloudfront.net      |
| API Gateway          | `ipl-api` — k9s4lfemfe.execute-api.ap-south-1         |
| Lambda               | `ipl-query-runner`                                     |
| Glue Database        | `ipl_cricket`                                          |
| Athena Workgroup     | `ipl-workgroup`                                        |
| S3 Frontend          | `ipl-frontend-814871720600`                            |
| S3 Processed Data    | `ipl-processed-data-814871720600`                      |
| S3 Athena Results    | `ipl-athena-results-814871720600`                      |
| CloudFormation Stack | `IplStack` (ap-south-1)                                |

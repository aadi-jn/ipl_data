# Data Model Runbook

How to take a new or updated data model from CSV to queryable on the frontend.

---

## Pipeline Overview

```
Notebook (extract & transform)
  → CSV / Parquet in data_modeling/
    → S3 upload (processed bucket, Parquet)
      → Glue table definition (ipl_stack.py)
        → CDK deploy
          → Frontend schema + examples (App.jsx)
            → Frontend deploy to S3 + CloudFront invalidation
```

---

## Steps

### 1. Build the data model

- Create/update a notebook in `data_modeling/` that extracts and transforms data from source files.
- Output both CSV (for inspection) and Parquet (for Athena) to `data_modeling/`.
- Name the Parquet file to match the intended Athena table name (e.g., `match_info.parquet` → table `match_info`).

### 2. Upload Parquet to S3

```bash
aws s3 cp data_modeling/<model>.parquet s3://ipl-processed-data-<account>/<table_name>/
```

- The S3 path prefix must match what the Glue table points to.
- For an **updated** model (same table, new columns), replace the existing file at the same path.
- For a **new** model, create a new prefix folder.

### 3. Update Glue table in CDK (`ipl/ipl_stack.py`)

**If updating an existing table:** modify the `columns` list in the existing `glue.CfnTable` block.

**If adding a new table:** duplicate the `glue.CfnTable` block and update:
- `Name` — the Athena table name
- `columns` — list of `{"name": ..., "type": ...}` matching the Parquet schema
- `location` — S3 path from step 2

Column type mapping (Python → Glue/Athena):
| Python / Pandas | Glue type |
|-----------------|-----------|
| str / object    | `string`  |
| int64           | `bigint`  |
| float64         | `double`  |
| bool            | `boolean` |
| date            | `date`    |
| datetime        | `timestamp` |

### 4. Deploy infrastructure

```bash
cdk deploy
```

This updates the Glue catalog. Athena can now query the new/updated table.

**Verify in Athena console or CLI:**
```sql
SELECT * FROM ipl_cricket.<table_name> LIMIT 5;
```

### 5. Update frontend schema (`frontend/src/App.jsx`)

**a) Update or add to the `SCHEMA` constant** (currently line ~5):

Add entries for new columns:
```js
{ name: "column_name", type: "string", note: "Short description" }
```

For a new table, consider whether SCHEMA should become table-aware (e.g., a map of table → columns).

**b) Update or add `EXAMPLES`** (currently line ~17):

Add/update example queries that reference the new columns or table. These are what users see as starter queries.

### 6. Deploy frontend

```bash
cd frontend && npm run build
aws s3 sync build/ s3://ipl-frontend-<account>/ --delete
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

---

## Checklist (copy per model)

```
[ ] Notebook created/updated in data_modeling/
[ ] CSV + Parquet generated
[ ] Parquet uploaded to correct S3 path
[ ] Glue table added/updated in ipl_stack.py
[ ] cdk deploy successful
[ ] Athena test query works
[ ] Frontend SCHEMA updated
[ ] Frontend EXAMPLES updated (if applicable)
[ ] Frontend built and deployed
[ ] CloudFront invalidation created
```

---

## Notes

- **Lambda needs no changes** — it's query-agnostic. It forwards any SELECT to Athena and returns results.
- **API Gateway needs no changes** — it proxies to Lambda.
- **Athena workgroup and database are shared** across all tables, no per-table config needed.
- All tables live in the `ipl_cricket` Glue database.
- Athena auto-adds `LIMIT 50` via Lambda if the query doesn't include one.

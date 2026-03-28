# Architecture Decisions & Deployed Resources

## Decisions

### 2026-03-28: Project Initialization
- **CDK Language**: Python — keeps the entire project in one language
- **Region**: ap-south-1 (Mumbai) — closest to IPL audience, supports Bedrock
- **IaC Tool**: AWS CDK over raw CloudFormation for higher-level abstractions and faster iteration

### 2026-03-28: Data Layer Infrastructure
- **Storage format**: Parquet with Snappy compression — columnar format ideal for analytical queries
- **Glue tables defined explicitly** (no crawler) — deterministic schemas, faster deploys, no runtime cost
- **Athena workgroup**: Enforced config so all queries use the designated results bucket
- **S3 bucket names**: Suffixed with account ID to ensure global uniqueness
- **RemovalPolicy.DESTROY**: All buckets set to auto-delete for easy teardown during development

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
- **Tables**: `matches` (15 columns), `match_players` (4 columns), `deliveries` (14 columns)
- All tables point to `s3://ipl-processed-data-814871720600/<table_name>/`

### Athena
- **Workgroup**: `ipl-workgroup` → results at `s3://ipl-athena-results-814871720600/results/`

### CloudFormation
- **Stack**: `IplStack` (arn:aws:cloudformation:ap-south-1:814871720600:stack/IplStack/6b6e2b80-2ab7-11f1-ba4e-0a7b269a06b5)

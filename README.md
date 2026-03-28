# IPL Cricket Q&A App

A serverless IPL (Indian Premier League) cricket Q&A application powered by AWS services.

## Architecture

- **AWS Bedrock** — LLM-powered natural language Q&A about IPL cricket data
- **AWS Lambda** — Serverless compute for handling queries
- **Amazon API Gateway** — REST API endpoint
- **Amazon DynamoDB / S3** — Data storage for IPL datasets
- **AWS CDK (Python)** — Infrastructure as code

## Prerequisites

- AWS CLI configured with `ap-south-1` region
- Node.js and npm (for CDK CLI)
- Python 3.12+

## Getting Started

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Synthesize CloudFormation template
cdk synth

# Deploy
cdk deploy
```

## Project Structure

```
ipl/
  ipl_stack.py       # CDK stack definition
app.py               # CDK app entry point
tests/               # Unit tests
```

# Deployment Scripts

Automated deployment scripts for AWS infrastructure.

## Scripts

### `deploy-infrastructure.py`
- Creates all AWS resources
- Sets up IAM roles and policies
- Configures API Gateway, Lambda, Lex, DynamoDB, ElasticSearch

### `deploy-frontend.py`
- Builds React application
- Uploads to S3 bucket
- Configures static website hosting

## Prerequisites

- AWS CLI configured
- Appropriate IAM permissions
- Python 3.x with boto3

## Usage

```bash
# Deploy all infrastructure
python deploy-infrastructure.py

# Deploy frontend only
python deploy-frontend.py
```

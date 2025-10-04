# Data Processor Lambda

Processes restaurant requests from SQS queue and sends recommendations via email.

## Function Details

- **Runtime**: Python 3.9
- **Timeout**: 5 minutes
- **Memory**: 512 MB
- **Trigger**: SQS Queue

## Dependencies

```python
boto3>=1.26.0
requests>=2.28.0
```

## Environment Variables

- `DYNAMODB_TABLE`: DynamoDB table name for restaurants
- `ELASTICSEARCH_ENDPOINT`: ElasticSearch cluster endpoint
- `SES_FROM_EMAIL`: Verified sender email for SES
- `AWS_REGION`: AWS region

## Features

- Processes restaurant requests from SQS
- Searches ElasticSearch for matching restaurants
- Sends email recommendations via SES

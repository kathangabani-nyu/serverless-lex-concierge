# Lambda Functions

This directory contains all AWS Lambda functions for the Dining Concierge application.

## Functions Overview

### LF0 - Chat API Lambda (`chat-api/`)
- **Purpose**: Handles chat requests from the frontend
- **Integration**: Connects to Amazon Lex chatbot
- **Input**: User messages from API Gateway
- **Output**: Bot responses

### LF1 - Lex Code Hook Lambda (`lex-hook/`)
- **Purpose**: Processes Lex bot intents and manages conversation flow
- **Integration**: Amazon Lex code hook
- **Features**: Parameter validation, SQS message publishing, response formatting

### Data Processor Lambda (`data-processor/`)
- **Purpose**: Processes restaurant data from SQS queue
- **Integration**: DynamoDB, ElasticSearch, SES (for email notifications)
- **Features**: Restaurant recommendation logic, email sending

## Deployment

Each Lambda function can be deployed individually using AWS CLI or Serverless Framework.

## Environment Variables

- `LEX_BOT_NAME`: Name of the Lex bot
- `LEX_BOT_ALIAS`: Bot alias
- `SQS_QUEUE_URL`: URL of the SQS queue
- `DYNAMODB_TABLE`: DynamoDB table name
- `ELASTICSEARCH_ENDPOINT`: ElasticSearch cluster endpoint

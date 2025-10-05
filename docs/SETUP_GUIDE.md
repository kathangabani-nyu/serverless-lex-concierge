# Dining Concierge - Complete Setup Guide

This guide will walk you through setting up the complete Dining Concierge application from scratch.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Python 3.9+** installed
3. **Node.js 16+** and npm installed
4. **Git** installed
5. **Yelp API Key** (get from https://www.yelp.com/developers)

## Step 1: Environment Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd serverless-lex-concierge
```

2. Copy environment template:
```bash
cp env.example .env
```

3. Edit `.env` with your values:
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Yelp API
YELP_API_KEY=your_yelp_api_key_here

# Lambda Function Names
LEX_BOT_NAME=DiningConciergeBot
LEX_BOT_ALIAS=PROD

# DynamoDB
DYNAMODB_TABLE=yelp-restaurants

# ElasticSearch
ELASTICSEARCH_ENDPOINT=https://your-es-domain.us-east-1.es.amazonaws.com

# SQS
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/your-account-id/restaurant-requests

# SES
SES_FROM_EMAIL=your-verified-email@example.com

# S3
S3_BUCKET_NAME=your-frontend-bucket-name

# API Gateway
API_GATEWAY_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
```

## Step 2: Install Dependencies

1. Install Python dependencies:
```bash
pip install boto3 requests python-dotenv
```

2. Install Node.js dependencies for frontend:
```bash
cd frontend
npm install
cd ..
```

## Step 3: Set Up AWS Infrastructure

1. Run the infrastructure setup script:
```bash
python other-scripts/deployment/infrastructure_setup.py
```

This will create:
- SQS queue with Dead Letter Queue
- SES configuration
- Lex bot with 3 intents
- DynamoDB table
- ElasticSearch domain

2. **Important**: Verify your email address in SES console after running the script.

## Step 4: Collect Restaurant Data

1. Run the Yelp scraper:
```bash
python other-scripts/yelp-scraper/yelp_scraper.py
```

This will:
- Collect 1000+ Manhattan restaurants across 15+ cuisines
- Store data in DynamoDB
- Generate a summary report

2. Set up ElasticSearch index:
```bash
python other-scripts/yelp-scraper/elasticsearch_setup.py
```

## Step 5: Deploy Lambda Functions

1. Run the deployment script:
```bash
python other-scripts/deployment/deploy.py
```

This will:
- Package and deploy all Lambda functions
- Create API Gateway with CORS
- Set up EventBridge triggers
- Deploy frontend to S3

## Step 6: Build and Deploy Frontend

1. Build the React application:
```bash
cd frontend
npm run build
cd ..
```

2. Update the API Gateway URL in your `.env` file with the URL from deployment.

3. Redeploy frontend:
```bash
python other-scripts/deployment/deploy.py
```

## Step 7: Test the Application

1. **Test the API directly**:
```bash
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "sessionId": "test-session"}'
```

2. **Test the complete flow**:
   - Open the frontend URL
   - Start a conversation with the bot
   - Provide all required information (location, cuisine, time, people, email)
   - Check your email for recommendations

## Step 8: Monitor and Troubleshoot

1. **Check CloudWatch Logs** for each Lambda function
2. **Monitor SQS queue** for message processing
3. **Check SES** for email delivery status
4. **Verify DynamoDB** has restaurant data
5. **Test ElasticSearch** queries

## Architecture Overview

```
User → Frontend (S3) → API Gateway → Chat API Lambda → Lex Bot → Lex Hook Lambda → SQS Queue
                                                                                    ↓
Email ← SES ← Suggestions Worker Lambda ← EventBridge (every minute) ← DynamoDB + ElasticSearch
```

## Components

### Lambda Functions
- **LF0 (chat-api)**: Handles API requests and integrates with Lex
- **LF1 (lex-hook)**: Lex code hook for intent processing
- **LF2 (suggestions-worker)**: Processes SQS messages and sends emails

### Data Storage
- **DynamoDB**: Stores complete restaurant information
- **ElasticSearch**: Stores restaurant IDs and cuisines for fast search

### AWS Services
- **SQS**: Queue for restaurant requests with DLQ
- **SES**: Email service for recommendations
- **Lex**: Conversational AI bot
- **API Gateway**: REST API with CORS
- **EventBridge**: Triggers suggestions worker every minute

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure API Gateway has proper CORS configuration
2. **Lex Bot Not Responding**: Check bot is built and published
3. **Email Not Sending**: Verify SES email address
4. **No Restaurant Data**: Run Yelp scraper and ElasticSearch setup
5. **Lambda Timeout**: Increase timeout in Lambda configuration

### Debugging Steps

1. Check CloudWatch Logs for each component
2. Verify environment variables are set correctly
3. Test each component individually
4. Check AWS service limits and permissions

## Cleanup

To remove all resources:
```bash
python other-scripts/cleanup/cleanup.py
```

## Extra Credit: Dead Letter Queue

The DLQ is automatically configured with:
- Max receive count: 3
- 14-day retention
- Automatic error logging

To test DLQ functionality:
1. Use an invalid email address
2. Monitor SQS console for message movement
3. Check CloudWatch Logs for error details

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review CloudWatch Logs
3. Verify all environment variables
4. Ensure all AWS services are properly configured

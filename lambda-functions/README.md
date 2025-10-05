# Lambda Functions

AWS Lambda functions that power the Dining Concierge application's serverless backend.

## Overview

The application consists of three main Lambda functions that work together to provide a complete restaurant recommendation service:

- **LF0 (chat-api)**: Handles API requests and integrates with Amazon Lex
- **LF1 (lex-hook)**: Lex code hook for intent processing and SQS integration  
- **LF2 (suggestions-worker)**: Processes SQS messages and sends email recommendations

## Architecture

```
API Gateway → LF0 (chat-api) → Lex Bot → LF1 (lex-hook) → SQS Queue
                                                              ↓
Email ← SES ← LF2 (suggestions-worker) ← EventBridge ← DynamoDB + ElasticSearch
```

## Lambda Functions

### LF0: Chat API (`chat-api/`)

**Purpose**: Handles incoming API requests and integrates with Amazon Lex bot.

**Key Features**:
- Receives POST requests from frontend
- Integrates with Amazon Lex runtime
- Handles CORS for web requests
- Error handling and logging
- Session management

**Environment Variables**:
- `AWS_REGION`: AWS region
- `LEX_BOT_NAME`: Name of the Lex bot
- `LEX_BOT_ALIAS`: Bot alias (e.g., PROD)

**Dependencies**:
- `boto3`: AWS SDK
- `json`: JSON handling

### LF1: Lex Hook (`lex-hook/`)

**Purpose**: Serves as a code hook for Amazon Lex bot to process intents and manage conversation flow.

**Key Features**:
- Handles 3 intents: GreetingIntent, ThankYouIntent, DiningSuggestionsIntent
- Slot elicitation for restaurant preferences
- SQS integration for request queuing
- Session attribute management
- Error handling

**Intents Handled**:
1. **GreetingIntent**: Responds to user greetings
2. **ThankYouIntent**: Handles expressions of gratitude
3. **DiningSuggestionsIntent**: Collects restaurant preferences and queues requests

**Environment Variables**:
- `AWS_REGION`: AWS region
- `SQS_QUEUE_URL`: URL of the SQS queue

**Dependencies**:
- `boto3`: AWS SDK
- `json`: JSON handling

### LF2: Suggestions Worker (`suggestions-worker/`)

**Purpose**: Processes restaurant requests from SQS queue and sends email recommendations.

**Key Features**:
- Polls SQS queue for restaurant requests
- Searches ElasticSearch for restaurant IDs
- Retrieves detailed restaurant data from DynamoDB
- Sends personalized email recommendations via SES
- Error handling with DLQ integration
- Batch processing for efficiency

**Environment Variables**:
- `AWS_REGION`: AWS region
- `DYNAMODB_TABLE`: DynamoDB table name
- `ELASTICSEARCH_ENDPOINT`: ElasticSearch domain endpoint
- `SES_FROM_EMAIL`: Verified SES email address

**Dependencies**:
- `boto3`: AWS SDK
- `requests`: HTTP requests for ElasticSearch
- `json`: JSON handling

## Data Flow

### 1. User Interaction Flow
```
User → Frontend → API Gateway → LF0 → Lex Bot → LF1 → SQS Queue
```

### 2. Recommendation Processing Flow
```
SQS Queue → LF2 → ElasticSearch → DynamoDB → SES → User Email
```

## Deployment

### Prerequisites
- AWS CLI configured
- Python 3.9+ runtime
- Required AWS permissions

### Manual Deployment

1. **Package Lambda Functions**
   ```bash
   # For each Lambda function
   cd lambda-functions/chat-api
   zip -r chat-api.zip .
   ```

2. **Deploy via AWS CLI**
   ```bash
   aws lambda create-function \
     --function-name chat-api \
     --runtime python3.9 \
     --role arn:aws:iam::ACCOUNT:role/lambda-execution-role \
     --handler lambda_function.lambda_handler \
     --zip-file fileb://chat-api.zip
   ```

### Automated Deployment

Use the deployment script:
```bash
python other-scripts/deployment/deploy.py
```

## Configuration

### IAM Permissions

Each Lambda function requires specific IAM permissions:

**LF0 (chat-api)**:
- `lex:PostText`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

**LF1 (lex-hook)**:
- `sqs:SendMessage`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

**LF2 (suggestions-worker)**:
- `sqs:ReceiveMessage`
- `sqs:DeleteMessage`
- `dynamodb:GetItem`
- `dynamodb:BatchGetItem`
- `ses:SendEmail`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

### Environment Variables

Set environment variables for each function:
```bash
aws lambda update-function-configuration \
  --function-name chat-api \
  --environment Variables='{
    "AWS_REGION":"us-east-1",
    "LEX_BOT_NAME":"DiningConciergeBot",
    "LEX_BOT_ALIAS":"PROD"
  }'
```

## Monitoring

### CloudWatch Logs

Each Lambda function automatically creates CloudWatch log groups:
- `/aws/lambda/chat-api`
- `/aws/lambda/lex-hook`
- `/aws/lambda/suggestions-worker`

### Metrics

Monitor key metrics:
- **Invocations**: Number of function calls
- **Duration**: Execution time
- **Errors**: Error count and rate
- **Throttles**: Concurrent execution limits

### Alarms

Set up CloudWatch alarms for:
- High error rates
- Long execution times
- Function failures

## Testing

### Unit Testing

Test individual functions:
```python
import json
from lambda_function import lambda_handler

# Test event
event = {
    'body': json.dumps({
        'message': 'Hello',
        'sessionId': 'test-session'
    })
}

# Test context
context = type('Context', (), {
    'aws_request_id': 'test-request-id',
    'function_name': 'test-function'
})()

# Invoke function
result = lambda_handler(event, context)
print(result)
```

### Integration Testing

Test complete flow:
1. Send message via API Gateway
2. Verify Lex bot response
3. Check SQS queue for messages
4. Monitor email delivery

## Error Handling

### Common Errors

1. **Lex Bot Not Found**
   - Verify bot name and alias
   - Check bot is built and published

2. **SQS Permission Denied**
   - Verify IAM permissions
   - Check queue URL

3. **DynamoDB Access Denied**
   - Verify table permissions
   - Check table name

4. **SES Email Not Sent**
   - Verify email address
   - Check SES sandbox mode

### Dead Letter Queue (DLQ)

The suggestions worker integrates with SQS DLQ:
- Failed messages retry up to 3 times
- After max retries, messages move to DLQ
- DLQ messages are logged for debugging

## Performance Optimization

### Cold Start Mitigation
- Use provisioned concurrency for critical functions
- Optimize package size
- Use connection pooling

### Memory and Timeout
- **LF0**: 256MB, 30s timeout
- **LF1**: 256MB, 30s timeout  
- **LF2**: 512MB, 300s timeout

### Batch Processing
- Process multiple SQS messages per invocation
- Use batch operations for DynamoDB
- Implement exponential backoff

## Security

### Best Practices
- Use IAM roles with minimal permissions
- Encrypt sensitive environment variables
- Enable VPC if required
- Use AWS Secrets Manager for API keys

### Network Security
- Configure VPC endpoints if needed
- Use security groups appropriately
- Enable CloudTrail logging

## Troubleshooting

### Debug Steps
1. Check CloudWatch Logs for errors
2. Verify environment variables
3. Test IAM permissions
4. Check AWS service limits
5. Validate input data format

### Common Issues

**Function Timeout**:
- Increase timeout setting
- Optimize code performance
- Check external API response times

**Memory Issues**:
- Increase memory allocation
- Optimize data processing
- Use streaming for large datasets

**Permission Errors**:
- Verify IAM role permissions
- Check resource ARNs
- Validate AWS credentials

## Maintenance

### Regular Tasks
- Monitor CloudWatch metrics
- Review error logs
- Update dependencies
- Test disaster recovery procedures

### Updates
- Update Lambda runtime versions
- Apply security patches
- Optimize performance
- Add new features

## License

This project is for educational purposes as part of CS-GY 9223 Fall 2025.
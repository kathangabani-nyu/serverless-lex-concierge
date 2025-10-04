# Lex Code Hook Lambda (LF1)

Handles Amazon Lex bot intents and manages conversation flow.

## Function Details

- **Runtime**: Python 3.9
- **Timeout**: 30 seconds
- **Memory**: 256 MB
- **Trigger**: Amazon Lex (Code Hook)

## Dependencies

```python
boto3>=1.26.0
```

## Environment Variables

- `SQS_QUEUE_URL`: URL of the SQS queue for restaurant requests
- `AWS_REGION`: AWS region

## Intents Handled

- **GreetingIntent**: Responds with welcome message
- **ThankYouIntent**: Acknowledges user thanks
- **DiningSuggestionsIntent**: Collects restaurant preferences and sends to SQS

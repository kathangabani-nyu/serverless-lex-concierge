# Chat API Lambda (LF0)

Handles chat requests from the frontend and integrates with Amazon Lex.

## Function Details

- **Runtime**: Python 3.9
- **Timeout**: 30 seconds
- **Memory**: 256 MB
- **Trigger**: API Gateway

## Dependencies

```python
boto3>=1.26.0
```

## Environment Variables

- `LEX_BOT_NAME`: Name of the Lex bot
- `LEX_BOT_ALIAS`: Bot alias (e.g., "PROD")
- `AWS_REGION`: AWS region

## API Integration

This function receives requests from API Gateway and forwards them to Lex, then returns the bot's response.

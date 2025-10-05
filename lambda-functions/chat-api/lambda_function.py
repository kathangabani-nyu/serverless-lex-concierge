import json
import boto3
import os
from botocore.exceptions import ClientError
import uuid
from datetime import datetime

def lambda_handler(event, context):
    """
    Lambda function to handle chat requests according to the Swagger specification.
    
    Args:
        event: API Gateway event containing user message
        context: Lambda context object
        
    Returns:
        API Gateway response with bot message following Swagger spec
    """
    
    # Initialize Lex client
    lex_client = boto3.client('lex-runtime', region_name=os.environ['AWS_REGION'])
    
    try:
        # Parse the incoming request according to Swagger spec
        body = json.loads(event['body'])
        messages = body.get('messages', [])
        
        if not messages:
            return create_error_response(400, 'No messages provided')
        
        # Get the latest message
        latest_message = messages[-1]
        if latest_message.get('type') != 'unstructured':
            return create_error_response(400, 'Only unstructured messages supported')
        
        user_text = latest_message.get('unstructured', {}).get('text', '')
        if not user_text:
            return create_error_response(400, 'No text in message')
        
        # For now, implement boilerplate response as required
        # TODO: Later integrate with Lex bot
        bot_message = "I'm still under development. Please come back later."
        
        # Create response according to Swagger specification
        response_message = {
            'type': 'unstructured',
            'unstructured': {
                'id': str(uuid.uuid4()),
                'text': bot_message,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }
        
        # Return API Gateway response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'messages': [response_message]
            })
        }
        
    except ClientError as e:
        print(f"Error calling Lex: {e}")
        return create_error_response(500, 'Sorry, I encountered an error. Please try again.')
    except Exception as e:
        print(f"Unexpected error: {e}")
        return create_error_response(500, 'I\'m still under development. Please come back later.')

def create_error_response(status_code, message):
    """Create standardized error response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps({
            'code': status_code,
            'message': message
        })
    }

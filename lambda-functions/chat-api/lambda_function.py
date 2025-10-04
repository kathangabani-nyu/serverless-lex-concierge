import json
import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to handle chat requests and integrate with Amazon Lex.
    
    Args:
        event: API Gateway event containing user message
        context: Lambda context object
        
    Returns:
        API Gateway response with bot message
    """
    
    # Initialize Lex client
    lex_client = boto3.client('lex-runtime', region_name=os.environ['AWS_REGION'])
    
    try:
        # Parse the incoming request
        body = json.loads(event['body'])
        user_message = body.get('message', '')
        session_id = body.get('sessionId', 'default-session')
        
        # Prepare Lex request
        lex_response = lex_client.post_text(
            botName=os.environ['LEX_BOT_NAME'],
            botAlias=os.environ['LEX_BOT_ALIAS'],
            userId=session_id,
            inputText=user_message
        )
        
        # Extract bot response
        bot_message = lex_response.get('message', 'I\'m still under development. Please come back later.')
        
        # Return API Gateway response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'message': bot_message,
                'sessionId': session_id
            })
        }
        
    except ClientError as e:
        print(f"Error calling Lex: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Sorry, I encountered an error. Please try again.',
                'sessionId': session_id
            })
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'I\'m still under development. Please come back later.',
                'sessionId': 'default-session'
            })
        }

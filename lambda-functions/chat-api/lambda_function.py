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
    
    # Initialize Lex V2 client
    lex_client = boto3.client('lexv2-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    
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
        
        # Call Lex bot to process the user message
        bot_message = call_lex_bot(lex_client, user_text)
        
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

def call_lex_bot(lex_client, user_text):
    """
    Call Lex bot to process user message and return bot response.
    
    Args:
        lex_client: Boto3 Lex runtime client
        user_text: User's message text
        
    Returns:
        Bot response message
    """
    try:
        # Get bot configuration from environment variables
        bot_id = os.environ.get('LEX_BOT_ID', 'VDWYJZ7VIA')
        alias_id = os.environ.get('LEX_BOT_ALIAS_ID', '78VURXTWPO')
        
        print(f"Using bot ID: {bot_id}, alias ID: {alias_id}")
        
        # Use a consistent session ID to maintain conversation context
        # Extract sessionId from request body if provided, otherwise use IP-based session
        body_data = json.loads(event['body'])
        user_id = body_data.get('sessionId') or event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'default-session')
        
        # Call Lex V2 bot using actual IDs
        response = lex_client.recognize_text(
            botId=bot_id,
            botAliasId=alias_id,
            localeId='en_US',
            sessionId=user_id,
            text=user_text
        )
        
        # Extract bot message from Lex V2 response
        messages = response.get('messages', [])
        if messages:
            bot_message = messages[0].get('content', 'Sorry, I didn\'t understand that.')
        else:
            bot_message = 'Sorry, I didn\'t understand that.'
        
        # Check if we have a fulfilled intent (DiningSuggestionsIntent)
        session_state = response.get('sessionState', {})
        intent = session_state.get('intent', {})
        
        if intent.get('state') == 'Fulfilled':
            intent_name = intent.get('name', '')
            slots = intent.get('slots', {})
            
            if intent_name == 'DiningSuggestionsIntent':
                # Send to SQS for processing
                send_to_sqs(slots)
                bot_message = f"Perfect! I have your preferences: {slots.get('Cuisine', {}).get('value', {}).get('originalValue', '')} cuisine in {slots.get('Location', {}).get('value', {}).get('originalValue', '')} for {slots.get('NumberOfPeople', {}).get('value', {}).get('originalValue', '')} people at {slots.get('DiningTime', {}).get('value', {}).get('originalValue', '')}. I'll send my recommendations to {slots.get('Email', {}).get('value', {}).get('originalValue', '')}. Let me search for the best options!"
        
        return bot_message
        
    except ClientError as e:
        print(f"Error calling Lex: {e}")
        return "Sorry, I encountered an error. Please try again."
    except Exception as e:
        print(f"Unexpected error calling Lex: {e}")
        return "I'm still under development. Please come back later."

def send_to_sqs(slots):
    """
    Send restaurant request to SQS queue for processing.
    
    Args:
        slots: Dictionary containing user preferences from Lex
    """
    try:
        sqs_client = boto3.client('sqs')
        queue_url = os.environ.get('SQS_QUEUE_URL')
        
        if not queue_url:
            print("SQS_QUEUE_URL not configured")
            return
        
        # Create message payload (extract values from Lex V2 slot format)
        def extract_slot_value(slot):
            """Extract value from Lex V2 slot format."""
            if not slot:
                return ''
            return slot.get('value', {}).get('originalValue', '')
        
        message_body = {
            'cuisine': extract_slot_value(slots.get('Cuisine')),
            'location': extract_slot_value(slots.get('Location')),
            'number_of_people': extract_slot_value(slots.get('NumberOfPeople')),
            'dining_time': extract_slot_value(slots.get('DiningTime')),
            'email': extract_slot_value(slots.get('Email')),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send message to SQS
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body)
        )
        
        print(f"Message sent to SQS: {message_body}")
        
    except ClientError as e:
        print(f"Error sending to SQS: {e}")
    except Exception as e:
        print(f"Unexpected error sending to SQS: {e}")

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

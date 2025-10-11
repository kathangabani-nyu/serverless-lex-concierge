#!/usr/bin/env python3
"""
Lambda function to handle Lex bot code hook for intent responses.
"""

import json
import boto3
import os
from decimal import Decimal

def lambda_handler(event, context):
    """
    Lambda function to handle Lex bot code hook.
    This function is called before Lex responds to any intent.
    """
    
    print(f"Lex Code Hook Event: {json.dumps(event, indent=2)}")
    
    try:
        # Extract intent information
        intent_name = event.get('sessionState', {}).get('intent', {}).get('name', '')
        slots = event.get('sessionState', {}).get('intent', {}).get('slots', {})
        session_attributes = event.get('sessionState', {}).get('sessionAttributes', {})
        
        print(f"Intent: {intent_name}")
        print(f"Slots: {slots}")
        
        # Handle different intents
        if intent_name == 'GreetingIntent':
            response_message = "Hi there! I'm your personal dining concierge. How can I help you today?"
            
        elif intent_name == 'ThankYouIntent':
            response_message = "You're welcome! I'm here to help you find great restaurants. Is there anything else I can assist you with?"
            
        elif intent_name == 'DiningSuggestionsIntent':
            # Check if all slots are filled
            required_slots = ['Location', 'Cuisine', 'DiningTime', 'NumberOfPeople', 'Email']
            missing_slots = []
            
            for slot_name in required_slots:
                slot_value = slots.get(slot_name)
                if not slot_value or slot_value is None or not slot_value.get('value'):
                    missing_slots.append(slot_name)
            
            if missing_slots:
                # Still collecting slots - let Lex handle the prompts
                return {
                    'sessionState': {
                        'dialogAction': {
                            'type': 'Delegate'
                        },
                        'intent': {
                            'name': intent_name,
                            'slots': slots
                        }
                    }
                }
            else:
                # All slots collected - send to SQS and confirm
                try:
                    # Send to SQS queue
                    sqs_client = boto3.client('sqs', region_name='us-east-1')
                    queue_url = os.environ.get('SQS_QUEUE_URL', '')
                    
                    if queue_url:
                        message_body = {
                            'location': slots['Location']['value']['interpretedValue'],
                            'cuisine': slots['Cuisine']['value']['interpretedValue'],
                            'dining_time': slots['DiningTime']['value']['interpretedValue'],
                            'number_of_people': slots['NumberOfPeople']['value']['interpretedValue'],
                            'email': slots['Email']['value']['interpretedValue']
                        }
                        
                        sqs_client.send_message(
                            QueueUrl=queue_url,
                            MessageBody=json.dumps(message_body)
                        )
                        
                        print(f"Sent to SQS: {message_body}")
                        
                        response_message = f"Perfect! I've received your request for {slots['Cuisine']['value']['interpretedValue']} restaurants in {slots['Location']['value']['interpretedValue']} for {slots['NumberOfPeople']['value']['interpretedValue']} people at {slots['DiningTime']['value']['interpretedValue']}. I'll send the recommendations to {slots['Email']['value']['interpretedValue']} shortly. Have a great day!"
                    else:
                        response_message = "I've received your request! I'll send restaurant recommendations to your email shortly. Have a great day!"
                        
                except Exception as e:
                    print(f"Error sending to SQS: {e}")
                    response_message = "I've received your request! I'll send restaurant recommendations to your email shortly. Have a great day!"
                
                # Clear the intent slots for next conversation
                return {
                    'sessionState': {
                        'dialogAction': {
                            'type': 'Close',
                            'fulfillmentState': 'Fulfilled'
                        },
                        'intent': {
                            'name': intent_name,
                            'state': 'Fulfilled',
                            'slots': {}
                        }
                    },
                    'messages': [
                        {
                            'contentType': 'PlainText',
                            'content': response_message
                        }
                    ]
                }
        
        else:
            # Unknown intent
            response_message = "I'm not sure how to help with that. I can assist you with restaurant recommendations. Would you like to find a place to dine?"
        
        # Return response for GreetingIntent and ThankYouIntent
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close',
                    'fulfillmentState': 'Fulfilled'
                },
                'intent': {
                    'name': intent_name,
                    'state': 'Fulfilled',
                    'slots': slots
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': response_message
                }
            ]
        }
        
    except Exception as e:
        print(f"Error in Lambda code hook: {e}")
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close',
                    'fulfillmentState': 'Failed'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': "I'm sorry, I encountered an error. Please try again."
                }
            ]
        }

import json
import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to handle Amazon Lex bot intents.
    
    Args:
        event: Lex event containing intent information
        context: Lambda context object
        
    Returns:
        Lex response with bot message and session attributes
    """
    
    # Initialize SQS client
    sqs_client = boto3.client('sqs', region_name=os.environ['AWS_REGION'])
    
    try:
        # Extract intent information
        intent_name = event['currentIntent']['name']
        slots = event['currentIntent']['slots']
        session_attributes = event.get('sessionAttributes', {})
        
        if intent_name == 'GreetingIntent':
            return {
                'sessionAttributes': session_attributes,
                'dialogAction': {
                    'type': 'Close',
                    'fulfillmentState': 'Fulfilled',
                    'message': {
                        'contentType': 'PlainText',
                        'content': 'Hi there! I\'m your dining concierge. I can help you find great restaurants in Manhattan. What kind of cuisine are you in the mood for?'
                    }
                }
            }
            
        elif intent_name == 'ThankYouIntent':
            return {
                'sessionAttributes': session_attributes,
                'dialogAction': {
                    'type': 'Close',
                    'fulfillmentState': 'Fulfilled',
                    'message': {
                        'contentType': 'PlainText',
                        'content': 'You\'re welcome! I\'m here to help whenever you need restaurant recommendations. Have a great meal!'
                    }
                }
            }
            
        elif intent_name == 'DiningSuggestionsIntent':
            # Check if all required slots are filled
            required_slots = ['Location', 'Cuisine', 'DiningTime', 'NumberOfPeople', 'Email']
            missing_slots = [slot for slot in required_slots if not slots.get(slot)]
            
            if missing_slots:
                # Return slot elicitation
                slot_to_elicit = missing_slots[0]
                return {
                    'sessionAttributes': session_attributes,
                    'dialogAction': {
                        'type': 'ElicitSlot',
                        'intentName': intent_name,
                        'slots': slots,
                        'slotToElicit': slot_to_elicit,
                        'message': {
                            'contentType': 'PlainText',
                            'content': get_slot_elicitation_message(slot_to_elicit)
                        }
                    }
                }
            else:
                # All slots filled, send to SQS and confirm
                message_body = {
                    'location': slots['Location'],
                    'cuisine': slots['Cuisine'],
                    'dining_time': slots['DiningTime'],
                    'number_of_people': slots['NumberOfPeople'],
                    'email': slots['Email']
                }
                
                # Send message to SQS
                sqs_client.send_message(
                    QueueUrl=os.environ['SQS_QUEUE_URL'],
                    MessageBody=json.dumps(message_body)
                )
                
                return {
                    'sessionAttributes': session_attributes,
                    'dialogAction': {
                        'type': 'Close',
                        'fulfillmentState': 'Fulfilled',
                        'message': {
                            'contentType': 'PlainText',
                            'content': f'Perfect! I\'ve received your request for {slots["Cuisine"]} restaurants in {slots["Location"]} for {slots["NumberOfPeople"]} people at {slots["DiningTime"]}. I\'ll send you personalized recommendations via email shortly!'
                        }
                    }
                }
        
        else:
            # Unknown intent
            return {
                'sessionAttributes': session_attributes,
                'dialogAction': {
                    'type': 'Close',
                    'fulfillmentState': 'Fulfilled',
                    'message': {
                        'contentType': 'PlainText',
                        'content': 'I\'m still learning! Could you please tell me what kind of restaurant you\'re looking for?'
                    }
                }
            }
            
    except ClientError as e:
        print(f"Error processing intent: {e}")
        return {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close',
                'fulfillmentState': 'Failed',
                'message': {
                    'contentType': 'PlainText',
                    'content': 'Sorry, I encountered an error. Please try again.'
                }
            }
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close',
                'fulfillmentState': 'Failed',
                'message': {
                    'contentType': 'PlainText',
                    'content': 'I\'m still under development. Please come back later.'
                }
            }
        }

def get_slot_elicitation_message(slot_name):
    """Generate appropriate message for slot elicitation."""
    messages = {
        'Location': 'Where would you like to dine? (e.g., Manhattan, Midtown, Upper East Side)',
        'Cuisine': 'What type of cuisine are you in the mood for? (e.g., Italian, Chinese, Mexican, Japanese, Indian)',
        'DiningTime': 'What time would you like to dine? (e.g., 7:00 PM, 8:30 PM)',
        'NumberOfPeople': 'How many people will be dining? (e.g., 2, 4, 6)',
        'Email': 'What\'s your email address so I can send you the recommendations?'
    }
    return messages.get(slot_name, f'Please provide {slot_name.lower()}.')

import json
import boto3
import os
import random
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to process restaurant requests from SQS queue or EventBridge.
    
    Args:
        event: SQS event or EventBridge event
        context: Lambda context object
        
    Returns:
        Processing status
    """
    
    # Initialize AWS clients
    region = os.environ.get('AWS_REGION', 'us-east-1')
    dynamodb = boto3.resource('dynamodb', region_name=region)
    ses_client = boto3.client('ses', region_name=region)
    sqs_client = boto3.client('sqs', region_name=region)
    
    try:
        # Check if this is an SQS event or EventBridge event
        if 'Records' in event:
            # SQS event - process directly
            records = event['Records']
        else:
            # EventBridge event - poll SQS for messages
            queue_url = os.environ.get('SQS_QUEUE_URL', '')
            print(f"EventBridge trigger - polling SQS queue: {queue_url}")
            
            # Receive messages from SQS
            response = sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=1
            )
            
            records = response.get('Messages', [])
            print(f"Received {len(records)} messages from SQS")
            
            if not records:
                print("No messages in SQS queue")
                return {
                    'statusCode': 200,
                    'body': json.dumps('No messages to process')
                }
        
        # Process each record
        for record in records:
            # Parse the message body
            if 'body' in record:
                # SQS record
                message_body = json.loads(record['body'])
            else:
                # Direct EventBridge message
                message_body = record
            
            location = message_body['location']
            cuisine = message_body['cuisine']
            dining_time = message_body['dining_time']
            number_of_people = message_body['number_of_people']
            email = message_body['email']
            
            print(f"Processing request: {cuisine} in {location} for {number_of_people} people")
            
            # Search for restaurants in DynamoDB
            restaurants = search_restaurants(cuisine, location)
            
            # Get detailed restaurant information from DynamoDB
            detailed_restaurants = get_restaurant_details(restaurants, dynamodb)
            
            # Send email with recommendations
            send_recommendation_email(
                email, 
                detailed_restaurants, 
                cuisine, 
                location, 
                dining_time, 
                number_of_people,
                ses_client
            )
            
            # Delete message from SQS if it was received from queue
            if 'ReceiptHandle' in record:
                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=record['ReceiptHandle']
                )
                print(f"Deleted message from SQS queue")
            
        return {
            'statusCode': 200,
            'body': json.dumps('Restaurant recommendations sent successfully')
        }
        
    except Exception as e:
        print(f"Error processing restaurant request: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

def search_restaurants(cuisine, location):
    """Search for restaurants in DynamoDB using GSI."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'yelp-restaurants'))
    
    try:
        # Search using GSI on cuisine
        response = table.query(
            IndexName='cuisine-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('cuisine').eq(cuisine.lower()),
            Limit=10
        )
        
        restaurants = response.get('Items', [])
        
        if restaurants:
            # Randomly select 3 restaurants
            selected = random.sample(restaurants, min(3, len(restaurants)))
            return [restaurant['business_id'] for restaurant in selected]
        else:
            print(f"No restaurants found for cuisine: {cuisine}")
            return []
            
    except Exception as e:
        print(f"Error searching DynamoDB: {e}")
        return []

def get_restaurant_details(restaurant_ids, dynamodb):
    """Get detailed restaurant information from DynamoDB."""
    table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'yelp-restaurants'))
    restaurants = []
    
    for restaurant_id in restaurant_ids:
        try:
            response = table.get_item(Key={'business_id': restaurant_id})
            if 'Item' in response:
                restaurants.append(response['Item'])
        except ClientError as e:
            print(f"Error getting restaurant {restaurant_id}: {e}")
    
    return restaurants

def send_recommendation_email(email, restaurants, cuisine, location, dining_time, number_of_people, ses_client):
    """Send restaurant recommendations via SES."""
    
    # Create email content
    subject = f"Your {cuisine} Restaurant Recommendations for {location}"
    
    body_text = f"""
Hello!

Here are your personalized restaurant recommendations:

Cuisine: {cuisine}
Location: {location}
Dining Time: {dining_time}
Party Size: {number_of_people}

Restaurant Recommendations:
"""
    
    for i, restaurant in enumerate(restaurants[:5], 1):
        body_text += f"""
{i}. {restaurant.get('name', 'N/A')}
   Address: {restaurant.get('address', 'N/A')}
   Rating: {restaurant.get('rating', 'N/A')}/5 ({restaurant.get('review_count', 0)} reviews)
   Phone: {restaurant.get('phone', 'N/A')}
"""
    
    body_text += """
Enjoy your meal!

Best regards,
Your Dining Concierge
"""
    
    # Send email
    try:
        ses_client.send_email(
            Source='kdg7224@nyu.edu',  # Verified SES email address
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )
        print(f"Email sent successfully to {email}")
        
    except ClientError as e:
        print(f"Error sending email: {e}")
        raise

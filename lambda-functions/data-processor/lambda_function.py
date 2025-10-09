import json
import boto3
import os
import requests
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to process restaurant requests from SQS queue.
    
    Args:
        event: SQS event containing restaurant request
        context: Lambda context object
        
    Returns:
        Processing status
    """
    
    # Initialize AWS clients
    dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
    ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION'])
    
    try:
        # Process each SQS record
        for record in event['Records']:
            # Parse the message body
            message_body = json.loads(record['body'])
            
            location = message_body['location']
            cuisine = message_body['cuisine']
            dining_time = message_body['dining_time']
            number_of_people = message_body['number_of_people']
            email = message_body['email']
            
            # Search for restaurants in ElasticSearch
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
    """Search for restaurants in ElasticSearch."""
    es_endpoint = os.environ['ELASTICSEARCH_ENDPOINT']
    
    # ElasticSearch query
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"cuisine": cuisine.lower()}}
                ]
            }
        },
        "size": 10
    }
    
    try:
        response = requests.post(
            f"{es_endpoint}/restaurants/_search",
            json=query,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            results = response.json()
            return [hit['_source']['restaurant_id'] for hit in results['hits']['hits']]
        else:
            print(f"ElasticSearch error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error searching ElasticSearch: {e}")
        return []

def get_restaurant_details(restaurant_ids, dynamodb):
    """Get detailed restaurant information from DynamoDB."""
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
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

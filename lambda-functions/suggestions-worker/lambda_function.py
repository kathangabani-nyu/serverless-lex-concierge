import json
import boto3
import os
import requests
from botocore.exceptions import ClientError
import random

def lambda_handler(event, context):
    """
    Lambda function to process restaurant requests from SQS queue (LF2).
    This is the suggestions worker that runs every minute via EventBridge.
    
    Args:
        event: SQS event containing restaurant request
        context: Lambda context object
        
    Returns:
        Processing status
    """
    
    # Initialize AWS clients
    dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
    ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION'])
    sqs_client = boto3.client('sqs', region_name=os.environ['AWS_REGION'])
    
    try:
        # Process each SQS record
        for record in event['Records']:
            try:
                # Parse the message body
                message_body = json.loads(record['body'])
                
                location = message_body['location']
                cuisine = message_body['cuisine']
                dining_time = message_body['dining_time']
                number_of_people = message_body['number_of_people']
                email = message_body['email']
                
                print(f"Processing request for {cuisine} restaurants in {location} for {number_of_people} people")
                
                # Search for restaurants in ElasticSearch
                restaurant_ids = search_restaurants_in_elasticsearch(cuisine)
                
                if not restaurant_ids:
                    print(f"No restaurants found for cuisine: {cuisine}")
                    # Send error email
                    send_error_email(email, cuisine, location, ses_client)
                    continue
                
                # Get detailed restaurant information from DynamoDB
                detailed_restaurants = get_restaurant_details_from_dynamodb(restaurant_ids, dynamodb)
                
                if not detailed_restaurants:
                    print(f"No detailed restaurant data found")
                    send_error_email(email, cuisine, location, ses_client)
                    continue
                
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
                
                print(f"Successfully sent recommendations to {email}")
                
            except Exception as e:
                print(f"Error processing individual record: {e}")
                # Don't delete the message from queue on error - let SQS retry
                # This will eventually move to DLQ after maxReceiveCount
                raise
        
        return {
            'statusCode': 200,
            'body': json.dumps('Restaurant recommendations processed successfully')
        }
        
    except Exception as e:
        print(f"Error processing restaurant request: {e}")
        # Log the failure with requestId for visibility
        print(f"RequestId: {context.aws_request_id}, Error: {str(e)}")
        
        # Re-raise to prevent message deletion (SQS will retry)
        raise

def search_restaurants_in_elasticsearch(cuisine, size=10):
    """
    Search for restaurants by cuisine in ElasticSearch.
    
    Args:
        cuisine (str): Cuisine type to search for
        size (int): Number of results to return
        
    Returns:
        list: List of restaurant IDs
    """
    es_endpoint = os.environ['ELASTICSEARCH_ENDPOINT']
    
    # ElasticSearch query with random sampling
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"cuisine": cuisine.lower()}}
                ]
            }
        },
        "size": size,
        "sort": [
            {"_script": {
                "type": "number",
                "script": {
                    "source": "Math.random()"
                },
                "order": "asc"
            }}
        ]
    }
    
    try:
        response = requests.post(
            f"{es_endpoint}/restaurants/_search",
            json=query,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            results = response.json()
            hits = results['hits']['hits']
            restaurant_ids = [hit['_source']['restaurant_id'] for hit in hits]
            print(f"Found {len(restaurant_ids)} restaurants for {cuisine}")
            return restaurant_ids
        else:
            print(f"ElasticSearch error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"Error searching ElasticSearch: {e}")
        return []

def get_restaurant_details_from_dynamodb(restaurant_ids, dynamodb):
    """
    Get detailed restaurant information from DynamoDB.
    
    Args:
        restaurant_ids (list): List of restaurant IDs
        dynamodb: DynamoDB resource
        
    Returns:
        list: List of detailed restaurant data
    """
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    restaurants = []
    
    # Batch get items (max 100 per request)
    batch_size = 100
    for i in range(0, len(restaurant_ids), batch_size):
        batch_ids = restaurant_ids[i:i + batch_size]
        
        try:
            # Use batch_get_item for efficiency
            response = dynamodb.batch_get_item(
                RequestItems={
                    os.environ['DYNAMODB_TABLE']: {
                        'Keys': [{'business_id': rid} for rid in batch_ids]
                    }
                }
            )
            
            items = response.get('Responses', {}).get(os.environ['DYNAMODB_TABLE'], [])
            restaurants.extend(items)
            
        except ClientError as e:
            print(f"Error batch getting restaurants: {e}")
            # Fallback to individual gets
            for rid in batch_ids:
                try:
                    response = table.get_item(Key={'business_id': rid})
                    if 'Item' in response:
                        restaurants.append(response['Item'])
                except ClientError as e:
                    print(f"Error getting restaurant {rid}: {e}")
    
    print(f"Retrieved {len(restaurants)} detailed restaurant records")
    return restaurants

def send_recommendation_email(email, restaurants, cuisine, location, dining_time, number_of_people, ses_client):
    """
    Send restaurant recommendations via SES.
    
    Args:
        email (str): Recipient email address
        restaurants (list): List of restaurant data
        cuisine (str): Cuisine type
        location (str): Location
        dining_time (str): Dining time
        number_of_people (str): Number of people
        ses_client: SES client
    """
    
    # Limit to top 5 restaurants
    top_restaurants = restaurants[:5]
    
    # Create email content
    subject = f"Your {cuisine} Restaurant Recommendations for {location}"
    
    body_text = f"""Hello!

Here are your personalized restaurant recommendations:

Cuisine: {cuisine}
Location: {location}
Dining Time: {dining_time}
Party Size: {number_of_people}

Restaurant Recommendations:
"""
    
    for i, restaurant in enumerate(top_restaurants, 1):
        name = restaurant.get('name', 'N/A')
        address = restaurant.get('address', 'N/A')
        rating = restaurant.get('rating', 'N/A')
        review_count = restaurant.get('review_count', 0)
        phone = restaurant.get('phone', 'N/A')
        
        body_text += f"""
{i}. {name}
   Address: {address}
   Rating: {rating}/5 ({review_count} reviews)
   Phone: {phone}
"""
    
    body_text += """

Enjoy your meal!

Best regards,
Your Dining Concierge
"""
    
    # Send email
    try:
        ses_client.send_email(
            Source=os.environ['SES_FROM_EMAIL'],
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )
        print(f"Email sent successfully to {email}")
        
    except ClientError as e:
        print(f"Error sending email to {email}: {e}")
        # Re-raise to trigger SQS retry mechanism
        raise

def send_error_email(email, cuisine, location, ses_client):
    """
    Send error email when no restaurants are found.
    
    Args:
        email (str): Recipient email address
        cuisine (str): Cuisine type
        location (str): Location
        ses_client: SES client
    """
    
    subject = f"Restaurant Recommendations - No Results Found"
    
    body_text = f"""Hello!

I apologize, but I couldn't find any {cuisine} restaurants in {location} at this time.

This might be because:
- The cuisine type might not be available in that area
- Our database might need updating
- There might be a temporary issue with our search system

Please try again with a different cuisine type or location, or contact our support team.

Best regards,
Your Dining Concierge
"""
    
    try:
        ses_client.send_email(
            Source=os.environ['SES_FROM_EMAIL'],
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )
        print(f"Error email sent to {email}")
        
    except ClientError as e:
        print(f"Error sending error email to {email}: {e}")
        raise

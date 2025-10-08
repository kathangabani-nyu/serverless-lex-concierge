
import json
import boto3
import random
from botocore.exceptions import ClientError
from decimal import Decimal

def convert_decimals(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    else:
        return obj

def lambda_handler(event, context):
    """
    Lambda function to search restaurants by cuisine.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-restaurants')
    
    try:
        # Parse the event
        cuisine = event.get('cuisine', '')
        count = event.get('count', 3)
        
        if not cuisine:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Cuisine parameter required'})
            }
        
        # Search restaurants by cuisine
        response = table.query(
            IndexName='cuisine-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('cuisine').eq(cuisine),
            Limit=count * 3  # Get more to allow for random selection
        )
        
        restaurants = response.get('Items', [])
        
        if not restaurants:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'No restaurants found for cuisine: {cuisine}'})
            }
        
        # Randomly select restaurants
        selected = random.sample(restaurants, min(count, len(restaurants)))
        
        # Convert Decimal objects to float for JSON serialization
        selected_converted = convert_decimals(selected)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'cuisine': cuisine,
                'count': len(selected_converted),
                'restaurants': selected_converted
            })
        }
        
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

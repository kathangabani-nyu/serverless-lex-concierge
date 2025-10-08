import requests
import json
import time
import boto3
from datetime import datetime
import os
from botocore.exceptions import ClientError

class YelpRestaurantScraper:
    def __init__(self, yelp_api_key, aws_region='us-east-1'):
        """
        Initialize the Yelp scraper with API key and AWS configuration.
        
        Args:
            yelp_api_key (str): Yelp API key
            aws_region (str): AWS region for DynamoDB
        """
        self.yelp_api_key = yelp_api_key
        self.aws_region = aws_region
        self.dynamodb = boto3.resource('dynamodb', region_name=aws_region)
        self.table = self.dynamodb.Table('yelp-restaurants')
        
        # Yelp API configuration
        self.base_url = "https://api.yelp.com/v3/businesses/search"
        self.headers = {
            'Authorization': f'Bearer {yelp_api_key}',
            'Content-Type': 'application/json'
        }
        
        # Manhattan neighborhoods for comprehensive coverage
        self.manhattan_neighborhoods = [
            'Financial District', 'Tribeca', 'Chinatown', 'Little Italy', 'SoHo',
            'East Village', 'West Village', 'Greenwich Village', 'Chelsea',
            'Flatiron District', 'Gramercy', 'Stuyvesant Town', 'Lower East Side',
            'Midtown East', 'Midtown West', 'Times Square', 'Hell\'s Kitchen',
            'Upper East Side', 'Upper West Side', 'Morningside Heights',
            'Harlem', 'East Harlem', 'Washington Heights', 'Inwood'
        ]
        
        # Cuisine types to collect (minimum 5 as required)
        self.cuisine_types = [
            'Italian', 'Chinese', 'Japanese', 'Mexican', 'Indian',
            'Thai', 'French', 'American', 'Mediterranean', 'Korean',
            'Vietnamese', 'Spanish', 'Greek', 'Lebanese', 'Ethiopian'
        ]
        
        # Track collected restaurants to avoid duplicates
        self.collected_restaurants = set()
        
    def search_restaurants_by_cuisine(self, cuisine, location='Manhattan, NY', limit=50):
        """
        Search for restaurants by cuisine type in Manhattan.
        
        Args:
            cuisine (str): Type of cuisine
            location (str): Location to search in
            limit (int): Number of results per request (max 50)
            
        Returns:
            list: List of restaurant data
        """
        restaurants = []
        offset = 0
        
        print(f"Searching for {cuisine} restaurants in {location}...")
        
        while len(restaurants) < 200:  # Target 200 per cuisine
            params = {
                'term': f'{cuisine} restaurants',
                'location': location,
                'limit': min(limit, 200 - len(restaurants)),
                'offset': offset,
                'sort_by': 'rating',  # Get highly rated restaurants
                'price': '1,2,3,4'  # Include all price ranges
            }
            
            try:
                response = requests.get(self.base_url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                businesses = data.get('businesses', [])
                
                if not businesses:
                    print(f"No more {cuisine} restaurants found at offset {offset}")
                    break
                
                # Filter and process restaurants
                for business in businesses:
                    if self._is_valid_restaurant(business, cuisine):
                        restaurant_data = self._process_restaurant_data(business, cuisine)
                        if restaurant_data['business_id'] not in self.collected_restaurants:
                            restaurants.append(restaurant_data)
                            self.collected_restaurants.add(restaurant_data['business_id'])
                
                print(f"Found {len(businesses)} {cuisine} restaurants, {len(restaurants)} unique so far")
                
                offset += len(businesses)
                
                # Rate limiting - Yelp allows 500 requests per day
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching {cuisine} restaurants: {e}")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break
        
        print(f"Total unique {cuisine} restaurants collected: {len(restaurants)}")
        return restaurants
    
    def _is_valid_restaurant(self, business, target_cuisine):
        """
        Validate if a business is a valid restaurant for our purposes.
        
        Args:
            business (dict): Business data from Yelp API
            target_cuisine (str): Target cuisine type
            
        Returns:
            bool: True if valid restaurant
        """
        # Check if it's a restaurant
        categories = business.get('categories', [])
        is_restaurant = any(cat['alias'] in ['restaurants', 'food'] for cat in categories)
        
        if not is_restaurant:
            return False
        
        # Check if it matches our target cuisine
        cuisine_match = any(
            target_cuisine.lower() in cat['title'].lower() or 
            target_cuisine.lower() in cat['alias'].lower()
            for cat in categories
        )
        
        # Check if it's in Manhattan
        location = business.get('location', {})
        city = location.get('city', '').lower()
        is_manhattan = 'manhattan' in city or 'new york' in city
        
        # Check if it has required fields
        has_required_fields = all([
            business.get('id'),
            business.get('name'),
            business.get('location', {}).get('address1'),
            business.get('coordinates'),
            business.get('rating'),
            business.get('review_count', 0) > 0
        ])
        
        return cuisine_match and is_manhattan and has_required_fields
    
    def _process_restaurant_data(self, business, cuisine):
        """
        Process and clean restaurant data from Yelp API.
        
        Args:
            business (dict): Raw business data from Yelp
            cuisine (str): Detected cuisine type
            
        Returns:
            dict: Processed restaurant data
        """
        location = business.get('location', {})
        coordinates = business.get('coordinates', {})
        
        return {
            'business_id': business['id'],
            'name': business['name'],
            'address': location.get('address1', ''),
            'city': location.get('city', ''),
            'state': location.get('state', ''),
            'zip_code': location.get('zip_code', ''),
            'latitude': coordinates.get('latitude', 0),
            'longitude': coordinates.get('longitude', 0),
            'rating': business.get('rating', 0),
            'review_count': business.get('review_count', 0),
            'price': business.get('price', ''),
            'phone': business.get('display_phone', ''),
            'url': business.get('url', ''),
            'image_url': business.get('image_url', ''),
            'cuisine': cuisine,
            'categories': [cat['title'] for cat in business.get('categories', [])],
            'is_closed': business.get('is_closed', False),
            'insertedAtTimestamp': datetime.utcnow().isoformat()
        }
    
    def store_restaurants_in_dynamodb(self, restaurants):
        """
        Store restaurant data in DynamoDB table.
        
        Args:
            restaurants (list): List of restaurant data
        """
        print(f"Storing {len(restaurants)} restaurants in DynamoDB...")
        
        # Batch write to DynamoDB (max 25 items per batch)
        batch_size = 25
        for i in range(0, len(restaurants), batch_size):
            batch = restaurants[i:i + batch_size]
            
            try:
                with self.table.batch_writer() as batch_writer:
                    for restaurant in batch:
                        batch_writer.put_item(Item=restaurant)
                
                print(f"Stored batch {i//batch_size + 1}: {len(batch)} restaurants")
                
            except ClientError as e:
                print(f"Error storing batch {i//batch_size + 1}: {e}")
                continue
    
    def create_dynamodb_table(self):
        """
        Create DynamoDB table for storing restaurant data.
        """
        try:
            table = self.dynamodb.create_table(
                TableName='yelp-restaurants',
                KeySchema=[
                    {
                        'AttributeName': 'business_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'business_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'cuisine',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'cuisine-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'cuisine',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            )
            
            print("DynamoDB table 'yelp-restaurants' created successfully")
            
            # Wait for table to be active
            table.wait_until_exists()
            print("Table is now active")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print("Table 'yelp-restaurants' already exists")
            else:
                print(f"Error creating table: {e}")
                raise
    
    def scrape_all_restaurants(self):
        """
        Main method to scrape restaurants for all cuisine types.
        """
        print("Starting comprehensive restaurant data collection...")
        print(f"Target: 200+ restaurants per cuisine across {len(self.cuisine_types)} cuisines")
        
        all_restaurants = []
        
        # Create DynamoDB table if it doesn't exist
        self.create_dynamodb_table()
        
        for cuisine in self.cuisine_types:
            print(f"\n{'='*50}")
            print(f"Processing {cuisine} restaurants...")
            print(f"{'='*50}")
            
            restaurants = self.search_restaurants_by_cuisine(cuisine)
            
            if restaurants:
                # Store in DynamoDB
                self.store_restaurants_in_dynamodb(restaurants)
                all_restaurants.extend(restaurants)
            
            # Add delay between cuisine types to be respectful to API
            time.sleep(1)
        
        print(f"\n{'='*50}")
        print(f"COLLECTION COMPLETE")
        print(f"{'='*50}")
        print(f"Total unique restaurants collected: {len(all_restaurants)}")
        print(f"Total cuisines processed: {len(self.cuisine_types)}")
        print(f"Average restaurants per cuisine: {len(all_restaurants) / len(self.cuisine_types):.1f}")
        
        # Save summary to file
        summary = {
            'total_restaurants': len(all_restaurants),
            'cuisines_processed': len(self.cuisine_types),
            'collection_date': datetime.utcnow().isoformat(),
            'restaurants_by_cuisine': {}
        }
        
        for cuisine in self.cuisine_types:
            count = len([r for r in all_restaurants if r['cuisine'] == cuisine])
            summary['restaurants_by_cuisine'][cuisine] = count
        
        with open('restaurant_collection_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nSummary saved to 'restaurant_collection_summary.json'")
        return all_restaurants

def main():
    """
    Main function to run the scraper.
    """
    # Load environment variables from .env file
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    # Get API key from environment variable
    yelp_api_key = os.getenv('YELP_API_KEY')
    if not yelp_api_key:
        print("Error: YELP_API_KEY environment variable not set")
        print("Please set your Yelp API key in the .env file")
        return
    
    # Initialize scraper
    scraper = YelpRestaurantScraper(yelp_api_key)
    
    # Run the scraping process
    try:
        restaurants = scraper.scrape_all_restaurants()
        print(f"\n✅ Successfully collected {len(restaurants)} restaurants!")
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        raise

if __name__ == "__main__":
    main()

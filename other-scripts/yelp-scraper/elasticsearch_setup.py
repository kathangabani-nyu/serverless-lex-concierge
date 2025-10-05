import boto3
import json
import requests
from datetime import datetime
import os
from botocore.exceptions import ClientError

class ElasticSearchManager:
    def __init__(self, es_endpoint, aws_region='us-east-1'):
        """
        Initialize ElasticSearch manager.
        
        Args:
            es_endpoint (str): ElasticSearch domain endpoint
            aws_region (str): AWS region
        """
        self.es_endpoint = es_endpoint
        self.aws_region = aws_region
        self.dynamodb = boto3.resource('dynamodb', region_name=aws_region)
        self.table = self.dynamodb.Table('yelp-restaurants')
        
    def create_restaurants_index(self):
        """
        Create the restaurants index in ElasticSearch.
        """
        index_name = 'restaurants'
        mapping = {
            "mappings": {
                "properties": {
                    "restaurant_id": {
                        "type": "keyword"
                    },
                    "cuisine": {
                        "type": "keyword"
                    }
                }
            }
        }
        
        try:
            # Check if index exists
            response = requests.head(f"{self.es_endpoint}/{index_name}")
            if response.status_code == 200:
                print(f"Index '{index_name}' already exists")
                return
            
            # Create index
            response = requests.put(
                f"{self.es_endpoint}/{index_name}",
                json=mapping,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"Index '{index_name}' created successfully")
            else:
                print(f"Error creating index: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error creating ElasticSearch index: {e}")
            raise
    
    def populate_elasticsearch_from_dynamodb(self):
        """
        Populate ElasticSearch with restaurant data from DynamoDB.
        Only stores restaurant_id and cuisine as required.
        """
        print("Populating ElasticSearch from DynamoDB...")
        
        try:
            # Scan DynamoDB table
            response = self.table.scan()
            restaurants = response['Items']
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                restaurants.extend(response['Items'])
            
            print(f"Found {len(restaurants)} restaurants in DynamoDB")
            
            # Bulk index to ElasticSearch
            bulk_data = []
            for restaurant in restaurants:
                # Only store restaurant_id and cuisine as required
                doc = {
                    "restaurant_id": restaurant['business_id'],
                    "cuisine": restaurant['cuisine']
                }
                
                bulk_data.append({
                    "index": {
                        "_index": "restaurants",
                        "_type": "Restaurant"
                    }
                })
                bulk_data.append(doc)
            
            # Send bulk request
            if bulk_data:
                bulk_body = '\n'.join([json.dumps(item) for item in bulk_data]) + '\n'
                
                response = requests.post(
                    f"{self.es_endpoint}/_bulk",
                    data=bulk_body,
                    headers={'Content-Type': 'application/x-ndjson'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Successfully indexed {len(restaurants)} restaurants to ElasticSearch")
                    
                    # Check for errors
                    if result.get('errors'):
                        print("Some documents failed to index:")
                        for item in result['items']:
                            if 'error' in item.get('index', {}):
                                print(f"Error: {item['index']['error']}")
                else:
                    print(f"Error bulk indexing: {response.status_code} - {response.text}")
            
        except Exception as e:
            print(f"Error populating ElasticSearch: {e}")
            raise
    
    def search_restaurants_by_cuisine(self, cuisine, size=10):
        """
        Search for restaurants by cuisine in ElasticSearch.
        
        Args:
            cuisine (str): Cuisine type to search for
            size (int): Number of results to return
            
        Returns:
            list: List of restaurant IDs
        """
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"cuisine": cuisine.lower()}}
                    ]
                }
            },
            "size": size
        }
        
        try:
            response = requests.post(
                f"{self.es_endpoint}/restaurants/_search",
                json=query,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                hits = result['hits']['hits']
                return [hit['_source']['restaurant_id'] for hit in hits]
            else:
                print(f"Error searching ElasticSearch: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error searching ElasticSearch: {e}")
            return []
    
    def get_index_stats(self):
        """
        Get statistics about the restaurants index.
        """
        try:
            response = requests.get(f"{self.es_endpoint}/restaurants/_stats")
            if response.status_code == 200:
                stats = response.json()
                doc_count = stats['indices']['restaurants']['total']['docs']['count']
                print(f"Total documents in restaurants index: {doc_count}")
                return doc_count
            else:
                print(f"Error getting index stats: {response.status_code}")
                return 0
        except Exception as e:
            print(f"Error getting index stats: {e}")
            return 0

def main():
    """
    Main function to set up ElasticSearch.
    """
    es_endpoint = os.getenv('ELASTICSEARCH_ENDPOINT')
    if not es_endpoint:
        print("Error: ELASTICSEARCH_ENDPOINT environment variable not set")
        return
    
    # Initialize ElasticSearch manager
    es_manager = ElasticSearchManager(es_endpoint)
    
    try:
        # Create index
        es_manager.create_restaurants_index()
        
        # Populate from DynamoDB
        es_manager.populate_elasticsearch_from_dynamodb()
        
        # Get stats
        es_manager.get_index_stats()
        
        print("\n✅ ElasticSearch setup completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error setting up ElasticSearch: {e}")
        raise

if __name__ == "__main__":
    main()

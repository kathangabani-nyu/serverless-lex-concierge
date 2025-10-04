# Yelp API Scraper

Scripts to collect restaurant data from Yelp API for Manhattan restaurants.

## Requirements

- Yelp Fusion API key
- AWS credentials configured
- Python 3.x
- Required packages: `requests`, `boto3`, `python-dotenv`

## Setup

1. Install dependencies:
   ```bash
   pip install requests boto3 python-dotenv
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Run the scraper:
   ```bash
   python scrape_restaurants.py
   ```

## Features

- Collects 200+ restaurants per cuisine type
- Handles rate limiting and pagination
- Deduplicates restaurants
- Stores data in DynamoDB and ElasticSearch
- Supports multiple cuisine types

## Cuisine Types

- Italian
- Chinese
- Mexican
- Japanese
- Indian
- American
- Thai
- French

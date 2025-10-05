#!/usr/bin/env python3
"""
Complete validation script for Dining Concierge application.
This script tests all components to ensure they work together properly.
"""

import boto3
import json
import requests
import time
import os
from botocore.exceptions import ClientError

class DiningConciergeValidator:
    def __init__(self, aws_region='us-east-1'):
        """
        Initialize the validator.
        
        Args:
            aws_region (str): AWS region
        """
        self.aws_region = aws_region
        self.session = boto3.Session(region_name=aws_region)
        
        # Initialize AWS clients
        self.lambda_client = self.session.client('lambda')
        self.dynamodb = self.session.resource('dynamodb')
        self.sqs = self.session.client('sqs')
        self.ses = self.session.client('ses')
        self.lex = self.session.client('lex-runtime')
        self.apigateway = self.session.client('apigateway')
        
        # Load environment variables
        self.load_environment()
        
    def load_environment(self):
        """Load environment variables from .env file."""
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Set default values
        self.api_gateway_url = os.getenv('API_GATEWAY_URL', '')
        self.dynamodb_table = os.getenv('DYNAMODB_TABLE', 'yelp-restaurants')
        self.sqs_queue_url = os.getenv('SQS_QUEUE_URL', '')
        self.lex_bot_name = os.getenv('LEX_BOT_NAME', 'DiningConciergeBot')
        self.lex_bot_alias = os.getenv('LEX_BOT_ALIAS', 'PROD')
        self.ses_from_email = os.getenv('SES_FROM_EMAIL', '')
        
    def print_status(self, message, status="INFO"):
        """Print status message with formatting."""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m"
        }
        reset = "\033[0m"
        print(f"{colors.get(status, '')}[{status}]{reset} {message}")
    
    def test_lambda_functions(self):
        """Test all Lambda functions."""
        self.print_status("Testing Lambda functions...")
        
        functions = ['chat-api', 'lex-hook', 'suggestions-worker']
        
        for func_name in functions:
            try:
                response = self.lambda_client.get_function(FunctionName=func_name)
                self.print_status(f"✅ {func_name}: {response['Configuration']['State']}", "SUCCESS")
            except ClientError as e:
                self.print_status(f"❌ {func_name}: {e}", "ERROR")
                return False
        
        return True
    
    def test_dynamodb_table(self):
        """Test DynamoDB table."""
        self.print_status("Testing DynamoDB table...")
        
        try:
            table = self.dynamodb.Table(self.dynamodb_table)
            
            # Get table info
            response = table.describe_table()
            item_count = response['Table']['ItemCount']
            
            self.print_status(f"✅ DynamoDB table '{self.dynamodb_table}': {item_count} items", "SUCCESS")
            
            # Test a sample query
            scan_response = table.scan(Limit=1)
            if scan_response['Items']:
                self.print_status("✅ DynamoDB query test successful", "SUCCESS")
            else:
                self.print_status("⚠️ DynamoDB table is empty", "WARNING")
            
            return True
            
        except ClientError as e:
            self.print_status(f"❌ DynamoDB error: {e}", "ERROR")
            return False
    
    def test_sqs_queue(self):
        """Test SQS queue."""
        self.print_status("Testing SQS queue...")
        
        try:
            # Get queue attributes
            response = self.sqs.get_queue_attributes(
                QueueUrl=self.sqs_queue_url,
                AttributeNames=['All']
            )
            
            attributes = response['Attributes']
            message_count = attributes.get('ApproximateNumberOfMessages', '0')
            
            self.print_status(f"✅ SQS queue: {message_count} messages", "SUCCESS")
            
            return True
            
        except ClientError as e:
            self.print_status(f"❌ SQS error: {e}", "ERROR")
            return False
    
    def test_lex_bot(self):
        """Test Lex bot."""
        self.print_status("Testing Lex bot...")
        
        try:
            # Test Lex bot with a simple message
            response = self.lex.post_text(
                botName=self.lex_bot_name,
                botAlias=self.lex_bot_alias,
                userId='test-user',
                inputText='Hello'
            )
            
            if response.get('message'):
                self.print_status(f"✅ Lex bot response: {response['message']}", "SUCCESS")
                return True
            else:
                self.print_status("❌ Lex bot no response", "ERROR")
                return False
                
        except ClientError as e:
            self.print_status(f"❌ Lex bot error: {e}", "ERROR")
            return False
    
    def test_api_gateway(self):
        """Test API Gateway."""
        self.print_status("Testing API Gateway...")
        
        if not self.api_gateway_url:
            self.print_status("⚠️ API Gateway URL not configured", "WARNING")
            return False
        
        try:
            # Test API endpoint
            response = requests.post(
                f"{self.api_gateway_url}/chat",
                json={
                    "message": "Hello",
                    "sessionId": "test-session"
                },
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_status(f"✅ API Gateway response: {data.get('message', 'No message')}", "SUCCESS")
                return True
            else:
                self.print_status(f"❌ API Gateway error: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.print_status(f"❌ API Gateway error: {e}", "ERROR")
            return False
    
    def test_ses_configuration(self):
        """Test SES configuration."""
        self.print_status("Testing SES configuration...")
        
        try:
            # Get verified email addresses
            response = self.ses.list_verified_email_addresses()
            verified_emails = response['VerifiedEmailAddresses']
            
            if self.ses_from_email in verified_emails:
                self.print_status(f"✅ SES email '{self.ses_from_email}' is verified", "SUCCESS")
                return True
            else:
                self.print_status(f"⚠️ SES email '{self.ses_from_email}' not verified", "WARNING")
                return False
                
        except ClientError as e:
            self.print_status(f"❌ SES error: {e}", "ERROR")
            return False
    
    def test_complete_flow(self):
        """Test the complete user flow."""
        self.print_status("Testing complete user flow...")
        
        if not self.api_gateway_url:
            self.print_status("⚠️ Cannot test complete flow - API Gateway URL not configured", "WARNING")
            return False
        
        try:
            # Test complete conversation flow
            test_messages = [
                "Hello",
                "I need restaurant suggestions",
                "Manhattan",
                "Japanese",
                "2",
                "7 PM",
                "test@example.com"
            ]
            
            session_id = f"test-session-{int(time.time())}"
            
            for i, message in enumerate(test_messages):
                response = requests.post(
                    f"{self.api_gateway_url}/chat",
                    json={
                        "message": message,
                        "sessionId": session_id
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.print_status(f"✅ Message {i+1}: {data.get('message', 'No response')}", "SUCCESS")
                else:
                    self.print_status(f"❌ Message {i+1} failed: {response.status_code}", "ERROR")
                    return False
                
                # Small delay between messages
                time.sleep(1)
            
            self.print_status("✅ Complete flow test successful", "SUCCESS")
            return True
            
        except Exception as e:
            self.print_status(f"❌ Complete flow test error: {e}", "ERROR")
            return False
    
    def test_elasticsearch(self):
        """Test ElasticSearch connection."""
        self.print_status("Testing ElasticSearch...")
        
        es_endpoint = os.getenv('ELASTICSEARCH_ENDPOINT', '')
        if not es_endpoint:
            self.print_status("⚠️ ElasticSearch endpoint not configured", "WARNING")
            return False
        
        try:
            # Test ElasticSearch connection
            response = requests.get(
                f"{es_endpoint}/restaurants/_count",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                self.print_status(f"✅ ElasticSearch: {count} restaurants indexed", "SUCCESS")
                return True
            else:
                self.print_status(f"❌ ElasticSearch error: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.print_status(f"❌ ElasticSearch error: {e}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all validation tests."""
        self.print_status("🧪 Starting Dining Concierge validation tests...")
        self.print_status("=" * 50)
        
        tests = [
            ("Lambda Functions", self.test_lambda_functions),
            ("DynamoDB Table", self.test_dynamodb_table),
            ("SQS Queue", self.test_sqs_queue),
            ("Lex Bot", self.test_lex_bot),
            ("API Gateway", self.test_api_gateway),
            ("SES Configuration", self.test_ses_configuration),
            ("ElasticSearch", self.test_elasticsearch),
            ("Complete Flow", self.test_complete_flow)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            self.print_status(f"\n🔍 Testing {test_name}...")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                self.print_status(f"❌ {test_name} test failed: {e}", "ERROR")
                results.append((test_name, False))
        
        # Print summary
        self.print_status("\n" + "=" * 50)
        self.print_status("📊 VALIDATION SUMMARY")
        self.print_status("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.print_status(f"{test_name}: {status}", "SUCCESS" if result else "ERROR")
            if result:
                passed += 1
        
        self.print_status(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.print_status("🎉 All tests passed! Your Dining Concierge is ready!", "SUCCESS")
        else:
            self.print_status("⚠️ Some tests failed. Please check the errors above.", "WARNING")
        
        return passed == total

def main():
    """Main validation function."""
    validator = DiningConciergeValidator()
    
    try:
        success = validator.run_all_tests()
        return 0 if success else 1
        
    except Exception as e:
        validator.print_status(f"💥 Validation failed: {e}", "ERROR")
        return 1

if __name__ == "__main__":
    exit(main())

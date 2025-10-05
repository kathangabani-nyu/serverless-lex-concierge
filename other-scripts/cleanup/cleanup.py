#!/usr/bin/env python3
"""
Cleanup script for Dining Concierge application.
This script removes all AWS resources created during deployment.
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

class DiningConciergeCleanup:
    def __init__(self, aws_region='us-east-1'):
        """
        Initialize the cleanup manager.
        
        Args:
            aws_region (str): AWS region
        """
        self.aws_region = aws_region
        self.session = boto3.Session(region_name=aws_region)
        
        # Initialize AWS clients
        self.lambda_client = self.session.client('lambda')
        self.s3_client = self.session.client('s3')
        self.apigateway = self.session.client('apigateway')
        self.iam = self.session.client('iam')
        self.dynamodb = self.session.client('dynamodb')
        self.sqs = self.session.client('sqs')
        self.ses = self.session.client('ses')
        self.lex = self.session.client('lex-models')
        self.events = self.session.client('events')
        self.es_client = self.session.client('es')
        
    def delete_lambda_functions(self):
        """Delete all Lambda functions."""
        functions = ['chat-api', 'lex-hook', 'data-processor']
        
        for function_name in functions:
            try:
                self.lambda_client.delete_function(FunctionName=function_name)
                print(f"Deleted Lambda function: {function_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    print(f"Lambda function {function_name} not found")
                else:
                    print(f"Error deleting Lambda function {function_name}: {e}")
    
    def delete_api_gateways(self):
        """Delete API Gateway resources."""
        try:
            # List all APIs
            response = self.apigateway.get_rest_apis()
            
            for api in response['items']:
                if 'DiningConcierge' in api['name']:
                    # Delete the API
                    self.apigateway.delete_rest_api(restApiId=api['id'])
                    print(f"Deleted API Gateway: {api['name']}")
                    
        except ClientError as e:
            print(f"Error deleting API Gateway: {e}")
    
    def delete_s3_buckets(self):
        """Delete S3 buckets."""
        try:
            # List all buckets
            response = self.s3_client.list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                if 'dining-concierge' in bucket_name.lower():
                    try:
                        # Delete all objects first
                        objects = self.s3_client.list_objects_v2(Bucket=bucket_name)
                        if 'Contents' in objects:
                            for obj in objects['Contents']:
                                self.s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
                        
                        # Delete the bucket
                        self.s3_client.delete_bucket(Bucket=bucket_name)
                        print(f"Deleted S3 bucket: {bucket_name}")
                        
                    except ClientError as e:
                        print(f"Error deleting bucket {bucket_name}: {e}")
                        
        except ClientError as e:
            print(f"Error listing buckets: {e}")
    
    def delete_dynamodb_tables(self):
        """Delete DynamoDB tables."""
        tables = ['yelp-restaurants']
        
        for table_name in tables:
            try:
                self.dynamodb.delete_table(TableName=table_name)
                print(f"Deleted DynamoDB table: {table_name}")
                
                # Wait for table to be deleted
                waiter = self.dynamodb.get_waiter('table_not_exists')
                waiter.wait(TableName=table_name)
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    print(f"DynamoDB table {table_name} not found")
                else:
                    print(f"Error deleting DynamoDB table {table_name}: {e}")
    
    def delete_sqs_queues(self):
        """Delete SQS queues."""
        queues = ['restaurant-requests', 'restaurant-requests-dlq']
        
        for queue_name in queues:
            try:
                queue_url = self.sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
                self.sqs.delete_queue(QueueUrl=queue_url)
                print(f"Deleted SQS queue: {queue_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                    print(f"SQS queue {queue_name} not found")
                else:
                    print(f"Error deleting SQS queue {queue_name}: {e}")
    
    def delete_lex_bots(self):
        """Delete Lex bots."""
        try:
            # List bots
            response = self.lex.get_bots()
            
            for bot in response['bots']:
                if 'DiningConcierge' in bot['name']:
                    # Delete bot alias first
                    try:
                        aliases = self.lex.get_bot_aliases(botName=bot['name'])
                        for alias in aliases['botAliases']:
                            self.lex.delete_bot_alias(botName=bot['name'], name=alias['name'])
                    except ClientError:
                        pass
                    
                    # Delete bot
                    self.lex.delete_bot(name=bot['name'])
                    print(f"Deleted Lex bot: {bot['name']}")
                    
        except ClientError as e:
            print(f"Error deleting Lex bots: {e}")
    
    def delete_eventbridge_rules(self):
        """Delete EventBridge rules."""
        try:
            # List rules
            response = self.events.list_rules()
            
            for rule in response['Rules']:
                if 'restaurant-processor' in rule['Name']:
                    # Remove targets first
                    targets = self.events.list_targets_by_rule(Rule=rule['Name'])
                    if targets['Targets']:
                        target_ids = [target['Id'] for target in targets['Targets']]
                        self.events.remove_targets(Rule=rule['Name'], Ids=target_ids)
                    
                    # Delete rule
                    self.events.delete_rule(Name=rule['Name'])
                    print(f"Deleted EventBridge rule: {rule['Name']}")
                    
        except ClientError as e:
            print(f"Error deleting EventBridge rules: {e}")
    
    def delete_elasticsearch_domains(self):
        """Delete ElasticSearch domains."""
        try:
            # List domains
            response = self.es_client.list_domain_names()
            
            for domain in response['DomainNames']:
                if 'dining-concierge' in domain['DomainName'].lower():
                    self.es_client.delete_elasticsearch_domain(DomainName=domain['DomainName'])
                    print(f"Deleted ElasticSearch domain: {domain['DomainName']}")
                    
        except ClientError as e:
            print(f"Error deleting ElasticSearch domains: {e}")
    
    def delete_iam_roles(self):
        """Delete IAM roles."""
        roles = ['dining-concierge-lambda-execution-role']
        
        for role_name in roles:
            try:
                # Detach policies first
                attached_policies = self.iam.list_attached_role_policies(RoleName=role_name)
                for policy in attached_policies['AttachedPolicies']:
                    self.iam.detach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy['PolicyArn']
                    )
                
                # Delete role
                self.iam.delete_role(RoleName=role_name)
                print(f"Deleted IAM role: {role_name}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    print(f"IAM role {role_name} not found")
                else:
                    print(f"Error deleting IAM role {role_name}: {e}")
    
    def cleanup_all(self):
        """Clean up all resources."""
        print("Starting cleanup of Dining Concierge resources...")
        
        try:
            # Delete resources in reverse order of creation
            self.delete_eventbridge_rules()
            self.delete_lambda_functions()
            self.delete_api_gateways()
            self.delete_lex_bots()
            self.delete_sqs_queues()
            self.delete_dynamodb_tables()
            self.delete_elasticsearch_domains()
            self.delete_s3_buckets()
            self.delete_iam_roles()
            
            print("\n✅ Cleanup completed successfully!")
            print("All Dining Concierge resources have been removed.")
            
        except Exception as e:
            print(f"\n❌ Cleanup failed: {e}")
            raise

def main():
    """Main cleanup function."""
    print("🧹 Dining Concierge Cleanup Tool")
    print("This will delete ALL AWS resources created for this project.")
    
    confirm = input("\nAre you sure you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cleanup cancelled.")
        return 0
    
    cleanup = DiningConciergeCleanup()
    
    try:
        cleanup.cleanup_all()
        print("\n🎉 Cleanup successful!")
        
    except Exception as e:
        print(f"\n💥 Cleanup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

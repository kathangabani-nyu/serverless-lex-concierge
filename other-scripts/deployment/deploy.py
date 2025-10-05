#!/usr/bin/env python3
"""
Comprehensive deployment script for Dining Concierge application.
This script handles the complete deployment of all AWS resources.
"""

import boto3
import json
import os
import time
import zipfile
import shutil
from pathlib import Path
from botocore.exceptions import ClientError

class DiningConciergeDeployer:
    def __init__(self, aws_region='us-east-1'):
        """
        Initialize the deployer.
        
        Args:
            aws_region (str): AWS region for deployment
        """
        self.aws_region = aws_region
        self.session = boto3.Session(region_name=aws_region)
        
        # Initialize AWS clients
        self.lambda_client = self.session.client('lambda')
        self.s3_client = self.session.client('s3')
        self.apigateway = self.session.client('apigateway')
        self.iam = self.session.client('iam')
        self.cloudformation = self.session.client('cloudformation')
        
        # Configuration
        self.project_name = 'dining-concierge'
        self.bucket_name = f"{self.project_name}-deployment-{int(time.time())}"
        
    def create_deployment_bucket(self):
        """Create S3 bucket for deployment artifacts."""
        try:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            print(f"Created deployment bucket: {self.bucket_name}")
            return self.bucket_name
        except ClientError as e:
            print(f"Error creating bucket: {e}")
            raise
    
    def package_lambda_function(self, function_dir, function_name):
        """
        Package Lambda function for deployment.
        
        Args:
            function_dir (str): Directory containing Lambda function
            function_name (str): Name of the Lambda function
            
        Returns:
            str: Path to the deployment package
        """
        package_path = f"{function_name}.zip"
        
        # Create zip file
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add Python files
            for file_path in Path(function_dir).glob('*.py'):
                zip_file.write(file_path, file_path.name)
            
            # Add requirements if exists
            requirements_path = Path(function_dir) / 'requirements.txt'
            if requirements_path.exists():
                # Install dependencies to a temp directory
                temp_dir = f"temp_{function_name}"
                os.system(f"pip install -r {requirements_path} -t {temp_dir}")
                
                # Add installed packages
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, temp_dir)
                        zip_file.write(file_path, arc_path)
                
                # Clean up temp directory
                shutil.rmtree(temp_dir)
        
        print(f"Packaged {function_name}: {package_path}")
        return package_path
    
    def deploy_lambda_function(self, function_name, package_path, environment_vars=None):
        """
        Deploy Lambda function.
        
        Args:
            function_name (str): Name of the Lambda function
            package_path (str): Path to the deployment package
            environment_vars (dict): Environment variables
        """
        try:
            # Upload package to S3
            s3_key = f"lambda-functions/{function_name}.zip"
            self.s3_client.upload_file(package_path, self.bucket_name, s3_key)
            
            # Create or update Lambda function
            try:
                # Try to update existing function
                response = self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    S3Bucket=self.bucket_name,
                    S3Key=s3_key
                )
                print(f"Updated Lambda function: {function_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # Create new function
                    response = self.lambda_client.create_function(
                        FunctionName=function_name,
                        Runtime='python3.9',
                        Role=self._get_lambda_execution_role(),
                        Handler='lambda_function.lambda_handler',
                        Code={
                            'S3Bucket': self.bucket_name,
                            'S3Key': s3_key
                        },
                        Description=f'{function_name} for Dining Concierge',
                        Timeout=300,
                        MemorySize=256,
                        Environment={
                            'Variables': environment_vars or {}
                        }
                    )
                    print(f"Created Lambda function: {function_name}")
                else:
                    raise
            
            # Update environment variables if provided
            if environment_vars:
                self.lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Environment={'Variables': environment_vars}
                )
                print(f"Updated environment variables for {function_name}")
            
            return response['FunctionArn']
            
        except ClientError as e:
            print(f"Error deploying Lambda function {function_name}: {e}")
            raise
    
    def _get_lambda_execution_role(self):
        """Get or create Lambda execution role."""
        role_name = f"{self.project_name}-lambda-execution-role"
        
        try:
            # Try to get existing role
            response = self.iam.get_role(RoleName=role_name)
            return response['Role']['Arn']
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                # Create new role
                trust_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "lambda.amazonaws.com"
                            },
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
                
                # Create role
                self.iam.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description=f'Execution role for {self.project_name} Lambda functions'
                )
                
                # Attach policies
                policies = [
                    'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                    'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                    'arn:aws:iam::aws:policy/AmazonSQSFullAccess',
                    'arn:aws:iam::aws:policy/AmazonSESFullAccess',
                    'arn:aws:iam::aws:policy/AmazonLexFullAccess',
                    'arn:aws:iam::aws:policy/AmazonElasticsearchServiceFullAccess'
                ]
                
                for policy_arn in policies:
                    self.iam.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy_arn
                    )
                
                print(f"Created Lambda execution role: {role_name}")
                return f"arn:aws:iam::{self.session.client('sts').get_caller_identity()['Account']}:role/{role_name}"
            else:
                raise
    
    def create_api_gateway(self, api_name='DiningConciergeAPI'):
        """
        Create API Gateway with CORS support.
        
        Args:
            api_name (str): Name of the API
            
        Returns:
            str: API Gateway URL
        """
        try:
            # Create API
            response = self.apigateway.create_rest_api(
                name=api_name,
                description='API for Dining Concierge chatbot',
                endpointConfiguration={'types': ['REGIONAL']}
            )
            
            api_id = response['id']
            print(f"Created API Gateway: {api_id}")
            
            # Get root resource
            resources = self.apigateway.get_resources(restApiId=api_id)
            root_id = resources['items'][0]['id']
            
            # Create /v1 resource
            v1_resource = self.apigateway.create_resource(
                restApiId=api_id,
                parentId=root_id,
                pathPart='v1'
            )
            
            # Create /chatbot resource under /v1
            chat_resource = self.apigateway.create_resource(
                restApiId=api_id,
                parentId=v1_resource['id'],
                pathPart='chatbot'
            )
            
            chat_resource_id = chat_resource['id']
            
            # Create POST method
            self.apigateway.put_method(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='POST',
                authorizationType='NONE'
            )
            
            # Set up Lambda integration
            account_id = self.session.client('sts').get_caller_identity()['Account']
            lambda_arn = f"arn:aws:lambda:{self.aws_region}:{account_id}:function:chat-api"
            
            self.apigateway.put_integration(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='POST',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f"arn:aws:apigateway:{self.aws_region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            )
            
            # Enable CORS
            self.apigateway.put_method_response(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='POST',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': True,
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True
                }
            )
            
            self.apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='POST',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'"
                }
            )
            
            # Create OPTIONS method for CORS
            self.apigateway.put_method(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            self.apigateway.put_integration(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            
            self.apigateway.put_method_response(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': True,
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True
                }
            )
            
            self.apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'"
                }
            )
            
            # Deploy API
            deployment = self.apigateway.create_deployment(
                restApiId=api_id,
                stageName='prod',
                description='Production deployment'
            )
            
            api_url = f"https://{api_id}.execute-api.{self.aws_region}.amazonaws.com/prod"
            print(f"API Gateway deployed: {api_url}")
            
            return api_url
            
        except ClientError as e:
            print(f"Error creating API Gateway: {e}")
            raise
    
    def deploy_frontend(self, frontend_dir='frontend/build'):
        """
        Deploy frontend to S3 bucket.
        
        Args:
            frontend_dir (str): Directory containing built frontend
        """
        try:
            frontend_bucket = f"{self.project_name}-frontend-{int(time.time())}"
            
            # Create bucket
            self.s3_client.create_bucket(Bucket=frontend_bucket)
            
            # Configure bucket for static website hosting
            self.s3_client.put_bucket_website(
                Bucket=frontend_bucket,
                WebsiteConfiguration={
                    'IndexDocument': {'Suffix': 'index.html'},
                    'ErrorDocument': {'Key': 'index.html'}
                }
            )
            
            # Upload files
            for root, dirs, files in os.walk(frontend_dir):
                for file in files:
                    local_path = os.path.join(root, file)
                    s3_key = os.path.relpath(local_path, frontend_dir)
                    
                    # Set content type
                    content_type = 'text/html' if file.endswith('.html') else 'application/javascript' if file.endswith('.js') else 'text/css' if file.endswith('.css') else 'application/octet-stream'
                    
                    self.s3_client.upload_file(
                        local_path,
                        frontend_bucket,
                        s3_key,
                        ExtraArgs={'ContentType': content_type}
                    )
            
            # Make bucket public
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{frontend_bucket}/*"
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=frontend_bucket,
                Policy=json.dumps(bucket_policy)
            )
            
            website_url = f"http://{frontend_bucket}.s3-website-{self.aws_region}.amazonaws.com"
            print(f"Frontend deployed: {website_url}")
            
            return website_url
            
        except ClientError as e:
            print(f"Error deploying frontend: {e}")
            raise
    
    def deploy_all(self):
        """Deploy all components."""
        try:
            print("Starting deployment of Dining Concierge application...")
            
            # Create deployment bucket
            self.create_deployment_bucket()
            
            # Deploy Lambda functions
            lambda_functions = [
                {
                    'name': 'chat-api',
                    'dir': 'lambda-functions/chat-api',
                    'env_vars': {
                        'AWS_REGION': self.aws_region,
                        'LEX_BOT_NAME': 'DiningConciergeBot',
                        'LEX_BOT_ALIAS': 'PROD'
                    }
                },
                {
                    'name': 'lex-hook',
                    'dir': 'lambda-functions/lex-hook',
                    'env_vars': {
                        'AWS_REGION': self.aws_region,
                        'SQS_QUEUE_URL': os.getenv('SQS_QUEUE_URL', '')
                    }
                },
                {
                    'name': 'data-processor',
                    'dir': 'lambda-functions/data-processor',
                    'env_vars': {
                        'AWS_REGION': self.aws_region,
                        'DYNAMODB_TABLE': 'yelp-restaurants',
                        'ELASTICSEARCH_ENDPOINT': os.getenv('ELASTICSEARCH_ENDPOINT', ''),
                        'SES_FROM_EMAIL': os.getenv('SES_FROM_EMAIL', '')
                    }
                }
            ]
            
            for func in lambda_functions:
                package_path = self.package_lambda_function(func['dir'], func['name'])
                self.deploy_lambda_function(func['name'], package_path, func['env_vars'])
            
            # Create API Gateway
            api_url = self.create_api_gateway()
            
            # Deploy frontend (if built)
            if os.path.exists('frontend/build'):
                frontend_url = self.deploy_frontend()
                print(f"\nFrontend URL: {frontend_url}")
            
            print(f"\n✅ Deployment completed successfully!")
            print(f"API Gateway URL: {api_url}")
            print(f"Deployment Bucket: {self.bucket_name}")
            
            return {
                'api_url': api_url,
                'deployment_bucket': self.bucket_name
            }
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {e}")
            raise

def main():
    """Main deployment function."""
    deployer = DiningConciergeDeployer()
    
    try:
        result = deployer.deploy_all()
        print(f"\n🎉 Deployment successful!")
        print(f"API URL: {result['api_url']}")
        
    except Exception as e:
        print(f"\n💥 Deployment failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

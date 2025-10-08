import boto3
import json
import os
from botocore.exceptions import ClientError

class AWSInfrastructureManager:
    def __init__(self, aws_region='us-east-1'):
        """
        Initialize AWS infrastructure manager.
        
        Args:
            aws_region (str): AWS region
        """
        self.aws_region = aws_region
        self.sqs = boto3.client('sqs', region_name=aws_region)
        self.ses = boto3.client('ses', region_name=aws_region)
        self.lex = boto3.client('lex-models', region_name=aws_region)
        self.apigateway = boto3.client('apigateway', region_name=aws_region)
        self.lambda_client = boto3.client('lambda', region_name=aws_region)
        self.events = boto3.client('events', region_name=aws_region)
        
    def create_sqs_queue(self, queue_name='restaurant-requests'):
        """
        Create SQS queue for restaurant requests.
        
        Args:
            queue_name (str): Name of the SQS queue
            
        Returns:
            str: Queue URL
        """
        try:
            # Create main queue
            response = self.sqs.create_queue(
                QueueName=queue_name,
                Attributes={
                    'VisibilityTimeout': '300',  # 5 minutes
                    'MessageRetentionPeriod': '1209600',  # 14 days
                    'ReceiveMessageWaitTimeSeconds': '20'  # Long polling
                }
            )
            
            queue_url = response['QueueUrl']
            print(f"SQS queue '{queue_name}' created: {queue_url}")
            
            # Create Dead Letter Queue
            dlq_name = f"{queue_name}-dlq"
            dlq_response = self.sqs.create_queue(
                QueueName=dlq_name,
                Attributes={
                    'MessageRetentionPeriod': '1209600'  # 14 days
                }
            )
            
            dlq_url = dlq_response['QueueUrl']
            dlq_arn = self._get_queue_arn(dlq_url)
            
            print(f"Dead Letter Queue '{dlq_name}' created: {dlq_url}")
            
            # Configure main queue to use DLQ
            self.sqs.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes={
                    'RedrivePolicy': json.dumps({
                        'deadLetterTargetArn': dlq_arn,
                        'maxReceiveCount': 3
                    })
                }
            )
            
            print(f"Configured DLQ for '{queue_name}' with maxReceiveCount=3")
            
            return queue_url
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'QueueAlreadyExists':
                print(f"Queue '{queue_name}' already exists")
                return self.sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
            else:
                print(f"Error creating SQS queue: {e}")
                raise
    
    def _get_queue_arn(self, queue_url):
        """Get ARN for a queue URL."""
        account_id = boto3.client('sts').get_caller_identity()['Account']
        queue_name = queue_url.split('/')[-1]
        return f"arn:aws:sqs:{self.aws_region}:{account_id}:{queue_name}"
    
    def setup_ses(self, from_email):
        """
        Set up SES for sending emails.
        
        Args:
            from_email (str): Email address to send from
            
        Returns:
            bool: True if setup successful
        """
        try:
            # Verify email address
            self.ses.verify_email_identity(EmailAddress=from_email)
            print(f"Verification email sent to {from_email}")
            print("Please check your email and click the verification link")
            
            # Note: In production, you'd want to verify the domain instead
            return True
            
        except ClientError as e:
            print(f"Error setting up SES: {e}")
            return False
    
    def create_lex_bot(self, bot_name='DiningConciergeBot'):
        """
        Create Amazon Lex bot with required intents.
        
        Args:
            bot_name (str): Name of the Lex bot
            
        Returns:
            str: Bot name
        """
        try:
            # Check if bot already exists
            try:
                self.lex.get_bot(name=bot_name, versionOrAlias='$LATEST')
                print(f"Lex bot '{bot_name}' already exists")
                return bot_name
            except ClientError as e:
                if e.response['Error']['Code'] != 'NotFoundException':
                    raise
            
            # Create GreetingIntent
            greeting_intent = {
                'name': 'GreetingIntent',
                'sampleUtterances': [
                    'Hello',
                    'Hi',
                    'Hey',
                    'Good morning',
                    'Good afternoon',
                    'Good evening',
                    'How are you',
                    'What can you help me with'
                ],
                'fulfillmentActivity': {
                    'type': 'ReturnIntent'
                }
            }
            
            # Create ThankYouIntent
            thankyou_intent = {
                'name': 'ThankYouIntent',
                'sampleUtterances': [
                    'Thank you',
                    'Thanks',
                    'Thank you very much',
                    'Thanks a lot',
                    'Appreciate it',
                    'Much appreciated'
                ],
                'fulfillmentActivity': {
                    'type': 'ReturnIntent'
                }
            }
            
            # Create DiningSuggestionsIntent
            dining_intent = {
                'name': 'DiningSuggestionsIntent',
                'sampleUtterances': [
                    'I need restaurant suggestions',
                    'Find me a restaurant',
                    'I want to eat {Cuisine} food',
                    'Looking for {Cuisine} restaurants in {Location}',
                    'Can you recommend {Cuisine} restaurants',
                    'I need dining suggestions',
                    'Help me find a place to eat'
                ],
                'slots': [
                    {
                        'name': 'Location',
                        'slotType': 'AMAZON.City',
                        'slotConstraint': 'Required',
                        'valueElicitationPrompt': {
                            'messages': [
                                {
                                    'contentType': 'PlainText',
                                    'content': 'Where would you like to dine? (e.g., Manhattan, Midtown, Upper East Side)'
                                }
                            ]
                        }
                    },
                    {
                        'name': 'Cuisine',
                        'slotType': 'AMAZON.Food',
                        'slotConstraint': 'Required',
                        'valueElicitationPrompt': {
                            'messages': [
                                {
                                    'contentType': 'PlainText',
                                    'content': 'What type of cuisine are you in the mood for? (e.g., Italian, Chinese, Mexican, Japanese, Indian)'
                                }
                            ]
                        }
                    },
                    {
                        'name': 'DiningTime',
                        'slotType': 'AMAZON.TIME',
                        'slotConstraint': 'Required',
                        'valueElicitationPrompt': {
                            'messages': [
                                {
                                    'contentType': 'PlainText',
                                    'content': 'What time would you like to dine? (e.g., 7:00 PM, 8:30 PM)'
                                }
                            ]
                        }
                    },
                    {
                        'name': 'NumberOfPeople',
                        'slotType': 'AMAZON.NUMBER',
                        'slotConstraint': 'Required',
                        'valueElicitationPrompt': {
                            'messages': [
                                {
                                    'contentType': 'PlainText',
                                    'content': 'How many people will be dining? (e.g., 2, 4, 6)'
                                }
                            ]
                        }
                    },
                    {
                        'name': 'Email',
                        'slotType': 'AMAZON.EmailAddress',
                        'slotConstraint': 'Required',
                        'valueElicitationPrompt': {
                            'messages': [
                                {
                                    'contentType': 'PlainText',
                                    'content': 'What\'s your email address so I can send you the recommendations?'
                                }
                            ]
                        }
                    }
                ],
                'fulfillmentActivity': {
                    'type': 'ReturnIntent'
                }
            }
            
            # Create intents
            print("Creating Lex intents...")
            self.lex.put_intent(**greeting_intent)
            self.lex.put_intent(**thankyou_intent)
            self.lex.put_intent(**dining_intent)
            
            # Create bot
            bot_response = self.lex.put_bot(
                name=bot_name,
                description='Dining Concierge Bot for restaurant recommendations',
                intents=[
                    {'intentName': 'GreetingIntent', 'intentVersion': '$LATEST'},
                    {'intentName': 'ThankYouIntent', 'intentVersion': '$LATEST'},
                    {'intentName': 'DiningSuggestionsIntent', 'intentVersion': '$LATEST'}
                ],
                clarificationPrompt={
                    'messages': [
                        {
                            'contentType': 'PlainText',
                            'content': 'I didn\'t understand that. Could you please rephrase?'
                        }
                    ],
                    'maxAttempts': 2
                },
                abortStatement={
                    'messages': [
                        {
                            'contentType': 'PlainText',
                            'content': 'Sorry, I couldn\'t help you this time. Please try again later.'
                        }
                    ]
                },
                idleSessionTTLInSeconds=300,
                voiceId='Joanna',
                locale='en-US',
                childDirected=False
            )
            
            print(f"Lex bot '{bot_name}' created successfully")
            
            # Build the bot
            print("Building Lex bot...")
            self.lex.put_bot_alias(
                name='PROD',
                botName=bot_name,
                botVersion='$LATEST',
                description='Production alias'
            )
            
            return bot_name
            
        except ClientError as e:
            print(f"Error creating Lex bot: {e}")
            raise
    
    def create_eventbridge_rule(self, lambda_function_name):
        """
        Create EventBridge rule to trigger Lambda every minute.
        
        Args:
            lambda_function_name (str): Name of the Lambda function to trigger
        """
        try:
            rule_name = 'restaurant-processor-trigger'
            
            # Create rule
            response = self.events.put_rule(
                Name=rule_name,
                Description='Trigger restaurant processor Lambda every minute',
                ScheduleExpression='rate(1 minute)',
                State='ENABLED'
            )
            
            rule_arn = response['RuleArn']
            print(f"EventBridge rule '{rule_name}' created")
            
            # Add Lambda function as target
            account_id = boto3.client('sts').get_caller_identity()['Account']
            lambda_arn = f"arn:aws:lambda:{self.aws_region}:{account_id}:function:{lambda_function_name}"
            
            self.events.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': lambda_arn
                    }
                ]
            )
            
            print(f"Added Lambda function '{lambda_function_name}' as target")
            
            return rule_name
            
        except ClientError as e:
            print(f"Error creating EventBridge rule: {e}")
            raise

def main():
    """
    Main function to set up AWS infrastructure.
    """
    # Load environment variables from .env file
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    manager = AWSInfrastructureManager()
    
    try:
        print("Setting up AWS infrastructure...")
        
        # Create SQS queue
        queue_url = manager.create_sqs_queue()
        print(f"SQS Queue URL: {queue_url}")
        
        # Set up SES (requires manual email verification)
        from_email = os.getenv('SES_FROM_EMAIL', 'your-email@example.com')
        manager.setup_ses(from_email)
        
        # Create Lex bot
        bot_name = manager.create_lex_bot()
        print(f"Lex Bot Name: {bot_name}")
        
        print("\nAWS infrastructure setup completed!")
        print("\nNext steps:")
        print("1. Verify your email address in SES")
        print("2. Deploy Lambda functions")
        print("3. Set up API Gateway")
        print("4. Configure Lambda function permissions")
        
    except Exception as e:
        print(f"\nError setting up infrastructure: {e}")
        raise

if __name__ == "__main__":
    main()

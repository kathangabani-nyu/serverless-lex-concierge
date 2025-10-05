# Utility Scripts

Collection of utility scripts for data collection, deployment, and maintenance of the Dining Concierge application.

## Overview

This directory contains essential scripts for:
- **Data Collection**: Yelp API scraping and data processing
- **Deployment**: Automated AWS resource deployment
- **Cleanup**: Resource cleanup and cost management
- **Infrastructure**: AWS service setup and configuration

## Directory Structure

```
other-scripts/
├── yelp-scraper/              # Yelp API data collection
│   ├── yelp_scraper.py       # Main scraper script
│   ├── elasticsearch_setup.py # ElasticSearch configuration
│   └── README.md             # Scraper documentation
├── deployment/                # Deployment automation
│   ├── infrastructure_setup.py # AWS infrastructure setup
│   ├── deploy.py             # Complete deployment script
│   └── README.md             # Deployment documentation
├── cleanup/                   # Resource cleanup
│   ├── cleanup.py            # Complete cleanup script
│   └── README.md             # Cleanup documentation
└── README.md                 # This file
```

## Scripts Overview

### Yelp Scraper (`yelp-scraper/`)

**Purpose**: Collect restaurant data from Yelp API and populate AWS services.

**Key Features**:
- Collects 1000+ Manhattan restaurants
- Supports 15+ cuisine types
- Stores data in DynamoDB
- Creates ElasticSearch index
- Handles API rate limiting
- Duplicate prevention

**Usage**:
```bash
# Set Yelp API key
export YELP_API_KEY="your_api_key"

# Run scraper
python other-scripts/yelp-scraper/yelp_scraper.py

# Setup ElasticSearch
python other-scripts/yelp-scraper/elasticsearch_setup.py
```

**Output**:
- DynamoDB table: `yelp-restaurants`
- ElasticSearch index: `restaurants`
- Summary report: `restaurant_collection_summary.json`

### Deployment (`deployment/`)

**Purpose**: Automated deployment of all AWS resources and Lambda functions.

**Key Features**:
- Creates AWS infrastructure
- Deploys Lambda functions
- Sets up API Gateway
- Configures SQS queues
- Deploys frontend to S3
- Handles IAM roles and permissions

**Usage**:
```bash
# Setup infrastructure
python other-scripts/deployment/infrastructure_setup.py

# Deploy application
python other-scripts/deployment/deploy.py
```

**Resources Created**:
- Lambda functions (LF0, LF1, LF2)
- API Gateway with CORS
- SQS queue with DLQ
- DynamoDB table
- ElasticSearch domain
- S3 buckets
- IAM roles and policies

### Cleanup (`cleanup/`)

**Purpose**: Remove all AWS resources to prevent ongoing charges.

**Key Features**:
- Removes all Lambda functions
- Deletes API Gateway resources
- Cleans up S3 buckets
- Removes DynamoDB tables
- Deletes ElasticSearch domains
- Removes IAM roles
- Handles dependencies

**Usage**:
```bash
# Interactive cleanup
python other-scripts/cleanup/cleanup.py
```

**Safety Features**:
- Confirmation prompts
- Dependency checking
- Error handling
- Resource verification

## Prerequisites

### System Requirements
- **Python 3.9+** with pip
- **AWS CLI** configured
- **Node.js 16+** (for frontend deployment)
- **Git** for version control

### AWS Permissions
Required AWS permissions for scripts:
- Lambda (create, update, delete functions)
- API Gateway (create, deploy, delete APIs)
- S3 (create, upload, delete buckets)
- DynamoDB (create, delete tables)
- ElasticSearch (create, delete domains)
- SQS (create, delete queues)
- SES (verify email addresses)
- Lex (create, delete bots)
- IAM (create, delete roles and policies)
- CloudWatch Events (create, delete rules)

### External APIs
- **Yelp API Key**: Required for data collection
- Get from [Yelp Developers](https://www.yelp.com/developers)

## Environment Setup

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd serverless-lex-concierge
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp env.example .env
# Edit .env with your values
```

### 4. Set AWS Credentials
```bash
aws configure
# Enter your AWS credentials
```

## Usage Workflow

### Complete Setup
```bash
# 1. Setup infrastructure
python other-scripts/deployment/infrastructure_setup.py

# 2. Collect restaurant data
python other-scripts/yelp-scraper/yelp_scraper.py
python other-scripts/yelp-scraper/elasticsearch_setup.py

# 3. Deploy application
python other-scripts/deployment/deploy.py

# 4. Build and deploy frontend
cd frontend && npm run build && cd ..
python other-scripts/deployment/deploy.py
```

### Maintenance
```bash
# Update restaurant data
python other-scripts/yelp-scraper/yelp_scraper.py

# Redeploy application
python other-scripts/deployment/deploy.py

# Clean up resources
python other-scripts/cleanup/cleanup.py
```

## Configuration

### Environment Variables

Key environment variables for scripts:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Yelp API
YELP_API_KEY=your_yelp_api_key

# AWS Services
DYNAMODB_TABLE=yelp-restaurants
ELASTICSEARCH_ENDPOINT=https://your-es-domain.us-east-1.es.amazonaws.com
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/account/queue
SES_FROM_EMAIL=your-verified-email@example.com
```

### Script Configuration

Each script can be configured by modifying:
- **Command line arguments**
- **Environment variables**
- **Configuration files**
- **Hardcoded parameters**

## Error Handling

### Common Issues

1. **AWS Credentials**
   - Verify AWS CLI configuration
   - Check IAM permissions
   - Ensure region is correct

2. **API Rate Limits**
   - Yelp API has daily limits
   - Implement retry logic
   - Use exponential backoff

3. **Resource Conflicts**
   - Check for existing resources
   - Use unique naming conventions
   - Handle resource dependencies

4. **Network Issues**
   - Check internet connectivity
   - Verify AWS service endpoints
   - Handle timeout errors

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check AWS service status:
```bash
aws health describe-events --region us-east-1
```

## Performance Optimization

### Data Collection
- **Batch Processing**: Process multiple restaurants per request
- **Parallel Processing**: Use threading for API calls
- **Caching**: Cache API responses to avoid duplicates
- **Rate Limiting**: Respect API rate limits

### Deployment
- **Incremental Updates**: Only update changed resources
- **Parallel Deployment**: Deploy multiple functions simultaneously
- **Resource Reuse**: Reuse existing resources when possible
- **Optimized Packages**: Minimize Lambda package sizes

### Cleanup
- **Dependency Resolution**: Handle resource dependencies
- **Batch Operations**: Delete multiple resources efficiently
- **Error Recovery**: Continue cleanup despite individual failures
- **Verification**: Confirm resources are actually deleted

## Monitoring

### Script Execution
- **Logging**: Comprehensive logging for all operations
- **Progress Tracking**: Show progress for long-running operations
- **Error Reporting**: Detailed error messages and suggestions
- **Success Confirmation**: Confirm successful operations

### AWS Resources
- **CloudWatch Logs**: Monitor Lambda function execution
- **CloudWatch Metrics**: Track resource usage and performance
- **SQS Monitoring**: Monitor queue depth and processing
- **Cost Tracking**: Monitor AWS costs and usage

## Security

### Best Practices
- **IAM Roles**: Use least privilege principle
- **Secrets Management**: Store sensitive data securely
- **Network Security**: Use VPC endpoints when appropriate
- **Audit Logging**: Enable CloudTrail for audit logs

### Data Protection
- **Encryption**: Encrypt data at rest and in transit
- **Access Control**: Implement proper access controls
- **Data Retention**: Set appropriate retention policies
- **Compliance**: Follow data protection regulations

## Troubleshooting

### Debug Steps
1. **Check Logs**: Review CloudWatch logs for errors
2. **Verify Permissions**: Ensure IAM permissions are correct
3. **Test Connectivity**: Verify network connectivity
4. **Check Resources**: Confirm AWS resources exist
5. **Validate Data**: Check data format and content

### Common Solutions

**Permission Denied**:
```bash
# Check IAM permissions
aws iam get-user
aws iam list-attached-user-policies --user-name your-username
```

**Resource Not Found**:
```bash
# List existing resources
aws lambda list-functions
aws s3 ls
aws dynamodb list-tables
```

**API Errors**:
```bash
# Check API Gateway logs
aws logs describe-log-groups --log-group-name-prefix /aws/apigateway
```

## Maintenance

### Regular Tasks
- **Update Dependencies**: Keep Python packages updated
- **Monitor Costs**: Track AWS spending
- **Review Logs**: Check for errors or issues
- **Test Functionality**: Verify all components work

### Updates
- **Script Improvements**: Enhance error handling and features
- **AWS Service Updates**: Use latest AWS service features
- **Security Patches**: Apply security updates
- **Performance Optimization**: Improve script performance

## Contributing

When modifying scripts:
1. **Follow Python PEP 8**: Use consistent coding style
2. **Add Error Handling**: Handle all possible error cases
3. **Include Logging**: Add comprehensive logging
4. **Update Documentation**: Keep documentation current
5. **Test Thoroughly**: Test all code paths

## License

This project is for educational purposes as part of CS-GY 9223 Fall 2025.
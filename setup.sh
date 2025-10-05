#!/bin/bash

# Dining Concierge - Complete Setup Script
# This script automates the entire setup process

set -e  # Exit on any error

echo "🍽️  Dining Concierge Setup Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.9+"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 16+"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm"
        exit 1
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install AWS CLI"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure'"
        exit 1
    fi
    
    print_success "All prerequisites met!"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    pip3 install boto3 requests python-dotenv
    print_success "Python dependencies installed!"
}

# Install Node.js dependencies
install_node_deps() {
    print_status "Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
    print_success "Node.js dependencies installed!"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    if [ ! -f .env ]; then
        cp env.example .env
        print_warning "Created .env file from template. Please edit it with your values:"
        print_warning "- AWS credentials"
        print_warning "- Yelp API key"
        print_warning "- SES email address"
        echo ""
        read -p "Press Enter after updating .env file..."
    else
        print_status ".env file already exists"
    fi
}

# Load environment variables
load_env() {
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
        print_success "Environment variables loaded!"
    else
        print_error ".env file not found!"
        exit 1
    fi
}

# Setup AWS infrastructure
setup_infrastructure() {
    print_status "Setting up AWS infrastructure..."
    python3 other-scripts/deployment/infrastructure_setup.py
    print_success "AWS infrastructure setup complete!"
    print_warning "Please verify your email address in SES console!"
}

# Collect restaurant data
collect_data() {
    print_status "Collecting restaurant data from Yelp..."
    python3 other-scripts/yelp-scraper/yelp_scraper.py
    print_success "Restaurant data collection complete!"
    
    print_status "Setting up ElasticSearch index..."
    python3 other-scripts/yelp-scraper/elasticsearch_setup.py
    print_success "ElasticSearch setup complete!"
}

# Deploy application
deploy_application() {
    print_status "Deploying Lambda functions and API Gateway..."
    python3 other-scripts/deployment/deploy.py
    print_success "Application deployment complete!"
}

# Build and deploy frontend
deploy_frontend() {
    print_status "Building React frontend..."
    cd frontend
    npm run build
    cd ..
    print_success "Frontend build complete!"
    
    print_status "Deploying frontend to S3..."
    python3 other-scripts/deployment/deploy.py
    print_success "Frontend deployment complete!"
}

# Test application
test_application() {
    print_status "Testing application..."
    
    # Get API Gateway URL from deployment
    API_URL=$(python3 -c "
import boto3
import json
apigateway = boto3.client('apigateway')
try:
    apis = apigateway.get_rest_apis()
    for api in apis['items']:
        if 'DiningConcierge' in api['name']:
            print(f'https://{api[\"id\"]}.execute-api.us-east-1.amazonaws.com/prod')
            break
except:
    print('API Gateway URL not found')
")
    
    if [ ! -z "$API_URL" ]; then
        print_status "Testing API endpoint: $API_URL/chat"
        
        # Test API
        response=$(curl -s -X POST "$API_URL/chat" \
            -H "Content-Type: application/json" \
            -d '{"message": "Hello", "sessionId": "test-session"}')
        
        if echo "$response" | grep -q "message"; then
            print_success "API test successful!"
        else
            print_warning "API test failed. Check CloudWatch Logs."
        fi
    else
        print_warning "Could not find API Gateway URL for testing"
    fi
}

# Main setup function
main() {
    echo ""
    print_status "Starting complete setup process..."
    echo ""
    
    # Step 1: Check prerequisites
    check_prerequisites
    echo ""
    
    # Step 2: Install dependencies
    install_python_deps
    install_node_deps
    echo ""
    
    # Step 3: Setup environment
    setup_environment
    load_env
    echo ""
    
    # Step 4: Setup infrastructure
    setup_infrastructure
    echo ""
    
    # Step 5: Collect data
    collect_data
    echo ""
    
    # Step 6: Deploy application
    deploy_application
    echo ""
    
    # Step 7: Deploy frontend
    deploy_frontend
    echo ""
    
    # Step 8: Test application
    test_application
    echo ""
    
    print_success "🎉 Setup complete!"
    echo ""
    print_status "Next steps:"
    echo "1. Verify your email address in SES console"
    echo "2. Test the complete flow through the frontend"
    echo "3. Check CloudWatch Logs for any issues"
    echo "4. Monitor SQS queue for message processing"
    echo ""
    print_status "To clean up resources later, run:"
    echo "python3 other-scripts/cleanup/cleanup.py"
}

# Run main function
main "$@"

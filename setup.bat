@echo off
REM Dining Concierge - Complete Setup Script for Windows
REM This script automates the entire setup process

echo 🍽️  Dining Concierge Setup Script
echo ==================================

REM Check prerequisites
echo [INFO] Checking prerequisites...

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.9+
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed. Please install Node.js 16+
    pause
    exit /b 1
)

REM Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is not installed. Please install npm
    pause
    exit /b 1
)

REM Check AWS CLI
aws --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS CLI is not installed. Please install AWS CLI
    pause
    exit /b 1
)

REM Check AWS credentials
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS credentials not configured. Please run 'aws configure'
    pause
    exit /b 1
)

echo [SUCCESS] All prerequisites met!

REM Install Python dependencies
echo [INFO] Installing Python dependencies...
pip install boto3 requests python-dotenv
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [SUCCESS] Python dependencies installed!

REM Install Node.js dependencies
echo [INFO] Installing Node.js dependencies...
cd frontend
npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies
    pause
    exit /b 1
)
cd ..
echo [SUCCESS] Node.js dependencies installed!

REM Setup environment
echo [INFO] Setting up environment...
if not exist .env (
    copy env.example .env
    echo [WARNING] Created .env file from template. Please edit it with your values:
    echo [WARNING] - AWS credentials
    echo [WARNING] - Yelp API key
    echo [WARNING] - SES email address
    echo.
    pause
) else (
    echo [INFO] .env file already exists
)

REM Load environment variables
if exist .env (
    echo [SUCCESS] Environment variables loaded!
) else (
    echo [ERROR] .env file not found!
    pause
    exit /b 1
)

REM Setup AWS infrastructure
echo [INFO] Setting up AWS infrastructure...
python other-scripts\deployment\infrastructure_setup.py
if errorlevel 1 (
    echo [ERROR] Failed to setup AWS infrastructure
    pause
    exit /b 1
)
echo [SUCCESS] AWS infrastructure setup complete!
echo [WARNING] Please verify your email address in SES console!

REM Collect restaurant data
echo [INFO] Collecting restaurant data from Yelp...
python other-scripts\yelp-scraper\yelp_scraper.py
if errorlevel 1 (
    echo [ERROR] Failed to collect restaurant data
    pause
    exit /b 1
)
echo [SUCCESS] Restaurant data collection complete!

echo [INFO] Setting up ElasticSearch index...
python other-scripts\yelp-scraper\elasticsearch_setup.py
if errorlevel 1 (
    echo [ERROR] Failed to setup ElasticSearch
    pause
    exit /b 1
)
echo [SUCCESS] ElasticSearch setup complete!

REM Deploy application
echo [INFO] Deploying Lambda functions and API Gateway...
python other-scripts\deployment\deploy.py
if errorlevel 1 (
    echo [ERROR] Failed to deploy application
    pause
    exit /b 1
)
echo [SUCCESS] Application deployment complete!

REM Build and deploy frontend
echo [INFO] Building React frontend...
cd frontend
npm run build
if errorlevel 1 (
    echo [ERROR] Failed to build frontend
    pause
    exit /b 1
)
cd ..
echo [SUCCESS] Frontend build complete!

echo [INFO] Deploying frontend to S3...
python other-scripts\deployment\deploy.py
if errorlevel 1 (
    echo [ERROR] Failed to deploy frontend
    pause
    exit /b 1
)
echo [SUCCESS] Frontend deployment complete!

echo.
echo [SUCCESS] 🎉 Setup complete!
echo.
echo [INFO] Next steps:
echo 1. Verify your email address in SES console
echo 2. Test the complete flow through the frontend
echo 3. Check CloudWatch Logs for any issues
echo 4. Monitor SQS queue for message processing
echo.
echo [INFO] To clean up resources later, run:
echo python other-scripts\cleanup\cleanup.py
echo.
pause

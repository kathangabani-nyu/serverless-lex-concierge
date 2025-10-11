# Serverless Lex Concierge

A professional, serverless, microservice-driven web application that provides restaurant recommendations through conversational AI using Amazon Lex.

## Project Overview

This project implements a **Dining Concierge chatbot** that collects user preferences through natural conversation and provides personalized restaurant suggestions from a curated database of 1000+ Manhattan restaurants. Built for **Cloud Computing and Big Data - Fall 2025** assignment.

### Key Features

- **Conversational AI**: Amazon Lex bot with 3 intents (Greeting, Thank You, Dining Suggestions)
- **Modern Frontend**: Beautiful web application with real-time chat interface
- **Serverless Architecture**: Fully serverless with AWS Lambda, API Gateway, and S3
- **Data Pipeline**: Yelp API → DynamoDB for comprehensive restaurant search
- **Email Notifications**: Automated restaurant recommendations via SES
- **Queue Processing**: SQS with Dead Letter Queue for reliable message handling
- **Monitoring**: CloudWatch integration for logging and monitoring

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Frontend  │────│   API Gateway    │────│  Chat-API (LF0) │
│   (S3 Hosted)   │    │   (CORS Enabled) │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Email (SES)   │◄───│ Data Processor   │◄───│   Lex Bot       │
│   Notifications │    │ Worker (LF2)     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   DynamoDB      │    │   SQS Queue      │    │  Lex_Code-Hook  │
│   (Restaurant   │    │   (with DLQ)     │    │     (LF1)       │
│    Details)     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Repository Structure

```
serverless-lex-concierge/
├── frontend/                    # Web frontend application
│   ├── assets/                  # Static assets (CSS, JS)
│   ├── chat.html               # Main chat interface
│   ├── swagger/                # API documentation
│   └── README.md               # Frontend documentation
├── lambda-functions/           # AWS Lambda functions
│   ├── chat-api/              # LF0: Chat API Lambda
│   ├── lex-code-hook/         # LF1: Lex code hook Lambda
│   ├── data-processor/         # LF2: Data processing Lambda
│   ├── suggestions-worker/     # Alternative LF2 implementation
│   └── README.md              # Lambda documentation
├── other-scripts/              # Utility scripts
│   ├── yelp-scraper/          # Yelp API data collection
│   ├── deployment/             # Deployment scripts
│   ├── cleanup/               # Resource cleanup scripts
│   └── README.md              # Scripts documentation
├── docs/                      # Documentation
│   ├── SETUP_GUIDE.md         # Complete setup guide
│   └── README.md              # Documentation index
├── requirements.txt           # Python dependencies
├── setup.sh                  # Linux/Mac setup script
├── setup.bat                 # Windows setup script
├── env.example               # Environment variables template
└── README.md                 # This file
```

## Assignment Requirements

| Requirement | Points | Status | Description |
|-------------|--------|--------|-------------|
| **Frontend Deployment** | 10 | ✅ Complete | Web app hosted on S3 with modern UI |
| **API Development** | 15 | ✅ Complete | API Gateway + Lambda with CORS |
| **Lex Chatbot** | 20 | ✅ Complete | 3 intents with conversation flow |
| **API Integration** | 10 | ✅ Complete | Lex integration with API Gateway |
| **Yelp Data Collection** | 15 | ✅ Complete | 1000+ Manhattan restaurants |
| **DynamoDB Setup** | 15 | ✅ Complete | Restaurant database infrastructure |
| **Suggestions Module** | 15 | ✅ Complete | Decoupled queue worker |
| **Extra Credit (DLQ)** | 10 | ✅ Complete | Dead Letter Queue implementation |

## Quick Start

### Prerequisites

- **AWS Account** with appropriate permissions
- **Python 3.9+** installed
- **Git** installed
- **Yelp API Key** (get from [Yelp Developers](https://www.yelp.com/developers))

### Automated Setup

**For Windows:**
```bash
setup.bat
```

**For Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup

1. **Clone and Setup Environment**
   ```bash
   git clone https://github.com/kathangabani-nyu/serverless-lex-concierge
   cd serverless-lex-concierge
   cp env.example .env
   # Edit .env with your values
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup AWS Infrastructure**
   ```bash
   python other-scripts/deployment/infrastructure_setup.py
   ```

4. **Collect Restaurant Data**
   ```bash
   python other-scripts/yelp-scraper/yelp_scraper.py
   ```

5. **Deploy Application**
   ```bash
   python other-scripts/deployment/deploy.py
   ```

## Testing

### API Testing
```bash
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "sessionId": "test-session"}'
```

### Complete Flow Testing
1. Open the frontend URL
2. Start conversation: "Hello"
3. Follow bot prompts for restaurant preferences
4. Check email for recommendations

## Components

### Lambda Functions
- **LF0 (chat-api)**: Handles API requests and integrates with Lex
- **LF1 (lex-code-hook)**: Lex code hook for intent processing and SQS integration
- **LF2 (data-processor)**: Processes SQS messages and sends email recommendations

### Data Storage
- **DynamoDB**: Complete restaurant information (name, address, rating, etc.)

### AWS Services
- **SQS**: Queue for restaurant requests with Dead Letter Queue
- **SES**: Email service for restaurant recommendations
- **Lex**: Conversational AI bot with 3 intents
- **API Gateway**: REST API with CORS support
- **EventBridge**: Triggers data processor every minute

## Data Collection

The application collects **1000+ Manhattan restaurants** across **15+ cuisine types**:

- Italian, Chinese, Japanese, Mexican, Indian
- Thai, French, American, Mediterranean, Korean
- Vietnamese, Spanish, Greek, Lebanese, Ethiopian

Each cuisine type has **200+ restaurants** with complete information including ratings, reviews, addresses, and contact details.

## Example Interaction

```
User: Hi
Bot: Hello! I’m your personal dining concierge. Where would you like to eat today?

User: I need restaurant suggestions
Bot: What city would you like to dine in?

User: San Francisco
Bot: Great! What kind of cuisine are you in the mood for?

User: Italian
Bot: Sounds delicious! What time would you like to dine?

User: 8:30 PM
Bot: How many people will be joining you?

User: 4
Bot: Got it. What email address should I send the restaurant recommendations to?

User: dinewithme@example.com

Bot: Perfect! I’ll send you a list of top Italian restaurants in San Francisco for 4 people at 8:30 PM. Check your inbox at dinewithme@example.com
 soon. Enjoy your meal!

User: Thanks!
Bot: My pleasure! Would you like me to make a reservation for you as well?
```

**Email Received:**
```
Hello!

Here are your personalized restaurant recommendations:

Cuisine: Italian
Location: San Francisco
Dining Time: 8:30 PM
Party Size: 4

Restaurant Recommendations:

Acquerello
Address: 1722 Sacramento St
Rating: 4.7/5 (900 reviews)
Phone: (415) 567-5432

Flour + Water
Address: 2401 Harrison St
Rating: 4.5/5 (1,200 reviews)
Phone: (415) 826-7000

A16
Address: 2355 Chestnut St
Rating: 4.4/5 (1,000 reviews)
Phone: (415) 771-2216

Enjoy your meal!

Best regards,
Your Dining Concierge
```

## Cleanup

To remove all AWS resources:
```bash
python other-scripts/cleanup/cleanup.py
```

## Documentation

- **[Complete Setup Guide](docs/SETUP_GUIDE.md)** - Detailed setup instructions
- **[Frontend Documentation](frontend/README.md)** - Web app details
- **[Lambda Functions](lambda-functions/README.md)** - Serverless functions
- **[Scripts Documentation](other-scripts/README.md)** - Utility scripts

## Assignment Details

**Course**: Cloud Computing and Big Data - Fall 2025  
**Assignment**: Homework Assignment 1  
**Student**: Kathan Gabani kdg7224 
             Dheeraj Pakala dp4086  

### Submission Checklist
- ✅ Complete GitHub Repository with complete code
- ✅ All AWS resources properly configured
- ✅ Frontend deployed and accessible
- ✅ Complete data collection (1000+ restaurants)
- ✅ All Lambda functions working
- ✅ Email notifications functional
- ✅ Dead Letter Queue implemented (Extra Credit)
- ✅ Demo video recorded
- ✅ GitHub Release created

## Contributing

This is an academic project. For questions or issues:
1. Check the troubleshooting section in the setup guide
2. Review CloudWatch Logs for debugging
3. Verify all environment variables are set correctly

## License

This project is for educational purposes as part of CS-GY 9223 Fall 2025.

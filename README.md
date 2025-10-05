# 🍽️ Serverless Lex Concierge

A professional, serverless, microservice-driven web application that provides restaurant recommendations through conversational AI using Amazon Lex.

## 🎯 Project Overview

This project implements a **Dining Concierge chatbot** that collects user preferences through natural conversation and provides personalized restaurant suggestions from a curated database of 1000+ Manhattan restaurants. Built for **Cloud Computing and Big Data - Fall 2025** assignment.

### ✨ Key Features

- **🤖 Conversational AI**: Amazon Lex bot with 3 intents (Greeting, Thank You, Dining Suggestions)
- **📱 Modern Frontend**: Beautiful React application with real-time chat interface
- **☁️ Serverless Architecture**: Fully serverless with AWS Lambda, API Gateway, and S3
- **📊 Data Pipeline**: Yelp API → DynamoDB → ElasticSearch for fast restaurant search
- **📧 Email Notifications**: Automated restaurant recommendations via SES
- **🔄 Queue Processing**: SQS with Dead Letter Queue for reliable message handling
- **📈 Monitoring**: CloudWatch integration for logging and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │────│   API Gateway    │────│  Chat API (LF0) │
│   (S3 Hosted)    │    │   (CORS Enabled) │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Email (SES)   │◄───│ Suggestions      │◄───│   Lex Bot       │
│   Notifications │    │ Worker (LF2)     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   DynamoDB      │    │   SQS Queue      │    │  Lex Hook (LF1) │
│   (Restaurant   │    │   (with DLQ)     │    │                 │
│    Details)     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  ElasticSearch   │
                       │  (Restaurant IDs │
                       │   & Cuisines)    │
                       └──────────────────┘
```

## 📁 Repository Structure

```
serverless-lex-concierge/
├── frontend/                    # React frontend application
│   ├── src/                    # Source code
│   ├── public/                 # Static assets
│   ├── package.json            # Dependencies
│   └── README.md               # Frontend documentation
├── lambda-functions/           # AWS Lambda functions
│   ├── chat-api/              # LF0: Chat API Lambda
│   ├── lex-hook/              # LF1: Lex code hook Lambda
│   ├── data-processor/         # LF2: Suggestions worker Lambda
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

## ✅ Assignment Requirements

| Requirement | Points | Status | Description |
|-------------|--------|--------|-------------|
| **Frontend Deployment** | 10 | ✅ | React app hosted on S3 with modern UI |
| **API Development** | 15 | ✅ | API Gateway + Lambda with CORS |
| **Lex Chatbot** | 20 | ✅ | 3 intents with conversation flow |
| **API Integration** | 10 | ✅ | Lex integration with API Gateway |
| **Yelp Data Collection** | 15 | ✅ | 1000+ Manhattan restaurants |
| **ElasticSearch Setup** | 15 | ✅ | Search infrastructure |
| **Suggestions Module** | 15 | ✅ | Decoupled queue worker |
| **Extra Credit (DLQ)** | 10 | ✅ | Dead Letter Queue implementation |

## 🚀 Quick Start

### Prerequisites

- **AWS Account** with appropriate permissions
- **Python 3.9+** installed
- **Node.js 16+** and npm installed
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
   git clone <your-repo-url>
   cd serverless-lex-concierge
   cp env.example .env
   # Edit .env with your values
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install && cd ..
   ```

3. **Setup AWS Infrastructure**
   ```bash
   python other-scripts/deployment/infrastructure_setup.py
   ```

4. **Collect Restaurant Data**
   ```bash
   python other-scripts/yelp-scraper/yelp_scraper.py
   python other-scripts/yelp-scraper/elasticsearch_setup.py
   ```

5. **Deploy Application**
   ```bash
   python other-scripts/deployment/deploy.py
   ```

6. **Build and Deploy Frontend**
   ```bash
   cd frontend && npm run build && cd ..
   python other-scripts/deployment/deploy.py
   ```

## 🧪 Testing

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

## 🔧 Components

### Lambda Functions
- **LF0 (chat-api)**: Handles API requests and integrates with Lex
- **LF1 (lex-hook)**: Lex code hook for intent processing and SQS integration
- **LF2 (suggestions-worker)**: Processes SQS messages and sends email recommendations

### Data Storage
- **DynamoDB**: Complete restaurant information (name, address, rating, etc.)
- **ElasticSearch**: Restaurant IDs and cuisines for fast search

### AWS Services
- **SQS**: Queue for restaurant requests with Dead Letter Queue
- **SES**: Email service for restaurant recommendations
- **Lex**: Conversational AI bot with 3 intents
- **API Gateway**: REST API with CORS support
- **EventBridge**: Triggers suggestions worker every minute

## 📊 Data Collection

The application collects **1000+ Manhattan restaurants** across **15+ cuisine types**:

- Italian, Chinese, Japanese, Mexican, Indian
- Thai, French, American, Mediterranean, Korean
- Vietnamese, Spanish, Greek, Lebanese, Ethiopian

Each cuisine type has **200+ restaurants** with complete information including ratings, reviews, addresses, and contact details.

## 🎯 Example Interaction

```
User: Hello
Bot: Hi there! I'm your dining concierge. I can help you find great restaurants in Manhattan. What kind of cuisine are you in the mood for?

User: I need some restaurant suggestions.
Bot: Great! I can help you with that. What city or city area are you looking to dine in?

User: Manhattan
Bot: Got it, Manhattan. What cuisine would you like to try?

User: Japanese
Bot: Ok, how many people are in your party?

User: Two
Bot: A few more to go. What date?

User: Today
Bot: What time?

User: 7 pm, please
Bot: Great. Lastly, I need your email address so I can send you my findings.

User: user@example.com
Bot: You're all set! Expect my suggestions shortly! Have a good day.

User: Thank you!
Bot: You're welcome!
```

**Email Received:**
```
Hello!

Here are your personalized restaurant recommendations:

Cuisine: Japanese
Location: Manhattan
Dining Time: 7 pm
Party Size: Two

Restaurant Recommendations:

1. Sushi Nakazawa
   Address: 23 Commerce St
   Rating: 4.5/5 (1200 reviews)
   Phone: (212) 924-2212

2. Jin Ramen
   Address: 3183 Broadway
   Rating: 4.2/5 (800 reviews)
   Phone: (212) 666-6666

3. Nikko
   Address: 1280 Amsterdam Ave
   Rating: 4.3/5 (650 reviews)
   Phone: (212) 666-6667

Enjoy your meal!

Best regards,
Your Dining Concierge
```

## 🧹 Cleanup

To remove all AWS resources:
```bash
python other-scripts/cleanup/cleanup.py
```

## 📚 Documentation

- **[Complete Setup Guide](docs/SETUP_GUIDE.md)** - Detailed setup instructions
- **[Frontend Documentation](frontend/README.md)** - React app details
- **[Lambda Functions](lambda-functions/README.md)** - Serverless functions
- **[Scripts Documentation](other-scripts/README.md)** - Utility scripts

## 🎓 Assignment Details

**Course**: Cloud Computing and Big Data - Fall 2025  
**Assignment**: Homework Assignment 1  
**Student**: [Your Name] - [Your NYU NetID]  

### Submission Checklist
- ✅ GitHub Repository with complete code
- ✅ All AWS resources properly configured
- ✅ Frontend deployed and accessible
- ✅ Complete data collection (1000+ restaurants)
- ✅ All Lambda functions working
- ✅ Email notifications functional
- ✅ Dead Letter Queue implemented (Extra Credit)
- ✅ Demo video recorded
- ✅ GitHub Release created

## 🤝 Contributing

This is an academic project. For questions or issues:
1. Check the troubleshooting section in the setup guide
2. Review CloudWatch Logs for debugging
3. Verify all environment variables are set correctly

## 📄 License

This project is for educational purposes as part of CS-GY 9223 Fall 2025.

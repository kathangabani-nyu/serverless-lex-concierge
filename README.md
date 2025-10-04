# Serverless Lex Concierge

A serverless, microservice-driven web application that provides restaurant recommendations through conversational AI using Amazon Lex.

## Project Overview

This project implements a Dining Concierge chatbot that collects user preferences through conversation and provides restaurant suggestions from a curated database of Manhattan restaurants.

## Architecture

- **Frontend**: React-based web application hosted on AWS S3
- **API**: AWS API Gateway with Lambda functions
- **Chatbot**: Amazon Lex with custom Lambda code hooks
- **Data Storage**: DynamoDB for restaurant data, ElasticSearch for search
- **Data Source**: Yelp API for restaurant information

## Repository Structure

```
serverless-lex-concierge/
├── frontend/                 # React frontend application
├── lambda-functions/         # AWS Lambda functions
│   ├── chat-api/            # LF0: Chat API Lambda
│   ├── lex-hook/            # LF1: Lex code hook Lambda
│   └── data-processor/      # Restaurant data processing Lambda
├── other-scripts/           # Utility scripts
│   ├── yelp-scraper/       # Yelp API data collection
│   ├── deployment/         # Deployment scripts
│   └── cleanup/            # Resource cleanup scripts
├── docs/                   # Documentation
└── README.md
```

## Assignment Requirements

1. ✅ **Frontend Deployment** (10 pts) - React app on S3
2. ✅ **API Development** (15 pts) - API Gateway + Lambda
3. ✅ **Lex Chatbot** (20 pts) - Conversational AI with 3 intents
4. ✅ **API Integration** (10 pts) - Lex integration with API
5. ✅ **Yelp Data Collection** (15 pts) - 1000+ Manhattan restaurants
6. ✅ **ElasticSearch Setup** (15 pts) - Search infrastructure

## Getting Started

### Prerequisites

- AWS Account with appropriate permissions
- Node.js and npm
- Python 3.x
- Git

### Setup Instructions

1. Clone the repository
2. Set up AWS credentials
3. Deploy infrastructure using provided scripts
4. Run data collection scripts
5. Deploy frontend to S3

## Team

- [Your Name] - [Your NYU NetID]

## Submission

- GitHub Repository: [serverless-lex-concierge](https://github.com/[your-username]/serverless-lex-concierge)
- Demo Video: [Video URL]
- Release: [Release URL]

## License

This project is for educational purposes as part of CS-GY 9223 Fall 2025.

# Frontend Application - Starter Template

This is the official frontend starter application for the Dining Concierge chatbot, repurposed from the provided template.

## Overview

This frontend application provides a clean, responsive chat interface for interacting with the Dining Concierge chatbot. It uses the provided HTML/CSS/JavaScript template and integrates with the API Gateway SDK.

## Features

- **Clean Chat Interface**: Bootstrap-based responsive design
- **Real-time Messaging**: Instant message sending and receiving
- **API Gateway Integration**: Uses generated SDK for secure API calls
- **Session Management**: Maintains conversation state
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **HTML5**: Semantic markup structure
- **CSS3**: Bootstrap framework with custom styling
- **JavaScript**: jQuery-based interactive functionality
- **AWS SDK**: Generated API Gateway SDK for secure calls
- **Bootstrap**: Responsive UI framework

## Project Structure

```
frontend/
├── chat.html              # Main chat interface
├── assets/
│   ├── css/              # Stylesheets
│   │   ├── bootstrap.min.css
│   │   ├── chat.css
│   │   ├── cover.css
│   │   └── main.css
│   └── js/               # JavaScript files
│       ├── aws-sdk.min.js
│       ├── chat.js       # Main chat functionality
│       └── sdk/          # Generated API Gateway SDK
│           ├── apigClient.js
│           └── lib/      # SDK dependencies
└── README.md             # This file
```

## API Integration

The frontend integrates with the backend through the API Gateway SDK:

```javascript
// API call structure
var sdk = apigClientFactory.newClient({});

// Send message to chatbot
sdk.chatbotPost({}, {
  messages: [{
    type: 'unstructured',
    unstructured: {
      text: message
    }
  }]
}, {});
```

## Setup Instructions

1. **Deploy to S3**: Upload all files to an S3 bucket configured for static website hosting
2. **Configure SDK**: Update the API Gateway endpoint in the generated SDK
3. **Enable CORS**: Ensure API Gateway has proper CORS configuration
4. **Test Integration**: Verify the chat interface connects to the backend

## Deployment

### S3 Static Website Hosting

1. **Create S3 Bucket**:
   ```bash
   aws s3 mb s3://your-frontend-bucket-name
   ```

2. **Upload Files**:
   ```bash
   aws s3 sync . s3://your-frontend-bucket-name --delete
   ```

3. **Enable Static Website Hosting**:
   ```bash
   aws s3 website s3://your-frontend-bucket-name --index-document chat.html
   ```

4. **Configure Bucket Policy**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::your-frontend-bucket-name/*"
       }
     ]
   }
   ```

## Customization

### Styling
- Modify `assets/css/chat.css` for chat-specific styling
- Update `assets/css/main.css` for general layout changes
- Customize Bootstrap variables in `assets/css/bootstrap.min.css`

### Functionality
- Edit `assets/js/chat.js` for chat behavior
- Modify `chat.html` for layout changes
- Update SDK configuration for API endpoint changes

## API Specification Compliance

This frontend follows the provided Swagger specification:

- **Endpoint**: `/v1/chatbot`
- **Method**: POST
- **Request Format**: 
  ```json
  {
    "messages": [{
      "type": "unstructured",
      "unstructured": {
        "text": "user message"
      }
    }]
  }
  ```
- **Response Format**:
  ```json
  {
    "messages": [{
      "type": "unstructured",
      "unstructured": {
        "id": "uuid",
        "text": "bot response",
        "timestamp": "ISO datetime"
      }
    }]
  }
  ```

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Verify API Gateway CORS configuration
   - Check browser console for specific error messages

2. **SDK Connection Issues**:
   - Confirm API Gateway endpoint URL
   - Verify SDK is properly generated and uploaded

3. **Styling Issues**:
   - Check CSS file loading order
   - Verify Bootstrap dependencies

### Debug Mode

Enable debug logging in browser console:
```javascript
// Add to chat.js for debugging
console.log('API Response:', response);
console.log('Error Details:', error);
```

## License

This project is for educational purposes as part of CS-GY 9223 Fall 2025.
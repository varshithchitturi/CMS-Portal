# API Documentation for P-004 Complaint Management System

## Overview
This document provides comprehensive API documentation for the P-004 Complaint Management System with AI Chatbot Integration.

## System Architecture
- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python Flask
- **AI Engine**: Google Gemini 2.0 Flash
- **Database**: SQLite
- **ML Components**: Scikit-learn for complaint categorization

## Gemini API Integration

### Configuration
```python
import google.generativeai as genai
genai.configure(api_key="AIzaSyAS0gSykyuzXdnLDvgPdLGP6_pdviK3l14")
model = genai.GenerativeModel("gemini-2.0-flash-exp")
```

### API Endpoints

#### 1. Notifications API

**Endpoints**:

**Get User Notifications**  
`GET /api/notifications`  
Gets notifications for the current authenticated user.

Query Parameters:
- `limit` (optional): Maximum number of notifications to return (default: 20)
- `unread` (optional): Boolean, set to true to only get unread notifications

Response Format:
```json
{
    "notifications": [
        {
            "id": "notification-uuid",
            "title": "Notification title",
            "message": "Notification message content",
            "type": "info|success|warning|danger",
            "read": false,
            "time": "15 minutes ago"
        }
    ],
    "unread_count": 5
}
```

**Get Unread Count**  
`GET /api/notifications/unread-count`  
Gets the number of unread notifications for the current user.

Response Format:
```json
{
    "count": 5
}
```

**Mark as Read**  
`PUT /api/notifications/{notification_id}/read`  
Marks a specific notification as read.

Response Format:
```json
{
    "success": true
}
```

**Mark All as Read**  
`PUT /api/notifications/mark-all-read`  
Marks all notifications as read for the current user.

Response Format:
```json
{
    "success": true
}
```

**Delete Notification**  
`DELETE /api/notifications/{notification_id}`  
Deletes a specific notification.

Response Format:
```json
{
    "success": true
}
```

#### 2. Chat with AI Assistant
**Endpoint**: `POST /ask`
**Purpose**: Send user messages to AI chatbot for complaint processing

**Request Format**:
```json
{
    "message": "string - User's complaint or question"
}
```

**Response Format**:
```json
{
    "reply": "string - AI generated response",
    "requires_ticket": "boolean - Whether ticket creation is needed",
    "session_id": "string - Chat session identifier",
    "show_ticket_button": "boolean - Show ticket creation option"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:5000/ask \
  -H 'Content-Type: application/json' \
  -H 'Cookie: session=<session_cookie>' \
  -d '{
    "message": "My internet connection is very slow and keeps disconnecting"
  }'
```

#### 2. Create Support Ticket
**Endpoint**: `POST /create_ticket`
**Purpose**: Generate support ticket from chat conversation

**Request Format**:
```json
{
    "message": "string - Final user message that requires ticket"
}
```

**Response Format**:
```json
{
    "success": "boolean",
    "ticket_id": "string - Generated ticket ID",
    "category": "string - AI determined category",
    "priority": "string - AI determined priority",
    "message": "string - Confirmation message"
}
```

#### 3. User Authentication
**Login Endpoint**: `POST /login`
```json
{
    "username": "string",
    "password": "string"
}
```

**Registration Endpoint**: `POST /register`
```json
{
    "username": "string",
    "email": "string",
    "password": "string",
    "full_name": "string",
    "phone": "string (optional)"
}
```

#### 4. Admin Operations
**Update Ticket**: `POST /admin/update_ticket`
```json
{
    "ticket_id": "string",
    "status": "string - New status",
    "assigned_to": "string - Team member",
    "resolution_notes": "string - Resolution details"
}
```

## Gemini AI Prompt Engineering

### System Prompt Structure
```
You are an intelligent complaint management assistant for P-004 system.

CAPABILITIES:
1. Analyze user complaints for sentiment and urgency
2. Provide instant solutions for common issues
3. Categorize complaints: Technical, Billing, Service, Product, General
4. Assign priority: Critical, High, Medium, Low
5. Generate structured ticket information

WORKFLOW:
1. Greet user professionally
2. Listen to complaint details
3. Attempt instant resolution for common issues
4. If unresolved, categorize and prioritize
5. Create ticket with detailed information
6. Provide estimated resolution time
```

### AI Decision Making Process

#### Category Classification:
- **Technical**: Login issues, system errors, connectivity problems
- **Billing**: Payment issues, incorrect charges, refund requests
- **Service**: Customer service complaints, staff behavior
- **Product**: Product defects, missing features, quality issues
- **General**: Information requests, how-to questions

#### Priority Assignment Logic:
- **Critical**: Service outages, security breaches, payment failures
- **High**: Login issues, billing errors, urgent requests
- **Medium**: General complaints, feature requests
- **Low**: Information requests, minor issues

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE
);
```

### Complaints Table
```sql
CREATE TABLE complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT DEFAULT 'Registered',
    assigned_to TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    estimated_resolution_time TEXT
);
```

### Chat History Table
```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_id TEXT,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Machine Learning Components

### Complaint Categorization Model
- **Algorithm**: Naive Bayes with TF-IDF vectorization
- **Training Data**: Predefined complaint samples
- **Features**: Text content, keywords, sentiment
- **Accuracy**: Continuously improved through user feedback

### Text Processing Pipeline
1. **Preprocessing**: Remove stop words, tokenization
2. **Feature Extraction**: TF-IDF vectorization
3. **Classification**: Multinomial Naive Bayes
4. **Post-processing**: Confidence scoring and fallback rules

## API Rate Limits and Security

### Rate Limiting
- Chat API: 100 requests per minute per user
- Ticket Creation: 10 tickets per hour per user
- Admin API: No limits for authenticated admins

### Security Features
- Session-based authentication
- Password hashing with SHA-256
- SQL injection prevention
- XSS protection
- CSRF token validation

## Integration Examples

### Direct Gemini API Call
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" \
  -H 'Content-Type: application/json' \
  -H 'X-goog-api-key: AIzaSyAS0gSykyuzXdnLDvgPdLGP6_pdviK3l14' \
  -X POST \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "Categorize this complaint and assign priority: My account was charged twice for the same service"
          }
        ]
      }
    ]
  }'
```

### Python Integration Example
```python
import google.generativeai as genai

genai.configure(api_key="AIzaSyAS0gSykyuzXdnLDvgPdLGP6_pdviK3l14")
model = genai.GenerativeModel("gemini-2.0-flash-exp")

response = model.generate_content(
    "Analyze this complaint: 'The website keeps crashing when I try to make a payment'"
)
print(response.text)
```

## Error Handling

### Common Error Responses
```json
{
    "error": "Authentication required",
    "code": 401
}

{
    "error": "Invalid input data",
    "code": 400,
    "details": "Missing required field: message"
}

{
    "error": "Rate limit exceeded",
    "code": 429,
    "retry_after": 60
}
```

## Performance Metrics

### Response Times (Target)
- Chat Response: < 2 seconds
- Ticket Creation: < 3 seconds
- Dashboard Load: < 1 second
- Admin Operations: < 2 seconds

### System Capabilities
- Concurrent Users: 1000+
- Daily Tickets: 10,000+
- Chat Sessions: 50,000+
- Database Queries: 100,000+

## Deployment Configuration

### Environment Variables
```env
GEMINI_API_KEY=AIzaSyAS0gSykyuzXdnLDvgPdLGP6_pdviK3l14
SECRET_KEY=P-004-complaint-management-secret-key
DATABASE_URL=sqlite:///complaints.db
FLASK_ENV=production
```

### Default Admin Credentials
- **Username**: admin
- **Password**: admin123
- **Note**: Change password immediately after first login

## API Testing

### Test Cases
1. **User Registration**: Verify account creation and validation
2. **AI Chat**: Test complaint processing and response quality
3. **Ticket Generation**: Verify automatic categorization and priority
4. **Admin Functions**: Test ticket management and reporting
5. **Error Handling**: Verify appropriate error responses

### Sample Test Data
```json
{
    "test_complaints": [
        {
            "message": "I cannot log into my account",
            "expected_category": "Technical",
            "expected_priority": "High"
        },
        {
            "message": "Wrong amount charged on my bill",
            "expected_category": "Billing",
            "expected_priority": "High"
        }
    ]
}
```

## Maintenance and Monitoring

### Log Files
- Application logs: `app.log`
- Error logs: `error.log`
- Access logs: `access.log`
- AI interaction logs: `ai_chat.log`

### Monitoring Endpoints
- Health Check: `GET /health`
- System Stats: `GET /api/stats` (Admin only)
- Performance Metrics: `GET /api/metrics` (Admin only)

## Support and Documentation

### Contact Information
- Technical Support: tech@p004-system.com
- API Documentation: https://docs.p004-system.com
- Issue Tracking: https://github.com/p004-system/issues

### Version Information
- System Version: 1.0.0
- API Version: v1
- Gemini Model: gemini-2.0-flash-exp
- Last Updated: August 6, 2025

---

**Note**: This system implements advanced AI-powered complaint management with real-time processing, intelligent categorization, and automated ticket generation. All API interactions are logged for quality assurance and system improvement.

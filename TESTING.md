# ChatBoard API Testing Guide

## 🚀 Quick Start

Your ChatBoard application is running at: **http://localhost:8000**

All services are healthy:
- ✅ Database (PostgreSQL): localhost:55432
- ✅ Redis: localhost:6379
- ✅ Web App: localhost:8000
- ✅ Celery Worker: Running
- ✅ Celery Beat: Running

---

## 📋 API Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **API Schema**: http://localhost:8000/api/schema/
- **Admin Panel**: http://localhost:8000/admin/

---

## 🔐 Step 1: User Authentication

### 1.1 User Registration
```bash
POST http://localhost:8000/api/v1/auth/register/
Content-Type: application/json

{
    "email": "test@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
}
```

**Expected Response:**
```json
{
    "id": 5,
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "avatar_url": null
}
```

### 1.2 User Login
```bash
POST http://localhost:8000/api/v1/auth/token/
Content-Type: application/json

{
    "email": "test@example.com",
    "password": "testpass123"
}
```

**Expected Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 1.3 Get User Profile
```bash
GET http://localhost:8000/api/v1/auth/me/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## 🏢 Step 2: Organization Management

### 2.1 Create Organization
```bash
POST http://localhost:8000/api/v1/orgs/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "name": "My Test Organization"
}
```

**Expected Response:**
```json
{
    "id": 1,
    "name": "My Test Organization",
    "created_at": "2025-10-21T15:30:00Z"
}
```

### 2.2 List User's Organizations
```bash
GET http://localhost:8000/orgs/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 2.3 Get Organization Details
```bash
GET http://localhost:8000/orgs/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 2.4 List Organization Members
```bash
GET http://localhost:8000/orgs/1/members/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 2.5 Invite User to Organization
```bash
POST http://localhost:8000/orgs/1/invite/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "email": "newuser@example.com",
    "role": "MEMBER"
}
```

**Expected Response:**
```json
{
    "id": 1,
    "token": "invite_token_here",
    "email": "newuser@example.com",
    "role": "MEMBER"
}
```

### 2.6 Accept Organization Invite
```bash
POST http://localhost:8000/orgs/accept-invite/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "token": "invite_token_here"
}
```

---

## 💬 Step 3: Chat Rooms

### 3.1 Create Chat Room
```bash
POST http://localhost:8000/rooms/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "name": "General Chat",
    "description": "General discussion room",
    "org": 1
}
```

**Expected Response:**
```json
{
    "id": 1,
    "name": "General Chat",
    "description": "General discussion room",
    "org": 1,
    "created_at": "2025-10-21T15:30:00Z",
    "created_by": 1
}
```

### 3.2 List Organization Rooms
```bash
GET http://localhost:8000/rooms/?org=1
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 3.3 Get Room Details
```bash
GET http://localhost:8000/rooms/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 3.4 Join Room
```bash
POST http://localhost:8000/rooms/1/join/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## 📨 Step 4: Messaging

### 4.1 Send Message
```bash
POST http://localhost:8000/messages/rooms/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "body": "Hello everyone!",
    "message_type": "text"
}
```

**Expected Response:**
```json
{
    "id": 1,
    "room": 1,
    "sender": 1,
    "body": "Hello everyone!",
    "message_type": "text",
    "created_at": "2025-10-21T15:30:00Z"
}
```

### 4.2 Get Room Messages
```bash
GET http://localhost:8000/messages/rooms/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 4.3 Send Message with File
```bash
POST http://localhost:8000/messages/rooms/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "body": "Check out this file!",
    "message_type": "file",
    "file_url": "https://example.com/file.pdf"
}
```

---

## 📁 Step 5: File Uploads

### 5.1 Get Presigned Upload URL
```bash
POST http://localhost:8000/uploads/presign/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "filename": "document.pdf",
    "content_type": "application/pdf",
    "file_size": 1024000
}
```

**Expected Response:**
```json
{
    "upload_url": "https://s3.amazonaws.com/bucket/presigned-url",
    "file_url": "https://s3.amazonaws.com/bucket/file-path",
    "upload_id": "12345",
    "expires_in": 3600
}
```

### 5.2 List User's Uploads
```bash
GET http://localhost:8000/uploads/my-uploads/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## 🔗 Step 6: Webhooks

### 6.1 Create Webhook
```bash
POST http://localhost:8000/webhooks/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "org": 1,
    "url": "https://your-webhook-endpoint.com/webhook",
    "events": ["message.created", "room.created"]
}
```

### 6.2 List Organization Webhooks
```bash
GET http://localhost:8000/webhooks/?org=1
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 6.3 Test Webhook
```bash
POST http://localhost:8000/webhooks/1/test/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "test_data": {"message": "Test webhook"}
}
```

### 6.4 Get Webhook Events
```bash
GET http://localhost:8000/webhooks/1/events/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## 🧪 Testing Tools

### Using cURL
```bash
# Example: Register a user
curl -X POST http://localhost:8000/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "first_name": "Test", "last_name": "User"}'
```

### Using Postman
1. Import the API collection from Swagger: http://localhost:8000/api/docs/
2. Set base URL: `http://localhost:8000`
3. Add Authorization header: `Bearer YOUR_TOKEN`

### Using Python requests
```python
import requests

# Register user
response = requests.post('http://localhost:8000/auth/register/', json={
    'email': 'test@example.com',
    'password': 'testpass123',
    'first_name': 'Test',
    'last_name': 'User'
})

# Get access token
access_token = response.json()['tokens']['access']

# Use token for authenticated requests
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get('http://localhost:8000/orgs/', headers=headers)
```

---

## 🔍 WebSocket Testing (Real-time Chat)

### Using JavaScript in Browser Console
```javascript
// Connect to WebSocket
const socket = new WebSocket('ws://localhost:8000/ws/chat/1/');

socket.onopen = function(e) {
    console.log('Connected to chat room 1');
};

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log('Received message:', data);
};

// Send a message
socket.send(JSON.stringify({
    'type': 'chat_message',
    'message': 'Hello from WebSocket!',
    'room_id': 1
}));
```

---

## 📊 Expected Test Flow

1. **Register/Login** → Get access token
2. **Create Organization** → Get org ID
3. **Create Chat Room** → Get room ID
4. **Send Messages** → Test messaging
5. **Upload Files** → Test file handling
6. **Test WebSocket** → Real-time chat
7. **Test Webhooks** → External integrations

---

## 🐛 Common Issues & Solutions

### Issue: 401 Unauthorized
**Solution**: Make sure you're including the `Authorization: Bearer TOKEN` header

### Issue: 403 Forbidden
**Solution**: Check if you have the right permissions for the organization/room

### Issue: 404 Not Found
**Solution**: Verify the API endpoint URL and that the resource exists

### Issue: WebSocket Connection Failed
**Solution**: Make sure the room exists and you're a member

---

## 📈 Performance Testing

### Load Testing with Apache Bench
```bash
# Test registration endpoint
ab -n 100 -c 10 -H "Content-Type: application/json" -p register.json http://localhost:8000/api/v1/auth/register/
```

### Database Connection Test
```bash
# Check database health
curl http://localhost:8000/health/live
```

---

## 🎯 Success Criteria

✅ **Authentication**: Users can register, login, and get tokens  
✅ **Organizations**: Users can create and manage organizations  
✅ **Chat Rooms**: Users can create rooms and send messages  
✅ **File Uploads**: Users can upload and share files  
✅ **Real-time**: WebSocket messages work in real-time  
✅ **Webhooks**: External integrations work properly  

---

## 📝 Notes

- All timestamps are in UTC
- JWT tokens expire after 15 minutes (access) and 7 days (refresh)
- File uploads expire after 30 days
- WebSocket connections require authentication
- Rate limiting: 100 requests per minute per user

**Happy Testing! 🚀**

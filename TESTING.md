# ChatBoard API Testing Guide

## 🔐 Role-Based Access Control

**Organization Roles:**
- 👑 **ADMIN** - Full control over organization, can manage everything
- 🛡️ **MANAGER** - Can create rooms, invite users, manage members
- 👤 **MEMBER** - Basic access, can join rooms and send messages

**Room Roles:**
- 🏠 **Room MEMBER** - Can view room, send messages, see members

**Authentication:**
- 🔑 **Any authenticated user** - Just needs valid JWT token
- 📧 **Email match required** - User's email must match invited email

**✨ Room Access Levels:**
- **PUBLIC** (default) → All org members auto-join when room is created **OR when they join the org**
- **MANAGER_ONLY** → Only managers/admins auto-join when room is created **OR when they join the org**
- **PRIVATE** → No one auto-joins, requires invite or manual join
- Users can only join rooms in organizations they belong to

---

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
**🔐 Required Role:** Any authenticated user

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
**🔐 Required Role:** Any authenticated user (becomes ADMIN automatically)

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
GET http://localhost:8000/api/v1/orgs/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Any authenticated user

### 2.3 Get Organization Details
```bash
GET http://localhost:8000/api/v1/orgs/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Organization MEMBER, MANAGER, or ADMIN

### 2.4 List Organization Members
```bash
GET http://localhost:8000/api/v1/orgs/1/members/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Organization MEMBER, MANAGER, or ADMIN

**Expected Response:**
```json
[
    {
        "id": 1,
        "org": 1,
        "user": 1,
        "user_email": "admin@example.com",
        "user_first_name": "John",
        "user_last_name": "Admin",
        "role": "ADMIN",
        "joined_at": "2025-10-21T15:30:00Z"
    },
    {
        "id": 2,
        "org": 1,
        "user": 2,
        "user_email": "manager@example.com",
        "user_first_name": "Jane",
        "user_last_name": "Manager",
        "role": "MANAGER",
        "joined_at": "2025-10-21T16:00:00Z"
    },
    {
        "id": 3,
        "org": 1,
        "user": 3,
        "user_email": "member@example.com",
        "user_first_name": "Bob",
        "user_last_name": "Member",
        "role": "MEMBER",
        "joined_at": "2025-10-21T17:00:00Z"
    }
]
```

### 2.5 Invite User to Organization
```bash
POST http://localhost:8000/api/v1/orgs/1/invite/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "email": "newuser@example.com",
    "role": "MEMBER"
}
```
**🔐 Required Role:** Organization MANAGER or ADMIN

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
POST http://localhost:8000/api/v1/orgs/accept-invite/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "token": "invite_token_here"
}
```
**🔐 Required Role:** Any authenticated user (invited email must match user's email)

**Expected Response:**
```json
{
    "detail": "Joined",
    "org_id": 1,
    "role": "MEMBER"
}
```

✨ **Auto-Join Feature:** When you join an organization, you automatically join all existing PUBLIC rooms and MANAGER_ONLY rooms (if you're a manager/admin)!

---

## 💬 Step 3: Chat Rooms

### 3.1 Create Chat Room
```bash
POST http://localhost:8000/api/v1/rooms/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "name": "General Chat",
    "org": 1,
    "access_level": "PUBLIC"
}
```
**🔐 Required Role:** Organization MANAGER or ADMIN

**Required Fields:**
- `name` - Room name
- `org` - Organization ID

**Optional Fields:**
- `access_level` - `"PUBLIC"` (default), `"PRIVATE"`, or `"MANAGER_ONLY"`
- `is_dm` - Boolean, default `false`

✨ **Auto-Join Feature:** Members are automatically added based on `access_level`:
- `PUBLIC` → All org members join (existing members + future members)
- `MANAGER_ONLY` → Only managers/admins join (existing + future)
- `PRIVATE` → No one auto-joins, requires invite or manual join

**Expected Response:**
```json
{
    "id": 1,
    "name": "General Chat",
    "is_dm": false,
    "org": 1,
    "access_level": "PUBLIC",
    "created_at": "2025-10-21T15:30:00Z",
    "created_by": 1,
    "members_count": 1
}
```

### 3.2 List Your Rooms
```bash
GET http://localhost:8000/api/v1/rooms/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Any authenticated user (shows only rooms where user is a member)

### 3.3 Get Room Details
```bash
GET http://localhost:8000/api/v1/rooms/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Room MEMBER

### 3.4 Join Room
```bash
POST http://localhost:8000/api/v1/rooms/1/join/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Organization MEMBER (must be member of the room's organization)

**Expected Response:**
```json
{
    "detail": "Successfully joined the room"
}
```

### 3.5 Leave Room
```bash
POST http://localhost:8000/api/v1/rooms/1/leave/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Room MEMBER

**Expected Response:**
```json
{
    "detail": "Successfully left the room"
}
```

### 3.6 Invite User to Private Room
```bash
POST http://localhost:8000/api/v1/rooms/1/invite/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "user_id": 2
}
```
**🔐 Required Role:** Room creator or Organization ADMIN (only for PRIVATE rooms)

**Expected Response:**
```json
{
    "detail": "User successfully invited to the room"
}
```

### 3.7 List Room Members
```bash
GET http://localhost:8000/api/v1/rooms/1/members/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Room MEMBER

**Expected Response:**
```json
[
    {
        "id": 1,
        "room": 1,
        "user": 1,
        "user_email": "john@example.com",
        "user_first_name": "John",
        "user_last_name": "Doe",
        "org_role": "ADMIN",
        "last_read_msg_id": null,
        "joined_at": "2025-10-21T15:30:00Z"
    },
    {
        "id": 2,
        "room": 1,
        "user": 2,
        "user_email": "jane@example.com",
        "user_first_name": "Jane",
        "user_last_name": "Smith",
        "org_role": "MEMBER",
        "last_read_msg_id": 42,
        "joined_at": "2025-10-21T16:00:00Z"
    }
]
```

**Response Fields:**
- `id` - RoomMember ID
- `room` - Room ID
- `user` - User ID
- `user_email` - User's email address
- `user_first_name` - User's first name
- `user_last_name` - User's last name
- `org_role` - User's role in the organization (**ADMIN**, **MANAGER**, or **MEMBER**)
- `last_read_msg_id` - ID of last read message (null if none)
- `joined_at` - When user joined the room

---

## 📨 Step 4: Messaging

### 4.1 Send Message
```bash
POST http://localhost:8000/api/v1/messages/rooms/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "body": "Hello everyone!",
    "file_url": null
}
```
**🔐 Required Role:** Room MEMBER

**Expected Response:**
```json
{
    "id": 1,
    "org": 1,
    "room": 1,
    "sender": 1,
    "body": "Hello everyone!",
    "file_url": null,
    "is_deleted": false,
    "created_at": "2025-10-21T15:30:00Z"
}
```

### 4.2 Get Room Messages
```bash
GET http://localhost:8000/api/v1/messages/rooms/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Room MEMBER

**Response:** Paginated list of messages

### 4.3 Send Message with File
```bash
POST http://localhost:8000/api/v1/messages/rooms/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "body": "Check out this file!",
    "file_url": "https://your-s3-bucket.s3.amazonaws.com/uploads/file.pdf"
}
```
**🔐 Required Role:** Room MEMBER

**Note:** `file_url` can be from AWS S3 or local storage (`/media/uploads/...`)

---

## 📁 Step 5: File Uploads

The app supports two storage modes (configured via `USE_AWS_S3` environment variable):
- **Local Storage** (default, FREE) - Files stored on server
- **AWS S3** (requires AWS account) - Files stored in S3

### 5.1 Upload File (Local Storage)

**Option A: Using /direct/ endpoint (Recommended)**
```bash
POST http://localhost:8000/api/v1/uploads/direct/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data

Form Data:
- file: [your file]
- filename: "document.pdf"
```

**Option B: Using /presign/ endpoint**
```bash
POST http://localhost:8000/api/v1/uploads/presign/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data

Form Data:
- file: [your file]
- filename: "document.pdf"
```

**Expected Response (Local Storage):**
```json
{
    "upload_id": "12345",
    "file_url": "/media/uploads/user_id/filename.pdf",
    "message": "File uploaded successfully"
}
```

### 5.2 Get Presigned Upload URL (AWS S3)

For AWS S3, first get a presigned URL, then upload to S3:
```bash
POST http://localhost:8000/api/v1/uploads/presign/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "filename": "document.pdf",
    "content_type": "application/pdf",
    "file_size": 1024000
}
```
**🔐 Required Role:** Any authenticated user

**Expected Response (AWS S3):**
```json
{
    "upload_url": "https://s3.amazonaws.com/bucket/presigned-url",
    "file_url": "https://s3.amazonaws.com/bucket/file-path",
    "upload_id": "12345",
    "expires_in": 3600
}
```

Then upload your file to the `upload_url` using PUT method.

### 5.3 List User's Uploads
```bash
GET http://localhost:8000/api/v1/uploads/my-uploads/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Any authenticated user

---

## 🔗 Step 6: Webhooks

### 6.1 Create Webhook
```bash
POST http://localhost:8000/api/v1/webhooks/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "org": 1,
    "url": "https://your-webhook-endpoint.com/webhook",
    "events": ["message.created", "room.created"],
    "is_active": true
}
```
**🔐 Required Role:** Organization ADMIN

### 6.2 List Organization Webhooks
```bash
GET http://localhost:8000/api/v1/webhooks/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Organization ADMIN

### 6.3 Test Webhook
```bash
POST http://localhost:8000/api/v1/webhooks/1/test/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Organization ADMIN

**Expected Response:**
```json
{
    "detail": "Test webhook queued for delivery",
    "outbox_id": 1,
    "webhook_url": "https://your-webhook-endpoint.com/webhook"
}
```

### 6.4 List Webhook Events
```bash
GET http://localhost:8000/api/v1/webhooks/1/events/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Organization ADMIN

**Response:** List of webhook delivery attempts with status and retry information

---

## 🔔 Step 7: Notifications

### 7.1 List User Notifications
```bash
GET http://localhost:8000/api/v1/notifications/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Any authenticated user

### 7.2 Get Notification Details
```bash
GET http://localhost:8000/api/v1/notifications/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Any authenticated user (only own notifications)

### 7.3 Mark Notification as Read
```bash
PATCH http://localhost:8000/api/v1/notifications/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "is_read": true
}
```
**🔐 Required Role:** Any authenticated user (only own notifications)

### 7.4 Mark All Notifications as Read
```bash
POST http://localhost:8000/api/v1/notifications/mark-all-read/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Any authenticated user

### 7.5 Get Unread Count
```bash
GET http://localhost:8000/api/v1/notifications/unread-count/
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**🔐 Required Role:** Any authenticated user

**Expected Response:**
```json
{
    "unread_count": 5
}
```

---

## 🧪 Testing Tools

### Using cURL
```bash
# Example: Register a user
curl -X POST http://localhost:8000/api/v1/auth/register/ \
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
response = requests.post('http://localhost:8000/api/v1/auth/register/', json={
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
- JWT tokens expire after 6 days (access) and 7 days (refresh)
- File uploads expire after 30 days
- WebSocket connections require authentication
- Rate limiting: 100 requests per minute per user
- File storage defaults to local storage (FREE), configure AWS S3 via environment variables

**Happy Testing! 🚀**

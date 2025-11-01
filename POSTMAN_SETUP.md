# Postman Setup Guide for ChatBoard API

## Method 1: Import from OpenAPI Schema (Recommended) ✨

### Step 1: Get the OpenAPI Schema

With your Django server running (via `docker-compose up` or `python manage.py runserver`), visit:

```
http://127.0.0.1:8000/api/schema/
```

Or if using Docker:
```
http://localhost:8000/api/schema/
```

This will download a JSON/YAML file with all your API endpoints.

### Step 2: Import into Postman

1. Open Postman
2. Click **Import** button (top left)
3. Select **Link** tab
4. Enter: `http://127.0.0.1:8000/api/schema/`
5. Click **Continue** then **Import**

All your API endpoints will be imported with:
- ✅ Correct request methods (GET, POST, PUT, DELETE, etc.)
- ✅ Request parameters
- ✅ Request body schemas
- ✅ Authentication setup
- ✅ Example values

---

## Method 2: Manual Testing in Postman

### Basic Setup

**Base URL**: `http://127.0.0.1:8000` (or `http://localhost:8000` for Docker)

### Authentication Flow

#### 1. Register a User
```
POST http://127.0.0.1:8000/api/v1/auth/register/
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "securepass123"
}
```

#### 2. Get Access Token
```
POST http://127.0.0.1:8000/api/v1/auth/token/
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "securepass123"
}
```

**Response will contain:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 3. Set up Authentication in Postman

1. Go to **Collection Settings** (or individual request)
2. Under **Authorization** tab
3. Select **Bearer Token**
4. Paste your `access` token from step 2
5. Click **Update**

Now all requests in that collection will include: `Authorization: Bearer <token>`

---

## Key API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - Register new user
- `POST /api/v1/auth/token/` - Get JWT access token
- `POST /api/v1/auth/token/refresh/` - Refresh access token

### Organizations
- `GET /api/v1/orgs/` - List organizations (authenticated users)
- `POST /api/v1/orgs/` - Create organization
- `GET /api/v1/orgs/{id}/` - Get organization details
- `PUT /api/v1/orgs/{id}/` - Update organization
- `DELETE /api/v1/orgs/{id}/` - Delete organization
- `GET /api/v1/orgs/{id}/members/` - List organization members
- `POST /api/v1/orgs/{id}/invite/` - Invite user to organization
- `POST /api/v1/orgs/accept-invite/` - Accept organization invite

### Rooms
- `GET /api/v1/rooms/` - List rooms
- `POST /api/v1/rooms/` - Create room
- `GET /api/v1/rooms/{id}/` - Get room details
- `GET /api/v1/rooms/{id}/messages/` - Get messages in room

### Messages
- `POST /api/v1/messages/` - Send message
- `GET /api/v1/messages/{id}/` - Get message details

### Uploads
- `POST /api/v1/uploads/` - Upload file

### Webhooks
- `GET /api/v1/webhooks/` - List webhooks
- `POST /api/v1/webhooks/` - Create webhook

### Notifications
- `GET /api/v1/notifications/` - List notifications

---

## Quick Test Sequence

### 1. Register and Login
```bash
# Register
POST http://127.0.0.1:8000/api/v1/auth/register/
{
  "email": "user1@test.com",
  "password": "testpass123"
}

# Login
POST http://127.0.0.1:8000/api/v1/auth/token/
{
  "email": "user1@test.com",
  "password": "testpass123"
}

# Copy the "access" token for next steps
```

### 2. Set Authorization in Postman
- Add header: `Authorization: Bearer <your_access_token>`

### 3. Create Organization
```bash
POST http://127.0.0.1:8000/api/v1/orgs/
{
  "name": "My Test Organization"
}
```

### 4. Invite User to Organization
```bash
POST http://127.0.0.1:8000/api/v1/orgs/2/invite/
{
  "email": "invited@test.com",
  "role": "MEMBER"
}
```

### 5. List Organization Members
```bash
GET http://127.0.0.1:8000/api/v1/orgs/2/members/
```

---

## Tips for Postman

### Environment Variables
Create a Postman environment to store:
- `base_url`: `http://127.0.0.1:8000`
- `token`: Your JWT access token
- `org_id`: Current organization ID

Then use in requests:
- URL: `{{base_url}}/api/v1/orgs/{{org_id}}/`
- Authorization: `Bearer {{token}}`

### Pre-request Script (Auto-refresh Token)
Add this to your collection's pre-request script to auto-refresh expired tokens:

```javascript
// Auto-refresh token if expired
pm.sendRequest({
    url: pm.collectionVariables.get("refresh_url"),
    method: 'POST',
    header: {
        'Content-Type': 'application/json'
    },
    body: {
        mode: 'raw',
        raw: JSON.stringify({
            refresh: pm.collectionVariables.get("refresh_token")
        })
    }
}, function (err, res) {
    if (err) {
        console.log(err);
    } else {
        const json = res.json();
        pm.collectionVariables.set("token", json.access);
    }
});
```

### Common Headers
Add these default headers in collection settings:
- `Content-Type: application/json`
- `Accept: application/json`

---

## Interactive API Documentation

Visit in browser for interactive API docs:
```
http://127.0.0.1:8000/api/docs/
```

You can test endpoints directly in the browser!

---

## Troubleshooting

### 401 Unauthorized
- Make sure you've logged in and copied the access token
- Check if the token has expired (tokens expire after 6 days)
- Use the refresh endpoint to get a new access token

### 403 Forbidden
- User doesn't have permission for the requested action
- Check if user is a member/admin of the organization

### 404 Not Found
- Check if the endpoint URL is correct
- Ensure the API version is `v1` in the URL

### 500 Internal Server Error
- Check server logs in terminal
- Make sure all migrations are applied: `python manage.py migrate`
- Verify database connection


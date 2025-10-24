# ChatBoard — System Design (v2.0) 🚀

## 0) One-liner

**Production-ready enterprise chat platform** with real-time messaging, multi-tenant organizations, JWT auth, WebSocket integration, file uploads, webhooks, notifications, and comprehensive monitoring. Built with Django, Channels, Redis, Celery, and PostgreSQL.

---

## 1) Requirements

### **Functional Requirements**

#### **Core Features**
- ✅ **Authentication**: JWT with SimpleJWT (email login, refresh tokens)
- ✅ **Organizations**: Multi-tenant with roles (ADMIN, MANAGER, MEMBER)
- ✅ **Rooms**: Group chat with membership management
- ✅ **Messages**: Real-time with WebSocket fanout, pagination, file attachments
- ✅ **Unread Counts**: Per-room unread message tracking
- ✅ **Read Receipts**: Mark messages as read functionality
- ✅ **File Uploads**: Presigned S3 URLs with validation and cleanup
- ✅ **Webhooks**: HMAC-signed delivery with retry logic and outbox pattern
- ✅ **Notifications**: Background email notifications (Celery)
- ✅ **Typing Indicators**: Real-time typing status via WebSocket

#### **Security & Access Control**
- ✅ **RBAC**: Organization-scoped role-based permissions
- ✅ **WebSocket Auth**: JWT token validation for WebSocket connections
- ✅ **Rate Limiting**: 100 requests/minute per user
- ✅ **Input Validation**: Message length limits, file type/size validation
- ✅ **Invite Security**: Email-matching invite acceptance

### **Non-Functional Requirements**

#### **Performance**
- ✅ **Response Time**: P95 HTTP < 250ms, WebSocket fanout < 500ms
- ✅ **Throughput**: 100 req/min/user, 20 msgs/sec/WebSocket connection
- ✅ **Scalability**: Horizontal scaling with Redis channel layer
- ✅ **Database**: Optimized queries with proper indexing

#### **Reliability**
- ✅ **Message Retention**: 90-day message cleanup
- ✅ **Webhook Delivery**: At-least-once delivery with exponential backoff
- ✅ **Error Handling**: Comprehensive error responses and logging
- ✅ **Health Checks**: Liveness and readiness endpoints

#### **Observability**
- ✅ **Logging**: Structured JSON logs with request tracing
- ✅ **Monitoring**: Health endpoints and performance metrics
- ✅ **Documentation**: OpenAPI/Swagger documentation

---

## 2) API Surface

### **Authentication Endpoints**
```http
POST /api/v1/auth/register/              # User registration
POST /api/v1/auth/token/                 # Login (JWT tokens)
POST /api/v1/auth/token/refresh/         # Refresh access token
GET  /api/v1/auth/me/                    # Current user profile
PATCH /api/v1/auth/me/                   # Update user profile
GET  /api/v1/auth/me/unread-counts/      # Unread message counts
```

### **Organization Management**
```http
GET    /api/v1/orgs/                          # List user's organizations
POST   /api/v1/orgs/                          # Create organization
GET    /api/v1/orgs/{id}/members/             # List organization members
POST   /api/v1/orgs/{id}/invite/              # Invite user to organization
POST   /api/v1/orgs/accept-invite/            # Accept organization invitation
POST   /api/v1/orgs/{id}/members/{user_id}/role/  # Change member role
```

### **Room Management**
```http
GET    /api/v1/rooms/                         # List user's rooms
POST   /api/v1/rooms/                         # Create room (MANAGER/ADMIN)
GET    /api/v1/rooms/{id}/                    # Get room details
POST   /api/v1/rooms/{id}/join/               # Join a room
POST   /api/v1/rooms/{id}/leave/              # Leave a room
GET    /api/v1/rooms/{id}/members/            # List room members
POST   /api/v1/rooms/{id}/read/{msg_id}/      # Mark messages as read
```

### **Messaging**
```http
GET  /api/v1/messages/rooms/{room_id}/    # List messages (paginated)
POST /api/v1/messages/rooms/{room_id}/    # Send message
```

### **File Management**
```http
POST /api/v1/uploads/presign/            # Get presigned upload URL
GET  /api/v1/uploads/my-uploads/         # List user's uploaded files
```

### **Webhook Management**
```http
GET    /api/v1/webhooks/                 # List organization webhooks
POST   /api/v1/webhooks/                 # Create webhook
GET    /api/v1/webhooks/{id}/            # Get webhook details
POST   /api/v1/webhooks/{id}/test/       # Send test webhook
GET    /api/v1/webhooks/{id}/events/     # List webhook delivery events
```

### **Notification Management**
```http
GET    /api/v1/notifications/            # List user notifications
GET    /api/v1/notifications/{id}/       # Get notification details
PATCH  /api/v1/notifications/{id}/       # Mark notification as read
POST   /api/v1/notifications/mark-all-read/  # Mark all as read
GET    /api/v1/notifications/unread-count/   # Get unread count
```

### **WebSocket Endpoints**
```javascript
ws://domain/ws/rooms/{id}/?token=<JWT_TOKEN>
// Events: message, typing, presence, connection
```

---

## 3) Data Model

### **Core Models**

#### **User** (Custom AbstractUser)
```python
- id: BigAutoField (PK)
- email: EmailField (UNIQUE)
- password: CharField (hashed)
- avatar_url: URLField (optional)
- created_at: DateTimeField
- USERNAME_FIELD = "email"
```

#### **Organization**
```python
- id: BigAutoField (PK)
- name: CharField(120)
- created_at: DateTimeField
- INDEX: created_at
```

#### **OrganizationMember**
```python
- id: BigAutoField (PK)
- org: ForeignKey(Organization)
- user: ForeignKey(User)
- role: CharField(choices=[ADMIN, MANAGER, MEMBER])
- joined_at: DateTimeField
- UNIQUE: (org, user)
- INDEX: (org, user)
```

#### **OrganizationInvite**
```python
- id: BigAutoField (PK)
- org: ForeignKey(Organization)
- email: EmailField
- token: CharField(64, UNIQUE, INDEX)
- role: CharField(choices)
- created_by: ForeignKey(User)
- created_at: DateTimeField
- accepted_at: DateTimeField (nullable)
```

#### **Room**
```python
- id: BigAutoField (PK)
- org: ForeignKey(Organization, nullable)
- name: CharField(120)
- is_dm: BooleanField (default=False)
- created_by: ForeignKey(User)
- created_at: DateTimeField
- INDEX: created_at
```

#### **RoomMember**
```python
- id: BigAutoField (PK)
- room: ForeignKey(Room)
- user: ForeignKey(User)
- last_read_msg_id: BigIntegerField (nullable)
- joined_at: DateTimeField
- UNIQUE: (room, user)
- INDEX: (room, user)
```

#### **Message**
```python
- id: BigAutoField (PK)
- org: ForeignKey(Organization, nullable)
- room: ForeignKey(Room)
- sender: ForeignKey(User)
- body: TextField
- file_url: URLField (nullable)
- is_deleted: BooleanField (default=False)
- created_at: DateTimeField
- INDEX: (room, -id)  # For pagination
```

### **Integration Models**

#### **FileUpload**
```python
- id: UUIDField (PK)
- user: ForeignKey(User)
- filename: CharField(255)
- file_size: BigIntegerField
- content_type: CharField(100)
- file_url: URLField
- uploaded_at: DateTimeField
- expires_at: DateTimeField (nullable)
- INDEX: (user, -uploaded_at), expires_at
```

#### **Webhook**
```python
- id: BigAutoField (PK)
- org: ForeignKey(Organization)
- url: URLField(500)
- secret: CharField(64)
- events: JSONField (list of event types)
- is_active: BooleanField
- created_at: DateTimeField
- last_triggered: DateTimeField (nullable)
- INDEX: (org, is_active)
```

#### **WebhookOutbox**
```python
- id: BigAutoField (PK)
- webhook: ForeignKey(Webhook)
- event_type: CharField(50)
- payload: JSONField
- status: CharField(choices=[pending, sent, failed, retrying])
- retries: IntegerField (default=0)
- max_retries: IntegerField (default=3)
- next_attempt_at: DateTimeField
- last_attempt_at: DateTimeField (nullable)
- last_error: TextField
- created_at: DateTimeField
- INDEX: (status, next_attempt_at), (webhook, status)
```

---

## 4) Architecture

### **Technology Stack**
- **Backend**: Django 5.0 + Django REST Framework
- **Real-time**: Django Channels + Redis Channel Layer
- **Database**: PostgreSQL 15 with optimized indexes
- **Cache**: Redis for caching, sessions, and channel layer
- **Background Jobs**: Celery + Redis broker/result backend
- **File Storage**: AWS S3 with presigned URLs
- **Authentication**: JWT with SimpleJWT
- **Documentation**: OpenAPI/Swagger with drf-spectacular
- **Containerization**: Docker + Docker Compose

### **System Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   Load Balancer │    │   CDN/Static    │
└─────────┬───────┘    └─────────┬───────┘    └─────────────────┘
          │                      │
          │ HTTP/WebSocket       │
          ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│  Django Web     │    │  WebSocket      │
│  (DRF API)      │    │  (Channels)     │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
                     ▼
          ┌─────────────────┐
          │     Redis        │
          │ (Cache + Channel │
          │  Layer + Broker) │
          └─────────┬───────┘
                    │
          ┌─────────┴───────┐
          │                 │
          ▼                 ▼
┌─────────────────┐ ┌─────────────────┐
│   PostgreSQL     │ │   Celery        │
│   (Primary DB)   │ │   Workers       │
└─────────────────┘ └─────────┬───────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │   AWS S3         │
                    │   (File Storage) │
                    └─────────────────┘
```

---

## 5) Key Flows

### **Message Sending Flow**
1. **Client** → `POST /api/rooms/{id}/messages` (with JWT)
2. **API** validates room membership and message content
3. **Database** transaction creates Message record
4. **WebSocket** fanout to room group via Redis channel layer
5. **Celery** task enqueued for notifications (offline users, @mentions)
6. **Response** returns message data to client

### **WebSocket Connection Flow**
1. **Client** connects to `ws://domain/ws/rooms/{id}/?token=<JWT>`
2. **Consumer** extracts JWT from query parameters
3. **Authentication** validates token and extracts user
4. **Authorization** checks room membership
5. **Connection** accepted and added to room group
6. **Welcome** message sent to client

### **File Upload Flow**
1. **Client** → `POST /api/uploads/presign/` (file metadata)
2. **API** validates file type/size and generates S3 presigned URL
3. **Database** creates FileUpload record with expiration
4. **Client** uploads directly to S3 using presigned URL
5. **Message** can reference file_url in message body

### **Webhook Delivery Flow**
1. **Event** occurs (message created, member joined, etc.)
2. **Outbox** record created in same database transaction
3. **Celery** worker picks up outbox record
4. **HMAC** signature generated using webhook secret
5. **HTTP** POST sent to webhook URL with signature header
6. **Retry** logic handles failures with exponential backoff

---

## 6) Security & Compliance

### **Authentication & Authorization**
- **JWT Tokens**: 15-minute access, 7-day refresh with rotation
- **WebSocket Auth**: JWT validation for real-time connections
- **RBAC**: Organization-scoped role-based permissions
- **Invite Security**: Email-matching for invite acceptance

### **Data Protection**
- **Input Validation**: Message length limits, file type validation
- **SQL Injection**: Django ORM protection
- **XSS Prevention**: Proper serialization and validation
- **CSRF Protection**: Token-based CSRF protection

### **Rate Limiting & Throttling**
- **API Throttling**: 100 requests/minute per user
- **WebSocket Limits**: 20 messages/second per connection
- **File Upload**: Size and type restrictions

---

## 7) Performance & Scaling

### **Database Optimization**
- **Indexes**: Optimized for common query patterns
- **Pagination**: Cursor-based pagination for messages
- **Query Optimization**: Select_related and prefetch_related
- **Connection Pooling**: Efficient database connections

### **Caching Strategy**
- **Redis Caching**: Session storage and temporary data
- **Query Caching**: Frequently accessed data
- **CDN Integration**: Static file delivery

### **Horizontal Scaling**
- **Stateless Design**: No server-side session storage
- **Redis Channel Layer**: WebSocket scaling across instances
- **Load Balancing**: Multiple Django instances
- **Database Replication**: Read replicas for scaling

---

## 8) Monitoring & Observability

### **Health Checks**
- **Liveness**: `/health/live` - Basic application health
- **Readiness**: `/health/ready` - Database and Redis connectivity
- **Metrics**: Performance and usage metrics

### **Logging**
- **Structured Logs**: JSON format with request tracing
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Request Tracing**: Unique request IDs for debugging

### **Monitoring**
- **Application Metrics**: Response times, error rates
- **Database Metrics**: Query performance, connection pools
- **Redis Metrics**: Memory usage, hit rates
- **WebSocket Metrics**: Connection counts, message rates

---

## 9) Implementation Status

### **✅ Completed Features**
- **Authentication**: JWT with SimpleJWT, custom user model
- **Organizations**: CRUD, member management, invitations, role changes
- **Rooms**: Creation, membership, permissions
- **Messages**: CRUD, WebSocket fanout, pagination
- **Unread Counts**: Per-room tracking and API endpoints
- **Read Receipts**: Mark messages as read functionality
- **File Uploads**: S3 presigned URLs with validation
- **Webhooks**: Creation, delivery, retry logic, outbox pattern
- **WebSocket Auth**: JWT token validation for connections
- **Rate Limiting**: DRF throttling and WebSocket limits
- **Health Checks**: Liveness and readiness endpoints
- **Docker**: Production-ready containerization
- **Testing**: Comprehensive test suite with pytest
- **Documentation**: Beautiful README and API docs

### **🔄 In Progress**
- **Celery Setup**: Background task processing
- **Notifications**: Email notifications for offline users
- **CI/CD**: GitHub Actions pipeline

### **📋 Future Enhancements**
- **Message Threading**: Reply-to functionality
- **Message Search**: Full-text search across messages
- **Push Notifications**: Mobile push notifications
- **Video/Audio Calls**: WebRTC integration
- **Message Reactions**: Emoji reactions
- **Message Editing**: Edit and delete messages
- **Advanced Analytics**: Usage metrics and insights

---

## 10) Deployment & DevOps

### **Containerization**
- **Docker**: Multi-stage builds for production
- **Docker Compose**: Local development environment
- **Health Checks**: Container health monitoring

### **Cloud Deployment**
- **AWS**: ECS/EKS with RDS and ElastiCache
- **Google Cloud**: Cloud Run with Cloud SQL
- **Azure**: Container Instances with managed databases
- **Railway/Render**: One-click deployment platforms

### **CI/CD Pipeline**
- **GitHub Actions**: Automated testing and deployment
- **Testing**: pytest with coverage reporting
- **Security**: Dependency scanning and code analysis
- **Deployment**: Automated staging and production deployments

---

## 11) Success Metrics

### **Technical Metrics**
- **Uptime**: 99.9% availability target
- **Response Time**: P95 < 250ms for API endpoints
- **WebSocket Latency**: < 500ms for message delivery
- **Error Rate**: < 0.1% error rate
- **Test Coverage**: > 90% code coverage

### **Business Metrics**
- **User Engagement**: Daily/monthly active users
- **Message Volume**: Messages per day/hour
- **File Uploads**: Storage usage and bandwidth
- **Webhook Delivery**: Success rate and latency
- **API Usage**: Requests per minute/hour

---

**Built with ❤️ for modern team collaboration**

*This system design represents a production-ready, enterprise-grade chat platform that demonstrates advanced Django development skills, real-time architecture, and modern DevOps practices.*

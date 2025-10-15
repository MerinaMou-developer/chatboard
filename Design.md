# ChatBoard — System Design (v1.0)

## 0) One-liner
Production-ready realtime team chat (rooms + DMs) with offline notifications, file uploads, RBAC, rate limits, webhooks, and clean docs/deploy.

## 1) Requirements
**Functional**
- Auth (JWT), organizations, rooms, DMs
- Send/receive text (+ optional file_url), @mentions, typing indicator
- Unread counts, mark-as-read
- Email/push notifications for offline/mentioned users
- Basic search by keyword within a room
- Webhooks: `message.created`, `message.deleted`, `member.invited`

**Non-functional**
- P95 HTTP < 250ms (demo tier), WS fanout < 500ms
- Rate limit 100 req/min/user (HTTP), 20 msgs/sec/connection (WS)
- Retain messages 90 days

**Out of scope (v1)**
- Org billing/SSO, global search in files, message threads

## 2) API Surface
- `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`
- `POST /orgs`, `GET /orgs/me`, `POST /orgs/invite`, `POST /orgs/accept-invite`
- `GET /me`, `PATCH /me`
- `POST /rooms`, `GET /rooms`, `GET /rooms/{id}`, `POST /rooms/dm`
- `GET /rooms/{id}/messages?before=<id>&limit=50`
- `POST /rooms/{id}/messages` (optional `Idempotency-Key`)
- `PATCH /messages/{id}`, `DELETE /messages/{id}`
- `GET /me/unread-counts`, `POST /rooms/{id}/read/{msg_id}`
- `POST /uploads/presign` → `{upload_url, file_url}`
- `POST /webhooks`, `POST /webhooks/test/{id}`
- **WS** `ws/rooms/{id}` events: `message`, `typing`, `presence`

## 3) Data Model
- **Organization**(id, name, created_at)
- **User**(id, org_id*, email UNIQUE, password_hash, role[ADMIN|MANAGER|MEMBER], name, avatar_url, created_at)
- **Room**(id, org_id*, name, is_dm, created_by_id, created_at)
- **RoomMember**(id, room_id*, user_id*, last_read_msg_id, joined_at) UNIQUE(room_id, user_id)
- **Message**(id, org_id*, room_id*, sender_id*, body, file_url, is_deleted, created_at)
- **ApiKey**(id, org_id*, key_hash UNIQUE, scopes[], created_at)
- **Webhook**(id, org_id*, url, secret_hash, events[], is_active, created_at)
- **WebhookOutbox**(id, org_id*, event_type, payload_json, status[pending|sent|fail], retries, next_attempt_at, created_at)
- **Notification**(id, user_id*, type, payload_json, read_at, created_at)
- **AuditLog**(id, org_id*, actor_id, action, meta_json, created_at)

**Indexes**
- Message: (room_id, created_at DESC), (org_id, created_at)
- Outbox: (status, next_attempt_at)
- User: (org_id, email)

## 4) Architecture
- **HTTP API:** Django + DRF  
- **WebSocket:** Django Channels (ASGI) + Redis channel layer  
- **DB:** PostgreSQL  
- **Cache/Rate-limit/Presence:** Redis  
- **Background jobs:** Celery (+ Beat), broker Redis (RabbitMQ optional)  
- **Storage:** S3/MinIO/Cloudinary for uploads  
- **Docs:** drf-spectacular (Swagger)  
- **Deploy:** Docker + Render/Railway (web + worker)

Client ──HTTP──> DRF(API) ──SQL──> Postgres
│ │
└─WS────────────> Channels ── Redis (channel layer + cache)
│
└─ Celery Worker ── SMTP / Webhook delivery
│
└─ S3/Cloudinary (file storage)


## 5) Key Flows
**Send message**
1) `POST /rooms/{id}/messages` → create `Message` (DB tx)
2) Publish WS event to `room:{id}` (Channels)
3) Enqueue Celery notifications for offline users and mentions
4) Update sender’s `last_read_msg_id`

**Mark read**
- `POST /rooms/{id}/read/{msg_id}` sets `RoomMember.last_read_msg_id`
- Unread counts = messages with id > last_read per room

**Webhook delivery**
- Write to **WebhookOutbox** inside same tx
- Celery worker delivers with HMAC SHA256 signature, retries with backoff

## 6) Scaling & Performance
- Paginate messages (limit=50), indexes as above
- Cache hot membership lists, presence in Redis (TTL 60s)
- DRF throttles: `100/min/user`; WS token bucket: 20 msgs/sec/conn

## 7) Reliability & Correctness
- DB transactions for create/edit/delete
- Celery retries (`max_retries`, `retry_backoff`)
- Optional `Idempotency-Key` for message POST
- Outbox pattern for guaranteed webhook send (at-least-once)

## 8) Security & Observability
- JWT for users; `X-API-Key` for service clients
- Org-scoped filtering on all queries
- Upload validation (type/size), sanitize body, max 2000 chars
- JSON logs (request_id, user_id, org_id, endpoint, latency)
- `/health/live`, `/health/ready` (+ optional `/metrics` Prometheus)

## 9) Deliverables
- Live demo URL, Swagger docs, test creds
- README with run instructions (Docker + local)
- Screenshots + 2–3 min demo video
- CI (pytest) green badge

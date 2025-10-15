# ChatBoard
Realtime team chat backend (Django/DRF + Channels + Redis + Celery). Production-style stack with JWT auth, orgs/rooms, WS fanout, offline notifications, uploads, webhooks, and Swagger docs.

<p align="left">
  <b>Stack:</b> Django • DRF • Channels • Redis • Celery • PostgreSQL • Docker • drf-spectacular
</p>

## ✨ Features
- JWT auth + organizations (multi-tenant)
- Rooms & DMs, unread counts, typing indicator
- WebSocket realtime messaging (Channels + Redis)
- Offline email/push notifications (Celery + retries)
- File uploads (pre-signed URL; S3/Cloudinary)
- Outbound webhooks (HMAC-signed, outbox + backoff)
- Rate limits, health checks, JSON logs
- Swagger API docs

## 🚀 Live
- API Docs: `https://<your-deploy>/api/docs/`  
- Health: `https://<your-deploy>/health/live`

## 🧰 Local Development

### 1) Prereqs
- Python 3.11+, Docker, Git

### 2) Clone & venv
```bash
git clone <repo-url> chatboard && cd chatboard
python -m venv venv
# Windows PowerShell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
# macOS/Linux
# source venv/bin/activate
pip install -r requirements.txt

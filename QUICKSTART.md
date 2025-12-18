# TikTok Auto-Poster - Quick Start Guide

## Option 1: Docker Compose (Recommended)

The easiest way to run everything:

```bash
# From the workspace root directory
cd /mnt/c/Users/meesv/Documents/agent-smith/chat-ea2f3f66/workspace

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

**Services:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## Option 2: Local Development (No Docker)

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Redis 7+
- FFmpeg (for video processing)

### Step 1: Start PostgreSQL and Redis

**Using Docker for just databases:**
```bash
docker run -d --name tiktok-postgres \
  -e POSTGRES_USER=tiktok \
  -e POSTGRES_PASSWORD=tiktok_password_dev \
  -e POSTGRES_DB=tiktok_db \
  -p 5432:5432 \
  postgres:16-alpine

docker run -d --name tiktok-redis \
  -p 6379:6379 \
  redis:7-alpine redis-server --requirepass redis_password_dev
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Start Celery Worker (new terminal)

```bash
cd backend
source venv/bin/activate

# Start worker
celery -A app.worker.celery_app worker --loglevel=info
```

### Step 4: Frontend Setup (new terminal)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## Testing the Setup

1. **Check backend health:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **View API docs:**
   Open http://localhost:8000/docs

3. **Access frontend:**
   Open http://localhost:3000

---

## First Steps After Setup

1. **Add Proxies** (Settings → Proxies)
   - Upload proxies in format: `host:port:username:password`

2. **Add Accounts** (Settings → Accounts)
   - Import TikTok accounts with cookies
   - Format: JSON with cookies array

3. **Create Campaign** (Campaigns → New)
   - Upload video
   - Set caption
   - Select accounts
   - Configure schedule
   - Start campaign!

---

## Troubleshooting

### Database connection failed
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env

### Redis connection failed
- Ensure Redis is running
- Check REDIS_URL in .env

### Celery tasks not running
- Ensure Celery worker is started
- Check Redis connection

### Video upload fails
- Ensure `uploads` directory exists and is writable
- Check MAX_UPLOAD_SIZE in .env

---

## Environment Variables

Key variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | See .env |
| REDIS_URL | Redis connection string | See .env |
| SADCAPTCHA_API_KEY | Captcha solver API key | Required for uploads |
| TIKTOK_HEADLESS | Run browser headless | true |
| UPLOAD_DIR | Video upload directory | ./uploads |

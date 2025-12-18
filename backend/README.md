# TikTok Auto-Poster Backend

FastAPI backend for managing TikTok auto-posting campaigns with account management, proxy support, and browser fingerprinting.

## Features

- **Account Management**: Manage TikTok accounts with status tracking (active, banned, cooldown, needs_captcha)
- **Proxy Support**: Configure and health-check residential, datacenter, and mobile proxies
- **Browser Profiles**: Manage browser fingerprints with customizable user agents, viewports, timezones, and more
- **Campaign Management**: Create and manage posting campaigns with flexible scheduling
- **Job Queue**: Track individual upload jobs with retry logic and error handling
- **Bulk Import**: CSV and JSON bulk import for accounts and proxies
- **Health Monitoring**: Proxy health checks and account login testing

## Project Structure

```
backend/
├── app/
│   ├── api/              # API route handlers
│   │   ├── accounts.py   # Account CRUD + bulk import + test login
│   │   ├── proxies.py    # Proxy CRUD + bulk import + health checks
│   │   ├── profiles.py   # Browser profile CRUD + templates
│   │   ├── campaigns.py  # Campaign CRUD + start campaign
│   │   └── jobs.py       # Job management + retry logic
│   ├── models/           # SQLAlchemy models
│   │   ├── account.py    # Account model
│   │   ├── proxy.py      # Proxy model
│   │   ├── profile.py    # BrowserProfile model
│   │   ├── campaign.py   # Campaign model
│   │   └── job.py        # Job model
│   ├── schemas/          # Pydantic schemas
│   │   ├── account.py
│   │   ├── proxy.py
│   │   ├── profile.py
│   │   ├── campaign.py
│   │   └── job.py
│   ├── config.py         # Application settings
│   ├── database.py       # Database setup and session management
│   └── main.py           # FastAPI app initialization
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment variables
└── README.md             # This file
```

## Installation

1. **Clone the repository**

```bash
cd backend
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your database credentials and settings
```

5. **Set up PostgreSQL database**

```bash
# Create database
createdb tiktok_autoposter

# Or using psql
psql -U postgres
CREATE DATABASE tiktok_autoposter;
```

6. **Initialize database tables**

The tables will be created automatically when you first run the application.

## Running the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### Accounts
- `GET /api/v1/accounts` - List all accounts
- `GET /api/v1/accounts/{id}` - Get account by ID
- `POST /api/v1/accounts` - Create new account
- `PUT /api/v1/accounts/{id}` - Update account
- `DELETE /api/v1/accounts/{id}` - Delete account
- `POST /api/v1/accounts/bulk-import` - Bulk import from JSON
- `POST /api/v1/accounts/bulk-import-csv` - Bulk import from CSV
- `POST /api/v1/accounts/test-login` - Test account login

### Proxies
- `GET /api/v1/proxies` - List all proxies
- `GET /api/v1/proxies/{id}` - Get proxy by ID
- `POST /api/v1/proxies` - Create new proxy
- `PUT /api/v1/proxies/{id}` - Update proxy
- `DELETE /api/v1/proxies/{id}` - Delete proxy
- `POST /api/v1/proxies/bulk-import` - Bulk import from JSON
- `POST /api/v1/proxies/bulk-import-csv` - Bulk import from CSV
- `POST /api/v1/proxies/{id}/health-check` - Check proxy health
- `POST /api/v1/proxies/health-check-all` - Check all proxies

### Browser Profiles
- `GET /api/v1/profiles` - List all profiles
- `GET /api/v1/profiles/{id}` - Get profile by ID
- `GET /api/v1/profiles/templates` - Get available templates
- `POST /api/v1/profiles` - Create new profile
- `POST /api/v1/profiles/from-template/{template_name}` - Create from template
- `PUT /api/v1/profiles/{id}` - Update profile
- `DELETE /api/v1/profiles/{id}` - Delete profile

### Campaigns
- `GET /api/v1/campaigns` - List all campaigns
- `GET /api/v1/campaigns/{id}` - Get campaign by ID
- `POST /api/v1/campaigns` - Create new campaign
- `PUT /api/v1/campaigns/{id}` - Update campaign
- `DELETE /api/v1/campaigns/{id}` - Delete campaign
- `POST /api/v1/campaigns/{id}/start` - Start campaign
- `POST /api/v1/campaigns/{id}/pause` - Pause campaign
- `POST /api/v1/campaigns/{id}/cancel` - Cancel campaign

### Jobs
- `GET /api/v1/jobs` - List all jobs (with filters)
- `GET /api/v1/jobs/{id}` - Get job by ID
- `POST /api/v1/jobs` - Create new job
- `PUT /api/v1/jobs/{id}` - Update job
- `DELETE /api/v1/jobs/{id}` - Delete job
- `POST /api/v1/jobs/{id}/retry` - Retry failed job
- `POST /api/v1/jobs/retry-failed` - Retry all failed jobs
- `GET /api/v1/jobs/statistics/summary` - Get job statistics

## Database Models

### Account
- Email, password, cookies (JSON)
- Status: active, banned, cooldown, needs_captcha, inactive
- Relations: proxy, browser profile
- Timestamps: last_used, created_at, updated_at

### Proxy
- Host, port, username, password
- Type: residential, datacenter, mobile
- Status: active, inactive, banned, error
- Latency tracking and health monitoring

### BrowserProfile
- Name, user agent, viewport, timezone, locale
- Fingerprint configuration (canvas, WebGL, audio)
- Pre-defined templates available

### Campaign
- Name, video path, caption template
- Status: draft, scheduled, running, paused, completed, cancelled
- Account selection strategy and filters
- Schedule configuration

### Job
- Campaign and account references
- Status: pending, running, completed, failed, cancelled, retrying
- Video path, caption, error tracking
- Retry logic with configurable max retries

## CSV Import Formats

### Accounts CSV
```csv
email,password,status,proxy_id,profile_id
user@example.com,password123,active,1,1
```

### Proxies CSV
```csv
host,port,username,password,type,status
proxy.example.com,8080,user,pass,residential,active
```

## Environment Variables

See `.env.example` for all available configuration options.

## Development

The backend uses:
- **FastAPI**: Modern async web framework
- **SQLAlchemy 2.0**: Async ORM
- **Pydantic**: Data validation
- **PostgreSQL**: Database with asyncpg driver

All async/await patterns are properly implemented throughout the codebase.

## Next Steps

1. Implement actual TikTok automation logic in account test login endpoint
2. Implement proxy health check logic
3. Add authentication and authorization
4. Create background task worker for job processing
5. Add rate limiting and request throttling
6. Implement file upload handling for videos
7. Add logging and monitoring
8. Create database migrations with Alembic

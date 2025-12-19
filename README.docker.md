# TikTok Auto-Poster - Docker Setup Guide

## Quick Start

1. Copy environment variables:
```bash
cp .env.example .env
```

2. Edit `.env` and set required variables:
   - `SECRET_KEY` - Generate with: `openssl rand -hex 32`
   - `POSTGRES_PASSWORD` - Strong database password
   - `REDIS_PASSWORD` - Strong Redis password
   - `SADCAPTCHA_API_KEY` - Your SadCaptcha API key

3. Build and start services:
```bash
docker-compose up -d
```

4. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Architecture

### Services

1. **postgres** - PostgreSQL 16 database
   - Persistent volume for data
   - Health checks enabled
   - Port: 5432

2. **redis** - Redis 7 cache and message broker
   - Persistent volume for data
   - Password protected
   - Port: 6379

3. **backend** - FastAPI application
   - Python 3.11 with Playwright and FFmpeg
   - Handles API requests
   - Port: 8000

4. **worker** - Celery worker
   - Processes background tasks
   - Video uploads, scheduling, automation
   - Shares image with backend

5. **beat** - Celery beat scheduler
   - Manages scheduled tasks
   - Triggers periodic jobs

6. **frontend** - Next.js application
   - React UI
   - Server-side rendering
   - Port: 3000

### Volumes

- `postgres_data` - Database persistence
- `redis_data` - Redis persistence
- `uploads` - Video/image uploads
- `sessions` - TikTok session storage

### Network

All services communicate via `tiktok-network` bridge network.

## Environment Variables

### Required Variables

```bash
SECRET_KEY=your_secret_key_here
POSTGRES_PASSWORD=secure_password
REDIS_PASSWORD=secure_password
SADCAPTCHA_API_KEY=your_api_key
```

### Optional Configuration

- `WORKER_CONCURRENCY` - Number of Celery workers (default: 4)
- `LOG_LEVEL` - Logging level (default: info)
- `MAX_UPLOAD_SIZE` - Max file size in bytes (default: 100MB)
- `CORS_ORIGINS` - Allowed origins for CORS

## Common Commands

Using Make (recommended):
```bash
make help              # Show all commands
make up                # Start all services
make down              # Stop all services
make logs              # View all logs
make logs-backend      # View backend logs
make migrate           # Run migrations
make shell-backend     # Open backend shell
make test              # Run tests
```

Using docker-compose directly:
```bash
docker-compose up -d                    # Start services
docker-compose down                     # Stop services
docker-compose logs -f backend          # View logs
docker-compose exec backend /bin/bash   # Shell access
docker-compose ps                       # List containers
```

## Development vs Production

### Development Mode

```bash
# Use development target in Dockerfile
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Features:
- Hot-reload enabled
- Debug mode
- Source code mounted as volume
- Detailed logging

### Production Mode

```bash
docker-compose up -d
```

Features:
- Optimized builds
- Non-root user
- Gunicorn with multiple workers
- Health checks
- Resource limits

## Health Checks

All services include health checks:

- **Postgres**: `pg_isready` every 10s
- **Redis**: `redis-cli ping` every 10s
- **Backend**: HTTP GET `/health` every 30s
- **Frontend**: HTTP GET `/api/health` every 30s
- **Worker**: Celery ping every 30s

Check health status:
```bash
docker-compose ps
# or
make health
```

## Database Management

### Migrations

Create new migration:
```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
docker-compose exec backend alembic upgrade head
```

Rollback migration:
```bash
docker-compose exec backend alembic downgrade -1
```

### Backup

Backup database:
```bash
docker-compose exec postgres pg_dump -U tiktok tiktok_db > backup.sql
```

Restore database:
```bash
docker-compose exec -T postgres psql -U tiktok -d tiktok_db < backup.sql
```

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Celery Monitoring

Check active tasks:
```bash
docker-compose exec worker celery -A app.celery inspect active
```

Check worker stats:
```bash
docker-compose exec worker celery -A app.celery inspect stats
```

Access Flower (Celery monitoring UI):
```bash
docker-compose exec worker celery -A app.celery flower
```

## Troubleshooting

### Backend won't start

1. Check logs:
```bash
docker-compose logs backend
```

2. Verify database connection:
```bash
docker-compose exec backend python -c "from app.database import engine; print(engine.connect())"
```

3. Check environment variables:
```bash
docker-compose exec backend env | grep DATABASE_URL
```

### Worker not processing tasks

1. Check worker logs:
```bash
docker-compose logs worker
```

2. Verify Celery connection:
```bash
docker-compose exec worker celery -A app.celery inspect ping
```

3. Check Redis connection:
```bash
docker-compose exec redis redis-cli -a redis_password ping
```

### Playwright/Browser issues

1. Rebuild with fresh browser installation:
```bash
docker-compose build --no-cache backend worker
```

2. Check browser installation:
```bash
docker-compose exec backend playwright install --dry-run
```

### Database connection refused

1. Wait for health check:
```bash
docker-compose ps postgres
```

2. Check if postgres is ready:
```bash
docker-compose exec postgres pg_isready -U tiktok
```

### Port already in use

Change ports in `.env`:
```bash
BACKEND_PORT=8001
FRONTEND_PORT=3001
POSTGRES_PORT=5433
REDIS_PORT=6380
```

## Security Best Practices

1. Always use strong passwords
2. Never commit `.env` file
3. Use secrets management in production
4. Enable SSL/TLS for external connections
5. Regularly update dependencies
6. Monitor logs for suspicious activity
7. Limit resource usage with Docker constraints

## Resource Limits (Production)

Add to `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Scaling

Scale workers:
```bash
docker-compose up -d --scale worker=4
```

Note: For production scaling, use Kubernetes or Docker Swarm.

## Updates

Update images:
```bash
docker-compose pull
docker-compose up -d
```

Rebuild after code changes:
```bash
docker-compose up -d --build
```

## Clean Up

Remove containers and volumes:
```bash
docker-compose down -v
```

Remove everything including images:
```bash
docker-compose down -v --rmi all
```

Clean Docker system:
```bash
docker system prune -af --volumes
```

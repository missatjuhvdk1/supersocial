# Celery Worker System - TikTok Auto-Poster

This directory contains the Celery-based job queue system for the TikTok auto-poster application.

## Overview

The worker system handles asynchronous tasks such as:
- Video uploads to TikTok accounts
- Campaign management and job scheduling
- Account authentication testing
- Proxy connectivity checks
- Batch video processing

## Architecture

```
app/worker/
├── celery_app.py      # Celery configuration
├── tasks.py           # Task definitions
├── __init__.py        # Module exports
└── README.md          # This file
```

## Configuration

### Redis Setup

The system requires Redis as the message broker and result backend:

```bash
# Install Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                  # macOS

# Start Redis
redis-server
```

Configure Redis URL via environment variable:
```bash
export REDIS_URL="redis://localhost:6379/0"
```

### Celery Configuration

Key configuration options in `celery_app.py`:

- **Broker**: Redis for message queuing
- **Result Backend**: Redis for storing task results
- **Serialization**: JSON format
- **Time Limits**: 30 min hard limit, 25 min soft limit
- **Rate Limiting**: 10 uploads/min, 30 account tests/min, 60 proxy checks/min
- **Retry Policy**: Max 3 retries with exponential backoff
- **Task Queues**:
  - `uploads`: Video upload tasks
  - `campaigns`: Campaign management tasks
  - `tests`: Account and proxy testing
  - `processing`: Video processing tasks

## Starting the Worker

### Development

```bash
# Start a single worker
celery -A app.worker.celery_app worker --loglevel=info

# Start worker with specific queues
celery -A app.worker.celery_app worker -Q uploads,campaigns --loglevel=info

# Start worker with concurrency
celery -A app.worker.celery_app worker --concurrency=4 --loglevel=info
```

### Production

```bash
# Start worker as daemon with autoscale
celery -A app.worker.celery_app worker \
  --loglevel=info \
  --concurrency=8 \
  --autoscale=10,3 \
  --max-tasks-per-child=50 \
  --time-limit=1800 \
  --soft-time-limit=1500 \
  --logfile=/var/log/celery/worker.log \
  --pidfile=/var/run/celery/worker.pid

# Start beat scheduler (for periodic tasks)
celery -A app.worker.celery_app beat \
  --loglevel=info \
  --logfile=/var/log/celery/beat.log \
  --pidfile=/var/run/celery/beat.pid
```

### Using Systemd (Recommended for Production)

Create `/etc/systemd/system/celery-worker.service`:

```ini
[Unit]
Description=Celery Worker for TikTok Auto-Poster
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment="REDIS_URL=redis://localhost:6379/0"
ExecStart=/path/to/venv/bin/celery -A app.worker.celery_app worker \
  --loglevel=info \
  --concurrency=8 \
  --logfile=/var/log/celery/worker.log \
  --pidfile=/var/run/celery/worker.pid
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start celery-worker
sudo systemctl enable celery-worker
```

## Available Tasks

### 1. upload_video_task(job_id)

Uploads a video to TikTok for a specific job.

**Parameters:**
- `job_id` (int): The ID of the job to process

**Features:**
- Creates unique video copy to avoid duplicate detection
- Uses proxy and browser profile if configured
- Updates job status in database
- Automatically retries on failure (max 3 times)
- Cleans up temporary files after upload

**Example:**
```python
from app.worker.tasks import upload_video_task

# Schedule immediate upload
result = upload_video_task.delay(job_id=123)

# Schedule upload with delay
result = upload_video_task.apply_async(
    args=[123],
    countdown=300  # Start in 5 minutes
)
```

### 2. start_campaign_task(campaign_id, account_ids)

Starts a campaign by creating and scheduling jobs for selected accounts.

**Parameters:**
- `campaign_id` (int): The ID of the campaign to start
- `account_ids` (list[int]): List of account IDs to use

**Features:**
- Distributes uploads across time range
- Adds random jitter to avoid patterns
- Assigns proxies to jobs
- Updates campaign status

**Example:**
```python
from app.worker.tasks import start_campaign_task

result = start_campaign_task.delay(
    campaign_id=456,
    account_ids=[1, 2, 3, 4, 5]
)
```

### 3. test_account_task(account_id)

Tests if an account's cookies are still valid.

**Parameters:**
- `account_id` (int): The ID of the account to test

**Features:**
- Verifies authentication with TikTok
- Updates account status (ACTIVE/INACTIVE)
- Retries on temporary failures (max 2 times)

**Example:**
```python
from app.worker.tasks import test_account_task

result = test_account_task.delay(account_id=789)
```

### 4. check_proxy_task(proxy_id)

Tests proxy connectivity and measures latency.

**Parameters:**
- `proxy_id` (int): The ID of the proxy to check

**Features:**
- Tests HTTP/HTTPS connectivity
- Measures latency
- Detects geolocation
- Updates proxy status

**Example:**
```python
from app.worker.tasks import check_proxy_task

result = check_proxy_task.delay(proxy_id=321)
```

### 5. batch_process_video_task(video_path, count, campaign_id)

Creates multiple unique variations of a video.

**Parameters:**
- `video_path` (str): Path to the source video
- `count` (int): Number of variations to create
- `campaign_id` (int): Campaign ID to associate variations with

**Features:**
- Creates unique video files with different hashes
- Applies subtle transformations
- Runs in parallel when possible

**Example:**
```python
from app.worker.tasks import batch_process_video_task

result = batch_process_video_task.delay(
    video_path="/path/to/video.mp4",
    count=10,
    campaign_id=456
)
```

### 6. cleanup_old_jobs_task(days)

Cleans up completed/failed jobs older than specified days.

**Parameters:**
- `days` (int): Number of days to keep jobs (default: 30)

**Example:**
```python
from app.worker.tasks import cleanup_old_jobs_task

result = cleanup_old_jobs_task.delay(days=30)
```

### 7. check_all_proxies_task()

Schedules check tasks for all proxies in the database.

**Example:**
```python
from app.worker.tasks import check_all_proxies_task

result = check_all_proxies_task.delay()
```

## Monitoring

### Flower (Web-based monitoring)

Install and start Flower:
```bash
pip install flower

# Start Flower
celery -A app.worker.celery_app flower --port=5555

# Access at http://localhost:5555
```

### Command Line Monitoring

```bash
# View active tasks
celery -A app.worker.celery_app inspect active

# View scheduled tasks
celery -A app.worker.celery_app inspect scheduled

# View registered tasks
celery -A app.worker.celery_app inspect registered

# View worker stats
celery -A app.worker.celery_app inspect stats

# Purge all tasks
celery -A app.worker.celery_app purge
```

### Logs

Monitor worker logs in real-time:
```bash
tail -f /var/log/celery/worker.log
```

## Error Handling

### Retry Behavior

Tasks automatically retry on failure with:
- **Max retries**: 3 attempts
- **Backoff**: Exponential with jitter
- **Countdown**: 5 seconds base (increases exponentially)
- **Max backoff**: 600 seconds (10 minutes)

### Task States

- `PENDING`: Task is waiting to be executed
- `STARTED`: Task has been started
- `RETRY`: Task failed and will be retried
- `FAILURE`: Task failed permanently
- `SUCCESS`: Task completed successfully

### Checking Task Status

```python
from app.worker.celery_app import celery_app

# Get task result
result = celery_app.AsyncResult(task_id)

print(f"State: {result.state}")
print(f"Info: {result.info}")

# Wait for result (blocking)
if result.ready():
    print(f"Result: {result.get()}")
```

## Rate Limiting

Tasks have rate limits to prevent overload:

- **upload_video_task**: 10/minute
- **test_account_task**: 30/minute
- **check_proxy_task**: 60/minute

Override rate limits if needed:
```python
upload_video_task.apply_async(
    args=[123],
    rate_limit="20/m"  # Override to 20 per minute
)
```

## Best Practices

1. **Use delays for campaigns**: Spread uploads over time to avoid detection
2. **Monitor worker health**: Use Flower or command-line tools
3. **Set appropriate concurrency**: Match your server resources
4. **Clean up old jobs**: Run cleanup task periodically
5. **Check proxy health**: Test proxies regularly
6. **Use unique videos**: Always process videos before upload
7. **Handle failures gracefully**: Let retry mechanism work
8. **Log everything**: Enable INFO level logging for debugging

## Troubleshooting

### Worker not starting

```bash
# Check Redis connection
redis-cli ping

# Check for port conflicts
lsof -i :6379

# Verify Python imports
python -c "from app.worker import celery_app"
```

### Tasks not executing

```bash
# Check worker is running
celery -A app.worker.celery_app inspect active

# Check task registration
celery -A app.worker.celery_app inspect registered

# Purge queue and restart
celery -A app.worker.celery_app purge
```

### High memory usage

```bash
# Reduce concurrency
celery -A app.worker.celery_app worker --concurrency=2

# Enable max-tasks-per-child
celery -A app.worker.celery_app worker --max-tasks-per-child=10
```

### Database connection issues

- Ensure async database session handling
- Check connection pool settings
- Monitor connection count

## Dependencies

Required packages:
```bash
pip install celery redis kombu sqlalchemy asyncio
```

Optional for monitoring:
```bash
pip install flower
```

## Environment Variables

- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379/0)
- `DATABASE_URL`: Database connection URL
- `CELERY_BROKER_URL`: Override broker URL
- `CELERY_RESULT_BACKEND`: Override result backend URL

## Support

For issues or questions:
1. Check logs in `/var/log/celery/`
2. Review task status with Flower
3. Inspect worker state with CLI commands
4. Check database for job states

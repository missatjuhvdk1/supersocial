"""
Celery Application Configuration for TikTok Auto-Poster

This module configures the Celery application with Redis as the broker
and result backend, along with task serialization, time limits, and retry policies.
"""

import os
from celery import Celery
from kombu import serialization

# Get Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "tiktok_autoposter",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.worker.tasks"]
)

# Celery Configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes hard limit
    task_soft_time_limit=1500,  # 25 minutes soft limit

    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    worker_disable_rate_limits=False,

    # Retry policy defaults
    task_default_retry_delay=60,  # 1 minute default retry delay
    task_max_retries=3,
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,

    # Broker settings
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,

    # Rate limiting
    task_annotations={
        "app.worker.tasks.upload_video_task": {
            "rate_limit": "10/m",  # 10 uploads per minute max
        },
        "app.worker.tasks.test_account_task": {
            "rate_limit": "30/m",  # 30 account tests per minute
        },
        "app.worker.tasks.check_proxy_task": {
            "rate_limit": "60/m",  # 60 proxy checks per minute
        },
    },

    # Task routes (can be used to route tasks to specific queues)
    task_routes={
        "app.worker.tasks.upload_video_task": {"queue": "uploads"},
        "app.worker.tasks.start_campaign_task": {"queue": "campaigns"},
        "app.worker.tasks.test_account_task": {"queue": "tests"},
        "app.worker.tasks.check_proxy_task": {"queue": "tests"},
        "app.worker.tasks.batch_process_video_task": {"queue": "processing"},
    },

    # Beat schedule (for periodic tasks if needed)
    beat_schedule={
        # Example: Check all proxies every hour
        # "check-all-proxies": {
        #     "task": "app.worker.tasks.check_all_proxies_task",
        #     "schedule": 3600.0,
        # },
    },
)

# Optional: Task events for monitoring
celery_app.conf.task_send_sent_event = True
celery_app.conf.worker_send_task_events = True

if __name__ == "__main__":
    celery_app.start()

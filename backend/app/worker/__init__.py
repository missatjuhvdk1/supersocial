"""
Worker Module for TikTok Auto-Poster

This module exports the Celery application and tasks for the TikTok auto-poster system.
"""

from app.worker.celery_app import celery_app
from app.worker.tasks import (
    upload_video_task,
    start_campaign_task,
    test_account_task,
    check_proxy_task,
    batch_process_video_task,
    cleanup_old_jobs_task,
    check_all_proxies_task,
)

__all__ = [
    "celery_app",
    "upload_video_task",
    "start_campaign_task",
    "test_account_task",
    "check_proxy_task",
    "batch_process_video_task",
    "cleanup_old_jobs_task",
    "check_all_proxies_task",
]

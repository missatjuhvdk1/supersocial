"""
Celery Tasks for TikTok Auto-Poster

This module contains all Celery tasks for video uploading, campaign management,
account testing, proxy checking, and video processing.
"""

import logging
import os
import shutil
import time
import random
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded, Retry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.worker.celery_app import celery_app
from app.database import async_session_maker
from app.models.job import Job, JobStatus
from app.models.campaign import Campaign, CampaignStatus
from app.models.account import Account, AccountStatus
from app.models.proxy import Proxy, ProxyStatus
from app.models.profile import BrowserProfile

# Configure logging
logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper function to run async code in sync context."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If there's already a running loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    name="app.worker.tasks.upload_video_task"
)
def upload_video_task(self, job_id: int) -> Dict[str, Any]:
    """
    Upload a video to TikTok for a specific job.

    Args:
        job_id: The ID of the job to process

    Returns:
        Dictionary with upload results

    Raises:
        Retry: If the upload fails and should be retried
    """
    return run_async(_upload_video_task_async(self, job_id))


async def _upload_video_task_async(task_self, job_id: int) -> Dict[str, Any]:
    """Async implementation of upload_video_task."""
    temp_video_path = None

    async with async_session_maker() as db:
        try:
            logger.info(f"Starting upload task for job_id={job_id}")

            # Fetch job from database
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()

            if not job:
                logger.error(f"Job {job_id} not found")
                raise ValueError(f"Job {job_id} not found")

            # Update job status to running
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            await db.commit()

            # Get associated account
            result = await db.execute(select(Account).where(Account.id == job.account_id))
            account = result.scalar_one_or_none()

            if not account:
                raise ValueError(f"Account {job.account_id} not found")

            # Get proxy if assigned
            proxy = None
            if account.proxy_id:
                result = await db.execute(select(Proxy).where(Proxy.id == account.proxy_id))
                proxy = result.scalar_one_or_none()

            # Get browser profile if assigned
            profile = None
            if account.profile_id:
                result = await db.execute(select(BrowserProfile).where(BrowserProfile.id == account.profile_id))
                profile = result.scalar_one_or_none()

            # Get campaign for video details
            result = await db.execute(select(Campaign).where(Campaign.id == job.campaign_id))
            campaign = result.scalar_one_or_none()

            if not campaign:
                raise ValueError(f"Campaign {job.campaign_id} not found")

            # Process video (create unique copy)
            logger.info(f"Processing video for job {job_id}")
            from app.services.video_processor import VideoProcessor
            video_processor = VideoProcessor()

            temp_video_path = video_processor.create_unique_copy(
                campaign.video_path,
                job_id=job_id
            )

            # Initialize TikTok uploader
            logger.info(f"Initializing TikTok uploader for account {account.email}")
            from app.services.tiktok_uploader import TikTokUploader
            uploader = TikTokUploader(
                cookies=account.cookies,
                proxy=_proxy_to_dict(proxy) if proxy else None,
                headless=True
            )

            # Prepare upload parameters from job and campaign
            upload_params = {
                "video_path": temp_video_path,
                "caption": job.caption,
            }

            # Upload video
            logger.info(f"Uploading video for job {job_id}")
            upload_result = await asyncio.to_thread(uploader.upload_video, **upload_params)

            # Update job with results
            if upload_result.get("success"):
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                account.last_used = datetime.utcnow()
                logger.info(f"Job {job_id} completed successfully")
            else:
                job.status = JobStatus.FAILED
                job.error_message = upload_result.get("error", "Unknown error")
                job.completed_at = datetime.utcnow()
                logger.error(f"Job {job_id} failed: {job.error_message}")

            await db.commit()

            return {
                "job_id": job_id,
                "status": job.status.value,
                "error": job.error_message
            }

        except SoftTimeLimitExceeded:
            logger.error(f"Job {job_id} exceeded time limit")
            job.status = JobStatus.FAILED
            job.error_message = "Task exceeded time limit"
            job.completed_at = datetime.utcnow()
            await db.commit()
            raise

        except Exception as e:
            logger.exception(f"Error processing job {job_id}: {str(e)}")

            # Update job status
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()

            if job:
                job.retry_count = (job.retry_count or 0) + 1

                if job.retry_count >= job.max_retries:
                    job.status = JobStatus.FAILED
                    job.error_message = f"Max retries exceeded: {str(e)}"
                    job.completed_at = datetime.utcnow()
                    await db.commit()
                    logger.error(f"Job {job_id} failed after max retries")
                else:
                    job.status = JobStatus.RETRYING
                    job.error_message = f"Retry {job.retry_count}/{job.max_retries}: {str(e)}"
                    await db.commit()
                    logger.info(f"Job {job_id} will retry (attempt {job.retry_count}/{job.max_retries})")

            raise

        finally:
            # Clean up temporary files
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                    logger.info(f"Cleaned up temporary file: {temp_video_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {temp_video_path}: {e}")


@celery_app.task(
    bind=True,
    name="app.worker.tasks.start_campaign_task"
)
def start_campaign_task(self, campaign_id: int, account_ids: list[int]) -> Dict[str, Any]:
    """
    Start a campaign by creating and scheduling jobs for all selected accounts.

    Args:
        campaign_id: The ID of the campaign to start
        account_ids: List of account IDs to use for this campaign

    Returns:
        Dictionary with campaign start results
    """
    return run_async(_start_campaign_task_async(self, campaign_id, account_ids))


async def _start_campaign_task_async(task_self, campaign_id: int, account_ids: list[int]) -> Dict[str, Any]:
    """Async implementation of start_campaign_task."""
    async with async_session_maker() as db:
        try:
            logger.info(f"Starting campaign {campaign_id}")

            # Fetch campaign
            result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
            campaign = result.scalar_one_or_none()

            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            # Update campaign status
            campaign.status = CampaignStatus.RUNNING
            campaign.started_at = datetime.utcnow()
            await db.commit()

            # Get selected accounts
            result = await db.execute(
                select(Account).where(Account.id.in_(account_ids))
            )
            accounts = result.scalars().all()

            if not accounts:
                raise ValueError(f"No accounts found for campaign {campaign_id}")

            # Get available active proxies
            result = await db.execute(
                select(Proxy).where(Proxy.status == ProxyStatus.ACTIVE)
            )
            proxies = result.scalars().all()

            # Parse schedule configuration
            schedule_config = campaign.schedule
            time_range_minutes = schedule_config.get("interval_minutes", 0)
            account_count = len(accounts)

            jobs_created = []

            # Create jobs for each account
            for idx, account in enumerate(accounts):
                # Calculate delay for this job
                if time_range_minutes > 0 and account_count > 1:
                    # Distribute uploads across the time range
                    max_delay_seconds = time_range_minutes * 60
                    delay_seconds = (max_delay_seconds / (account_count - 1)) * idx
                    # Add some randomness (±10%)
                    jitter = random.uniform(-0.1, 0.1) * delay_seconds
                    delay_seconds = max(0, delay_seconds + jitter)
                else:
                    # Add small random delay to avoid simultaneous uploads
                    delay_seconds = random.uniform(0, 30)

                # Create job
                job = Job(
                    campaign_id=campaign_id,
                    account_id=account.id,
                    status=JobStatus.PENDING,
                    video_path=campaign.video_path,
                    caption=campaign.caption_template,
                    retry_count=0,
                    max_retries=3,
                    created_at=datetime.utcnow()
                )

                db.add(job)
                await db.flush()

                # Schedule the upload task
                upload_video_task.apply_async(
                    args=[job.id],
                    countdown=int(delay_seconds)
                )

                jobs_created.append({
                    "job_id": job.id,
                    "account_id": account.id,
                    "account_email": account.email,
                    "delay_seconds": delay_seconds,
                })

                logger.info(
                    f"Created job {job.id} for account {account.email} "
                    f"with {delay_seconds:.0f}s delay"
                )

            await db.commit()

            logger.info(f"Campaign {campaign_id} started with {len(jobs_created)} jobs")

            return {
                "campaign_id": campaign_id,
                "jobs_created": len(jobs_created),
                "jobs": jobs_created
            }

        except Exception as e:
            logger.exception(f"Error starting campaign {campaign_id}: {str(e)}")

            # Update campaign status to cancelled
            result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
            campaign = result.scalar_one_or_none()

            if campaign:
                campaign.status = CampaignStatus.CANCELLED
                await db.commit()

            raise


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 10},
    name="app.worker.tasks.test_account_task"
)
def test_account_task(self, account_id: int) -> Dict[str, Any]:
    """
    Test if an account's cookies are still valid.

    Args:
        account_id: The ID of the account to test

    Returns:
        Dictionary with test results
    """
    return run_async(_test_account_task_async(self, account_id))


async def _test_account_task_async(task_self, account_id: int) -> Dict[str, Any]:
    """Async implementation of test_account_task."""
    async with async_session_maker() as db:
        try:
            logger.info(f"Testing account {account_id}")

            # Fetch account
            result = await db.execute(select(Account).where(Account.id == account_id))
            account = result.scalar_one_or_none()

            if not account:
                raise ValueError(f"Account {account_id} not found")

            # Initialize uploader to test cookies
            from app.services.tiktok_uploader import TikTokUploader
            uploader = TikTokUploader(
                cookies=account.cookies,
                headless=True
            )

            # Test authentication
            is_valid = await asyncio.to_thread(uploader.test_authentication)

            # Update account status
            if is_valid:
                account.status = AccountStatus.ACTIVE
                logger.info(f"Account {account.email} is valid")
            else:
                account.status = AccountStatus.INACTIVE
                logger.warning(f"Account {account.email} has invalid cookies")

            await db.commit()

            return {
                "account_id": account_id,
                "email": account.email,
                "is_valid": is_valid,
                "status": account.status.value
            }

        except Exception as e:
            logger.exception(f"Error testing account {account_id}: {str(e)}")

            # Mark account as inactive
            result = await db.execute(select(Account).where(Account.id == account_id))
            account = result.scalar_one_or_none()

            if account:
                account.status = AccountStatus.INACTIVE
                await db.commit()

            raise


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 5},
    name="app.worker.tasks.check_proxy_task"
)
def check_proxy_task(self, proxy_id: int) -> Dict[str, Any]:
    """
    Test proxy connectivity and latency.

    Args:
        proxy_id: The ID of the proxy to check

    Returns:
        Dictionary with proxy check results
    """
    return run_async(_check_proxy_task_async(self, proxy_id))


async def _check_proxy_task_async(task_self, proxy_id: int) -> Dict[str, Any]:
    """Async implementation of check_proxy_task."""
    async with async_session_maker() as db:
        try:
            logger.info(f"Checking proxy {proxy_id}")

            # Fetch proxy
            result = await db.execute(select(Proxy).where(Proxy.id == proxy_id))
            proxy = result.scalar_one_or_none()

            if not proxy:
                raise ValueError(f"Proxy {proxy_id} not found")

            # Check proxy
            from app.services.proxy_checker import ProxyChecker
            checker = ProxyChecker()
            check_result = await asyncio.to_thread(checker.check_proxy, _proxy_to_dict(proxy))

            # Update proxy status
            proxy.last_checked = datetime.utcnow()

            if check_result.get("is_working"):
                proxy.status = ProxyStatus.ACTIVE
                proxy.latency_ms = check_result.get("latency_ms")
                logger.info(
                    f"Proxy {proxy.host}:{proxy.port} is active "
                    f"(latency: {proxy.latency_ms}ms)"
                )
            else:
                proxy.status = ProxyStatus.ERROR
                logger.warning(
                    f"Proxy {proxy.host}:{proxy.port} failed: "
                    f"{check_result.get('error')}"
                )

            await db.commit()

            return {
                "proxy_id": proxy_id,
                "host": proxy.host,
                "port": proxy.port,
                "is_working": check_result.get("is_working"),
                "latency_ms": check_result.get("latency_ms"),
                "status": proxy.status.value
            }

        except Exception as e:
            logger.exception(f"Error checking proxy {proxy_id}: {str(e)}")

            # Mark proxy as error status
            result = await db.execute(select(Proxy).where(Proxy.id == proxy_id))
            proxy = result.scalar_one_or_none()

            if proxy:
                proxy.status = ProxyStatus.ERROR
                proxy.last_checked = datetime.utcnow()
                await db.commit()

            raise


@celery_app.task(
    bind=True,
    name="app.worker.tasks.batch_process_video_task"
)
def batch_process_video_task(
    self,
    video_path: str,
    count: int,
    campaign_id: int
) -> Dict[str, Any]:
    """
    Create multiple unique variations of a video.

    Args:
        video_path: Path to the source video
        count: Number of variations to create
        campaign_id: Campaign ID to associate the variations with

    Returns:
        Dictionary with processing results
    """
    return run_async(_batch_process_video_task_async(self, video_path, count, campaign_id))


async def _batch_process_video_task_async(
    task_self,
    video_path: str,
    count: int,
    campaign_id: int
) -> Dict[str, Any]:
    """Async implementation of batch_process_video_task."""
    async with async_session_maker() as db:
        try:
            logger.info(
                f"Batch processing video {video_path} - creating {count} variations"
            )

            if not os.path.exists(video_path):
                raise ValueError(f"Video file not found: {video_path}")

            # Fetch campaign
            result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
            campaign = result.scalar_one_or_none()

            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            # Initialize video processor
            from app.services.video_processor import VideoProcessor
            processor = VideoProcessor()

            # Create variations
            variations = []
            for i in range(count):
                try:
                    # Create unique variation
                    variation_path = await asyncio.to_thread(
                        processor.create_variation,
                        video_path,
                        variation_number=i + 1
                    )

                    variations.append(variation_path)
                    logger.info(f"Created variation {i + 1}/{count}: {variation_path}")

                except Exception as e:
                    logger.error(f"Failed to create variation {i + 1}: {str(e)}")
                    continue

            logger.info(
                f"Batch processing completed: {len(variations)}/{count} variations created"
            )

            return {
                "campaign_id": campaign_id,
                "requested_count": count,
                "created_count": len(variations),
                "variations": variations
            }

        except Exception as e:
            logger.exception(f"Error in batch video processing: {str(e)}")
            raise


# Additional helper tasks

@celery_app.task(
    bind=True,
    name="app.worker.tasks.cleanup_old_jobs_task"
)
def cleanup_old_jobs_task(self, days: int = 30) -> Dict[str, Any]:
    """
    Clean up completed jobs older than specified days.

    Args:
        days: Number of days to keep jobs

    Returns:
        Dictionary with cleanup results
    """
    return run_async(_cleanup_old_jobs_task_async(self, days))


async def _cleanup_old_jobs_task_async(task_self, days: int = 30) -> Dict[str, Any]:
    """Async implementation of cleanup_old_jobs_task."""
    async with async_session_maker() as db:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get old completed/failed jobs
            result = await db.execute(
                select(Job).where(
                    Job.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]),
                    Job.completed_at < cutoff_date
                )
            )
            old_jobs = result.scalars().all()

            # Delete jobs
            for job in old_jobs:
                await db.delete(job)

            await db.commit()

            deleted_count = len(old_jobs)
            logger.info(f"Cleaned up {deleted_count} old jobs")

            return {
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }

        except Exception as e:
            logger.exception(f"Error cleaning up old jobs: {str(e)}")
            raise


@celery_app.task(
    bind=True,
    name="app.worker.tasks.check_all_proxies_task"
)
def check_all_proxies_task(self) -> Dict[str, Any]:
    """
    Check all proxies in the database.

    Returns:
        Dictionary with check results
    """
    return run_async(_check_all_proxies_task_async(self))


async def _check_all_proxies_task_async(task_self) -> Dict[str, Any]:
    """Async implementation of check_all_proxies_task."""
    async with async_session_maker() as db:
        try:
            result = await db.execute(select(Proxy))
            proxies = result.scalars().all()

            # Schedule check task for each proxy
            task_ids = []
            for proxy in proxies:
                result = check_proxy_task.delay(proxy.id)
                task_ids.append(result.id)

            logger.info(f"Scheduled proxy checks for {len(proxies)} proxies")

            return {
                "proxies_checked": len(proxies),
                "task_ids": task_ids
            }

        except Exception as e:
            logger.exception(f"Error scheduling proxy checks: {str(e)}")
            raise


# Helper functions

def _proxy_to_dict(proxy: Proxy) -> Dict[str, Any]:
    """Convert Proxy model to dictionary."""
    return {
        "host": proxy.host,
        "port": proxy.port,
        "username": proxy.username,
        "password": proxy.password,
        "type": proxy.type.value,
    }

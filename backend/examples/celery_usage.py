"""
Example Usage of Celery Tasks for TikTok Auto-Poster

This script demonstrates how to use the various Celery tasks
for video uploads, campaign management, and system maintenance.
"""

import asyncio
from datetime import datetime, timedelta
from app.worker.tasks import (
    upload_video_task,
    start_campaign_task,
    test_account_task,
    check_proxy_task,
    batch_process_video_task,
    cleanup_old_jobs_task,
    check_all_proxies_task,
)
from app.worker.celery_app import celery_app


def example_upload_single_video():
    """Example: Upload a video immediately."""
    print("Example 1: Upload single video")

    job_id = 123  # Replace with actual job ID

    # Schedule immediate upload
    result = upload_video_task.delay(job_id)

    print(f"Task ID: {result.id}")
    print(f"Task State: {result.state}")

    # Wait for result (optional)
    # result.wait(timeout=300)
    # print(f"Result: {result.result}")


def example_upload_scheduled():
    """Example: Upload a video with a delay."""
    print("\nExample 2: Upload scheduled video")

    job_id = 124

    # Schedule upload to start in 5 minutes
    result = upload_video_task.apply_async(
        args=[job_id],
        countdown=300  # 5 minutes in seconds
    )

    print(f"Task ID: {result.id}")
    print(f"Scheduled to start in 5 minutes")


def example_upload_at_specific_time():
    """Example: Upload at a specific time."""
    print("\nExample 3: Upload at specific time")

    job_id = 125

    # Schedule upload for tomorrow at 9 AM
    upload_time = datetime.now().replace(
        hour=9, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)

    result = upload_video_task.apply_async(
        args=[job_id],
        eta=upload_time
    )

    print(f"Task ID: {result.id}")
    print(f"Scheduled for: {upload_time}")


def example_start_campaign():
    """Example: Start a campaign with multiple accounts."""
    print("\nExample 4: Start campaign")

    campaign_id = 456
    account_ids = [1, 2, 3, 4, 5]  # Replace with actual account IDs

    # Start campaign
    result = start_campaign_task.delay(
        campaign_id=campaign_id,
        account_ids=account_ids
    )

    print(f"Task ID: {result.id}")
    print(f"Campaign started with {len(account_ids)} accounts")


def example_test_accounts():
    """Example: Test multiple accounts."""
    print("\nExample 5: Test accounts")

    account_ids = [1, 2, 3]

    # Schedule test task for each account
    results = []
    for account_id in account_ids:
        result = test_account_task.delay(account_id)
        results.append(result)
        print(f"Testing account {account_id}: Task {result.id}")

    print(f"Started {len(results)} account tests")


def example_check_proxies():
    """Example: Check proxy health."""
    print("\nExample 6: Check proxies")

    proxy_ids = [10, 11, 12]

    # Check specific proxies
    for proxy_id in proxy_ids:
        result = check_proxy_task.delay(proxy_id)
        print(f"Checking proxy {proxy_id}: Task {result.id}")

    # Or check all proxies
    result = check_all_proxies_task.delay()
    print(f"Checking all proxies: Task {result.id}")


def example_batch_process():
    """Example: Create video variations."""
    print("\nExample 7: Batch process video")

    video_path = "/path/to/video.mp4"
    count = 10
    campaign_id = 456

    # Create 10 variations
    result = batch_process_video_task.delay(
        video_path=video_path,
        count=count,
        campaign_id=campaign_id
    )

    print(f"Task ID: {result.id}")
    print(f"Creating {count} video variations")


def example_cleanup():
    """Example: Clean up old jobs."""
    print("\nExample 8: Clean up old jobs")

    # Clean up jobs older than 30 days
    result = cleanup_old_jobs_task.delay(days=30)

    print(f"Task ID: {result.id}")
    print("Cleaning up jobs older than 30 days")


def example_task_chaining():
    """Example: Chain tasks together."""
    print("\nExample 9: Chain tasks")

    from celery import chain

    # Chain: Process video -> Create variations -> Start campaign
    workflow = chain(
        batch_process_video_task.s("/path/to/video.mp4", 5, 456),
        start_campaign_task.s(456, [1, 2, 3, 4, 5])
    )

    result = workflow.apply_async()
    print(f"Workflow started: Task {result.id}")


def example_task_grouping():
    """Example: Run tasks in parallel."""
    print("\nExample 10: Group tasks")

    from celery import group

    # Test multiple accounts in parallel
    job = group(
        test_account_task.s(1),
        test_account_task.s(2),
        test_account_task.s(3),
    )

    result = job.apply_async()
    print(f"Group started: {len(result)} tasks")


def example_task_callback():
    """Example: Task with callback."""
    print("\nExample 11: Task with callback")

    def on_success(result):
        print(f"Upload completed: {result}")

    def on_failure(exc):
        print(f"Upload failed: {exc}")

    result = upload_video_task.apply_async(
        args=[123],
        link=lambda r: on_success(r),
        link_error=lambda e: on_failure(e)
    )

    print(f"Task ID: {result.id}")


def example_monitor_task():
    """Example: Monitor task progress."""
    print("\nExample 12: Monitor task")

    job_id = 123
    result = upload_video_task.delay(job_id)

    print(f"Task ID: {result.id}")

    # Check task state
    print(f"State: {result.state}")

    # Wait for result with timeout
    try:
        final_result = result.get(timeout=300)  # 5 minute timeout
        print(f"Task completed: {final_result}")
    except Exception as e:
        print(f"Task failed or timed out: {e}")


def example_revoke_task():
    """Example: Cancel a task."""
    print("\nExample 13: Revoke task")

    # Schedule a task
    result = upload_video_task.apply_async(
        args=[123],
        countdown=3600  # 1 hour from now
    )

    print(f"Task ID: {result.id}")

    # Cancel the task
    result.revoke(terminate=True)
    print("Task revoked")


def example_inspect_workers():
    """Example: Inspect worker status."""
    print("\nExample 14: Inspect workers")

    from app.worker.celery_app import celery_app

    # Get active tasks
    inspect = celery_app.control.inspect()

    active = inspect.active()
    print(f"Active tasks: {active}")

    scheduled = inspect.scheduled()
    print(f"Scheduled tasks: {scheduled}")

    stats = inspect.stats()
    print(f"Worker stats: {stats}")


def example_rate_limiting():
    """Example: Rate-limited task execution."""
    print("\nExample 15: Rate limiting")

    # Upload multiple videos with rate limiting
    job_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    for job_id in job_ids:
        # Tasks will be rate-limited to 10/minute automatically
        result = upload_video_task.delay(job_id)
        print(f"Scheduled job {job_id}: Task {result.id}")


def example_retry_configuration():
    """Example: Custom retry configuration."""
    print("\nExample 16: Custom retry")

    # Upload with custom retry settings
    result = upload_video_task.apply_async(
        args=[123],
        retry=True,
        retry_policy={
            'max_retries': 5,
            'interval_start': 10,
            'interval_step': 20,
            'interval_max': 300,
        }
    )

    print(f"Task ID: {result.id}")
    print("Custom retry policy applied")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Celery Task Usage Examples - TikTok Auto-Poster")
    print("=" * 60)

    # Run examples (comment out ones you don't want to run)
    example_upload_single_video()
    example_upload_scheduled()
    example_upload_at_specific_time()
    example_start_campaign()
    example_test_accounts()
    example_check_proxies()
    example_batch_process()
    example_cleanup()
    example_task_chaining()
    example_task_grouping()
    example_monitor_task()
    example_inspect_workers()
    example_rate_limiting()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

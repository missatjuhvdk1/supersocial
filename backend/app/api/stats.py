"""
Stats API endpoints for dashboard statistics.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.database import get_db
from app.models.account import Account, AccountStatus
from app.models.proxy import Proxy, ProxyStatus
from app.models.campaign import Campaign, CampaignStatus
from app.models.job import Job, JobStatus

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics."""

    # Account stats
    total_accounts = await db.scalar(select(func.count(Account.id)))
    active_accounts = await db.scalar(
        select(func.count(Account.id)).where(Account.status == AccountStatus.ACTIVE)
    )

    # Proxy stats
    total_proxies = await db.scalar(select(func.count(Proxy.id)))
    active_proxies = await db.scalar(
        select(func.count(Proxy.id)).where(Proxy.status == ProxyStatus.ACTIVE)
    )

    # Campaign stats
    total_campaigns = await db.scalar(select(func.count(Campaign.id)))
    running_campaigns = await db.scalar(
        select(func.count(Campaign.id)).where(Campaign.status == CampaignStatus.RUNNING)
    )

    # Job stats
    total_jobs = await db.scalar(select(func.count(Job.id)))
    pending_jobs = await db.scalar(
        select(func.count(Job.id)).where(Job.status == JobStatus.PENDING)
    )
    running_jobs = await db.scalar(
        select(func.count(Job.id)).where(Job.status == JobStatus.RUNNING)
    )
    completed_jobs = await db.scalar(
        select(func.count(Job.id)).where(Job.status == JobStatus.COMPLETED)
    )
    failed_jobs = await db.scalar(
        select(func.count(Job.id)).where(Job.status == JobStatus.FAILED)
    )

    # Jobs in last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    jobs_24h = await db.scalar(
        select(func.count(Job.id)).where(Job.created_at >= yesterday)
    )
    completed_24h = await db.scalar(
        select(func.count(Job.id)).where(
            Job.status == JobStatus.COMPLETED,
            Job.completed_at >= yesterday
        )
    )

    # Calculate success rate
    if total_jobs and (completed_jobs + failed_jobs) > 0:
        success_rate = round((completed_jobs / (completed_jobs + failed_jobs)) * 100, 1)
    else:
        success_rate = 0.0

    return {
        "accounts": {
            "total": total_accounts or 0,
            "active": active_accounts or 0,
            "inactive": (total_accounts or 0) - (active_accounts or 0)
        },
        "proxies": {
            "total": total_proxies or 0,
            "active": active_proxies or 0,
            "inactive": (total_proxies or 0) - (active_proxies or 0)
        },
        "campaigns": {
            "total": total_campaigns or 0,
            "running": running_campaigns or 0
        },
        "jobs": {
            "total": total_jobs or 0,
            "pending": pending_jobs or 0,
            "running": running_jobs or 0,
            "completed": completed_jobs or 0,
            "failed": failed_jobs or 0,
            "success_rate": success_rate
        },
        "recent": {
            "jobs_24h": jobs_24h or 0,
            "completed_24h": completed_24h or 0
        }
    }


@router.get("/activity")
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get recent job activity."""
    result = await db.execute(
        select(Job)
        .order_by(Job.created_at.desc())
        .limit(limit)
    )
    jobs = result.scalars().all()

    activities = []
    for job in jobs:
        # Get account email
        account_result = await db.execute(
            select(Account).where(Account.id == job.account_id)
        )
        account = account_result.scalar_one_or_none()

        activities.append({
            "job_id": job.id,
            "campaign_id": job.campaign_id,
            "account_email": account.email if account else "Unknown",
            "status": job.status.value,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message
        })

    return {"activities": activities}

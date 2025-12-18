from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobRetry,
    JobRetryResponse
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    campaign_id: Optional[int] = Query(None, description="Filter by campaign ID"),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    db: AsyncSession = Depends(get_db)
) -> List[Job]:
    """List all jobs with optional filters and pagination."""
    query = select(Job)

    # Apply filters
    filters = []
    if campaign_id:
        filters.append(Job.campaign_id == campaign_id)
    if account_id:
        filters.append(Job.account_id == account_id)
    if status:
        filters.append(Job.status == status)

    if filters:
        query = query.where(and_(*filters))

    # Apply pagination and ordering
    query = query.offset(skip).limit(limit).order_by(Job.created_at.desc())

    result = await db.execute(query)
    jobs = result.scalars().all()
    return list(jobs)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
) -> Job:
    """Get a specific job by ID with full details."""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )

    return job


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db)
) -> Job:
    """Create a new job manually."""
    job = Job(**job_data.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: AsyncSession = Depends(get_db)
) -> Job:
    """Update an existing job."""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )

    # Update only provided fields
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    await db.commit()
    await db.refresh(job)

    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a job."""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )

    await db.delete(job)
    await db.commit()


@router.post("/{job_id}/retry", response_model=JobRetryResponse)
async def retry_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
) -> JobRetryResponse:
    """Retry a failed job."""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )

    if job.status not in [JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job with status '{job.status}' cannot be retried. Only failed or cancelled jobs can be retried."
        )

    if job.retry_count >= job.max_retries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job has reached maximum retry limit ({job.max_retries})"
        )

    # Reset job for retry
    job.status = JobStatus.PENDING
    job.retry_count += 1
    job.error_message = None
    job.started_at = None
    job.completed_at = None

    await db.commit()
    await db.refresh(job)

    return JobRetryResponse(
        job_id=job.id,
        status=job.status,
        retry_count=job.retry_count,
        message=f"Job queued for retry (attempt {job.retry_count}/{job.max_retries})"
    )


@router.post("/retry-failed", response_model=List[JobRetryResponse])
async def retry_all_failed_jobs(
    campaign_id: Optional[int] = Query(None, description="Filter by campaign ID"),
    db: AsyncSession = Depends(get_db)
) -> List[JobRetryResponse]:
    """Retry all failed jobs, optionally filtered by campaign."""
    query = select(Job).where(Job.status == JobStatus.FAILED)

    if campaign_id:
        query = query.where(Job.campaign_id == campaign_id)

    result = await db.execute(query)
    failed_jobs = result.scalars().all()

    retry_responses = []

    for job in failed_jobs:
        if job.retry_count < job.max_retries:
            # Reset job for retry
            job.status = JobStatus.PENDING
            job.retry_count += 1
            job.error_message = None
            job.started_at = None
            job.completed_at = None

            retry_responses.append(
                JobRetryResponse(
                    job_id=job.id,
                    status=job.status,
                    retry_count=job.retry_count,
                    message=f"Job queued for retry (attempt {job.retry_count}/{job.max_retries})"
                )
            )

    await db.commit()

    return retry_responses


@router.get("/statistics/summary")
async def get_job_statistics(
    campaign_id: Optional[int] = Query(None, description="Filter by campaign ID"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get job statistics summary."""
    query = select(Job)

    if campaign_id:
        query = query.where(Job.campaign_id == campaign_id)

    result = await db.execute(query)
    jobs = result.scalars().all()

    # Calculate statistics
    total = len(jobs)
    pending = sum(1 for job in jobs if job.status == JobStatus.PENDING)
    running = sum(1 for job in jobs if job.status == JobStatus.RUNNING)
    completed = sum(1 for job in jobs if job.status == JobStatus.COMPLETED)
    failed = sum(1 for job in jobs if job.status == JobStatus.FAILED)
    cancelled = sum(1 for job in jobs if job.status == JobStatus.CANCELLED)

    return {
        "total": total,
        "pending": pending,
        "running": running,
        "completed": completed,
        "failed": failed,
        "cancelled": cancelled,
        "success_rate": round((completed / total * 100) if total > 0 else 0, 2)
    }

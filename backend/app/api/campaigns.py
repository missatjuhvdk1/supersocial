from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import os
import uuid
import random
import logging

from app.database import get_db
from app.models.campaign import Campaign, CampaignStatus
from app.models.job import Job, JobStatus
from app.models.account import Account, AccountStatus
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignStart,
    CampaignStartResponse
)
from app.worker.tasks import upload_video_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[Campaign]:
    """List all campaigns with pagination."""
    result = await db.execute(
        select(Campaign).offset(skip).limit(limit).order_by(Campaign.created_at.desc())
    )
    campaigns = result.scalars().all()
    return list(campaigns)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
) -> Campaign:
    """Get a specific campaign by ID."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with id {campaign_id} not found"
        )

    return campaign


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db)
) -> Campaign:
    """Create a new campaign."""
    campaign = Campaign(**campaign_data.model_dump())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: AsyncSession = Depends(get_db)
) -> Campaign:
    """Update an existing campaign."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with id {campaign_id} not found"
        )

    # Update only provided fields
    update_data = campaign_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)

    await db.commit()
    await db.refresh(campaign)

    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a campaign."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with id {campaign_id} not found"
        )

    await db.delete(campaign)
    await db.commit()


@router.post("/{campaign_id}/start", response_model=CampaignStartResponse)
async def start_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
) -> CampaignStartResponse:
    """Start a campaign and create jobs based on account selection criteria."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with id {campaign_id} not found"
        )

    if campaign.status == CampaignStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign is already running"
        )

    # Get account selection configuration
    account_selection = campaign.account_selection
    strategy = account_selection.get("strategy", "all")
    filters = account_selection.get("filters", {})
    max_accounts = account_selection.get("max_accounts")
    random_select = account_selection.get("random_select", False)

    # Build query for selecting accounts
    query = select(Account).where(Account.status == AccountStatus.ACTIVE)

    # Apply filters if provided
    if "proxy_id" in filters and filters["proxy_id"]:
        query = query.where(Account.proxy_id == filters["proxy_id"])

    if "profile_id" in filters and filters["profile_id"]:
        query = query.where(Account.profile_id == filters["profile_id"])

    # Execute query
    result = await db.execute(query)
    accounts = list(result.scalars().all())

    if not accounts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active accounts found matching the selection criteria"
        )

    # Random selection if requested
    if random_select and max_accounts and max_accounts < len(accounts):
        accounts = random.sample(accounts, max_accounts)
    elif max_accounts and max_accounts < len(accounts):
        accounts = accounts[:max_accounts]

    # Get schedule configuration for delay calculation
    schedule_config = campaign.schedule or {}
    interval_minutes = schedule_config.get("interval_minutes", 5)
    account_count = len(accounts)

    # Create jobs and schedule Celery tasks
    jobs_created = 0
    scheduled_tasks = []

    for idx, account in enumerate(accounts):
        # Calculate delay for this job (distribute across time range)
        if interval_minutes > 0 and account_count > 1:
            max_delay_seconds = interval_minutes * 60
            delay_seconds = (max_delay_seconds / (account_count - 1)) * idx
            # Add jitter (±10%) to avoid patterns
            jitter = random.uniform(-0.1, 0.1) * delay_seconds
            delay_seconds = max(0, delay_seconds + jitter)
        else:
            # Small random delay between 5-30 seconds
            delay_seconds = random.uniform(5, 30)

        # Create job record
        job = Job(
            campaign_id=campaign.id,
            account_id=account.id,
            video_path=campaign.video_path,
            caption=campaign.caption_template,
            status=JobStatus.PENDING,
            retry_count=0,
            max_retries=3,
            created_at=datetime.utcnow()
        )
        db.add(job)
        await db.flush()  # Get the job ID

        # Schedule Celery task with delay
        task = upload_video_task.apply_async(
            args=[job.id],
            countdown=int(delay_seconds)
        )

        scheduled_tasks.append({
            "job_id": job.id,
            "account_id": account.id,
            "account_email": account.email,
            "delay_seconds": round(delay_seconds, 1),
            "celery_task_id": task.id
        })

        jobs_created += 1
        logger.info(f"Scheduled job {job.id} for account {account.email} with {delay_seconds:.0f}s delay")

    # Update campaign status
    campaign.status = CampaignStatus.RUNNING
    campaign.started_at = datetime.utcnow()

    await db.commit()

    logger.info(f"Campaign {campaign_id} started with {jobs_created} jobs")

    return CampaignStartResponse(
        campaign_id=campaign.id,
        status=campaign.status,
        jobs_created=jobs_created,
        message=f"Campaign started successfully with {jobs_created} jobs scheduled"
    )


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
) -> Campaign:
    """Pause a running campaign."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with id {campaign_id} not found"
        )

    if campaign.status != CampaignStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign is not running"
        )

    campaign.status = CampaignStatus.PAUSED
    await db.commit()
    await db.refresh(campaign)

    return campaign


@router.post("/{campaign_id}/cancel", response_model=CampaignResponse)
async def cancel_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
) -> Campaign:
    """Cancel a campaign."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with id {campaign_id} not found"
        )

    campaign.status = CampaignStatus.CANCELLED
    campaign.completed_at = datetime.utcnow()

    # Cancel all pending jobs
    result = await db.execute(
        select(Job).where(
            Job.campaign_id == campaign_id,
            Job.status == JobStatus.PENDING
        )
    )
    pending_jobs = result.scalars().all()

    for job in pending_jobs:
        job.status = JobStatus.CANCELLED

    await db.commit()
    await db.refresh(campaign)

    return campaign


# Video upload endpoint
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


@router.post("/upload-video")
async def upload_video(
    video: UploadFile = File(...),
):
    """Upload a video file for use in campaigns."""
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, "videos"), exist_ok=True)

    # Validate file type
    allowed_types = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska"]
    if video.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    # Generate unique filename
    file_extension = os.path.splitext(video.filename)[1] or ".mp4"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, "videos", unique_filename)

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)

        logger.info(f"Video uploaded: {file_path}")

        return {
            "success": True,
            "filename": unique_filename,
            "original_filename": video.filename,
            "path": file_path,
            "size": len(content)
        }
    except Exception as e:
        logger.error(f"Failed to upload video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save video: {str(e)}"
        )


@router.post("/create-with-video")
async def create_campaign_with_video(
    name: str = Form(...),
    caption: str = Form(...),
    account_selection: str = Form("all"),
    random_count: Optional[int] = Form(None),
    schedule_start: str = Form("08:00"),
    schedule_end: str = Form("20:00"),
    delay_min: int = Form(60),
    delay_max: int = Form(180),
    video: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Create a new campaign with video upload in one request."""
    # Upload video first
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, "videos"), exist_ok=True)

    file_extension = os.path.splitext(video.filename)[1] or ".mp4"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, "videos", unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save video: {str(e)}"
        )

    # Build account selection config
    account_selection_config = {
        "strategy": account_selection,
        "filters": {},
    }

    if account_selection == "random" and random_count:
        account_selection_config["max_accounts"] = random_count
        account_selection_config["random_select"] = True

    # Build schedule config
    schedule_config = {
        "start_time": schedule_start,
        "end_time": schedule_end,
        "interval_minutes": (delay_min + delay_max) // 2 // 60,  # Average delay in minutes
        "delay_min_seconds": delay_min,
        "delay_max_seconds": delay_max,
    }

    # Create campaign
    campaign = Campaign(
        name=name,
        video_path=file_path,
        caption_template=caption,
        account_selection=account_selection_config,
        schedule=schedule_config,
        status=CampaignStatus.DRAFT,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    logger.info(f"Campaign created with video: {campaign.id}")

    return {
        "success": True,
        "campaign_id": campaign.id,
        "name": campaign.name,
        "video_path": file_path,
        "status": campaign.status.value
    }

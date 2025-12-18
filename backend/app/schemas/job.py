from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.models.job import JobStatus


class JobBase(BaseModel):
    """Base job schema."""
    campaign_id: int
    account_id: int
    video_path: str = Field(..., min_length=1, max_length=500)
    caption: str = Field(..., min_length=1, max_length=2200)


class JobCreate(JobBase):
    """Schema for creating a job."""
    status: JobStatus = JobStatus.PENDING
    max_retries: int = Field(default=3, ge=0)


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    status: Optional[JobStatus] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: Optional[int] = None


class JobResponse(JobBase):
    """Schema for job response."""
    id: int
    status: JobStatus
    error_message: Optional[str] = None
    retry_count: int
    max_retries: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobRetry(BaseModel):
    """Schema for retrying a job."""
    job_id: int


class JobRetryResponse(BaseModel):
    """Schema for job retry response."""
    job_id: int
    status: JobStatus
    retry_count: int
    message: str

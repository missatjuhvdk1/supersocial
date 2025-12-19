from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.models.campaign import CampaignStatus


class AccountSelectionConfig(BaseModel):
    """Account selection configuration schema."""
    strategy: str = Field(..., description="Selection strategy: round_robin, random, least_used")
    filters: Optional[dict] = Field(default_factory=dict, description="Account filters: status, proxy_id, etc.")
    max_accounts: Optional[int] = Field(None, description="Maximum number of accounts to use")


class ScheduleConfig(BaseModel):
    """Schedule configuration schema."""
    start_time: Optional[datetime] = Field(None, description="Campaign start time")
    end_time: Optional[datetime] = Field(None, description="Campaign end time")
    interval_minutes: int = Field(..., gt=0, description="Interval between posts in minutes")
    posts_per_day: Optional[int] = Field(None, gt=0, description="Maximum posts per day")


class CampaignBase(BaseModel):
    """Base campaign schema."""
    name: str = Field(..., min_length=1, max_length=255)
    video_path: str = Field(..., min_length=1, max_length=500)
    caption_template: str = Field(..., min_length=1, max_length=2200)
    account_selection: dict = Field(...)
    schedule: dict = Field(...)


class CampaignCreate(CampaignBase):
    """Schema for creating a campaign."""
    status: CampaignStatus = CampaignStatus.DRAFT


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[CampaignStatus] = None
    video_path: Optional[str] = Field(None, min_length=1, max_length=500)
    caption_template: Optional[str] = Field(None, min_length=1, max_length=2200)
    account_selection: Optional[dict] = None
    schedule: Optional[dict] = None


class CampaignResponse(CampaignBase):
    """Schema for campaign response."""
    id: int
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CampaignStart(BaseModel):
    """Schema for starting a campaign."""
    campaign_id: int


class CampaignStartResponse(BaseModel):
    """Schema for campaign start response."""
    campaign_id: int
    status: CampaignStatus
    jobs_created: int
    message: str

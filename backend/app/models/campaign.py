from sqlalchemy import String, Integer, Enum, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from typing import Optional, TYPE_CHECKING

from app.database import Base

if TYPE_CHECKING:
    from app.models.job import Job


class CampaignStatus(str, enum.Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Campaign(Base):
    """Campaign model for managing TikTok posting campaigns."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[CampaignStatus] = mapped_column(Enum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT)
    video_path: Mapped[str] = mapped_column(String(500), nullable=False)
    caption_template: Mapped[str] = mapped_column(String(2200), nullable=False)  # TikTok caption max length

    # Account selection criteria and scheduling
    account_selection: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"strategy": "round_robin", "filters": {...}}
    schedule: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"start_time": "...", "interval_minutes": 30, ...}

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="campaign")

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name}, status={self.status})>"

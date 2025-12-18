from sqlalchemy import String, Integer, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from app.database import Base

if TYPE_CHECKING:
    from app.models.account import Account


class BrowserProfile(Base):
    """Browser profile model for managing browser fingerprints."""

    __tablename__ = "browser_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=False)
    viewport: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"width": 1920, "height": 1080}
    timezone: Mapped[str] = mapped_column(String(100), nullable=False)
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    fingerprint: Mapped[dict] = mapped_column(JSON, nullable=False)  # Canvas, WebGL, Audio fingerprints
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="profile")

    def __repr__(self) -> str:
        return f"<BrowserProfile(id={self.id}, name={self.name}, timezone={self.timezone})>"

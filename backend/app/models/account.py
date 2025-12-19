from sqlalchemy import String, Integer, ForeignKey, Enum, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from typing import Optional, TYPE_CHECKING

from app.database import Base

if TYPE_CHECKING:
    from app.models.proxy import Proxy
    from app.models.profile import BrowserProfile
    from app.models.job import Job


class AccountStatus(str, enum.Enum):
    """Account status enumeration."""
    ACTIVE = "active"
    BANNED = "banned"
    COOLDOWN = "cooldown"
    NEEDS_CAPTCHA = "needs_captcha"
    INACTIVE = "inactive"


class Account(Base):
    """TikTok account model."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    cookies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Session cookies
    status: Mapped[AccountStatus] = mapped_column(Enum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE)

    # Foreign Keys
    proxy_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("proxies.id"), nullable=True)
    profile_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("browser_profiles.id"), nullable=True)

    # Timestamps
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    proxy: Mapped[Optional["Proxy"]] = relationship("Proxy", back_populates="accounts")
    profile: Mapped[Optional["BrowserProfile"]] = relationship("BrowserProfile", back_populates="accounts")
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="account")

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, email={self.email}, status={self.status})>"

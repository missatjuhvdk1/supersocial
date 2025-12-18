from sqlalchemy import String, Integer, Float, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from typing import Optional, TYPE_CHECKING

from app.database import Base

if TYPE_CHECKING:
    from app.models.account import Account


class ProxyType(str, enum.Enum):
    """Proxy type enumeration."""
    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"
    MOBILE = "mobile"


class ProxyStatus(str, enum.Enum):
    """Proxy status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    ERROR = "error"


class Proxy(Base):
    """Proxy model for managing proxy servers."""

    __tablename__ = "proxies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[ProxyType] = mapped_column(Enum(ProxyType), nullable=False, default=ProxyType.RESIDENTIAL)
    status: Mapped[ProxyStatus] = mapped_column(Enum(ProxyStatus), nullable=False, default=ProxyStatus.ACTIVE)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="proxy")

    def __repr__(self) -> str:
        return f"<Proxy(id={self.id}, host={self.host}, port={self.port}, type={self.type})>"

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.models.proxy import ProxyType, ProxyStatus


class ProxyBase(BaseModel):
    """Base proxy schema."""
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., gt=0, le=65535)
    username: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, max_length=255)
    type: ProxyType = ProxyType.RESIDENTIAL
    status: ProxyStatus = ProxyStatus.ACTIVE


class ProxyCreate(ProxyBase):
    """Schema for creating a proxy."""
    pass


class ProxyUpdate(BaseModel):
    """Schema for updating a proxy."""
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, gt=0, le=65535)
    username: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, max_length=255)
    type: Optional[ProxyType] = None
    status: Optional[ProxyStatus] = None
    latency_ms: Optional[int] = None


class ProxyResponse(ProxyBase):
    """Schema for proxy response."""
    id: int
    latency_ms: Optional[int] = None
    last_checked: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProxyBulkImport(BaseModel):
    """Schema for bulk importing proxies."""
    proxies: list[ProxyCreate]


class ProxyHealthCheck(BaseModel):
    """Schema for proxy health check response."""
    proxy_id: int
    is_healthy: bool
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None

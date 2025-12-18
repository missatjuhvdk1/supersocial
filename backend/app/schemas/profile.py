from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ViewportConfig(BaseModel):
    """Viewport configuration schema."""
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)


class FingerprintConfig(BaseModel):
    """Browser fingerprint configuration schema."""
    canvas: Optional[dict] = None
    webgl: Optional[dict] = None
    audio: Optional[dict] = None
    fonts: Optional[list[str]] = None
    plugins: Optional[list[str]] = None


class BrowserProfileBase(BaseModel):
    """Base browser profile schema."""
    name: str = Field(..., min_length=1, max_length=255)
    user_agent: str = Field(..., min_length=1, max_length=500)
    viewport: dict = Field(...)
    timezone: str = Field(..., min_length=1, max_length=100)
    locale: str = Field(..., min_length=2, max_length=10)
    fingerprint: dict = Field(...)


class BrowserProfileCreate(BrowserProfileBase):
    """Schema for creating a browser profile."""
    pass


class BrowserProfileUpdate(BaseModel):
    """Schema for updating a browser profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    user_agent: Optional[str] = Field(None, min_length=1, max_length=500)
    viewport: Optional[dict] = None
    timezone: Optional[str] = Field(None, min_length=1, max_length=100)
    locale: Optional[str] = Field(None, min_length=2, max_length=10)
    fingerprint: Optional[dict] = None


class BrowserProfileResponse(BrowserProfileBase):
    """Schema for browser profile response."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BrowserProfileTemplate(BaseModel):
    """Schema for browser profile template."""
    template_name: str
    description: str
    profile: BrowserProfileCreate

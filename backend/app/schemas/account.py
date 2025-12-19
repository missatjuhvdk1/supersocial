from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.models.account import AccountStatus


class AccountBase(BaseModel):
    """Base account schema."""
    email: EmailStr
    status: AccountStatus = AccountStatus.ACTIVE
    proxy_id: Optional[int] = None
    profile_id: Optional[int] = None


class AccountCreate(AccountBase):
    """Schema for creating an account."""
    password: str = Field(..., min_length=1)


class AccountUpdate(BaseModel):
    """Schema for updating an account."""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=1)
    cookies: Optional[dict] = None
    status: Optional[AccountStatus] = None
    proxy_id: Optional[int] = None
    profile_id: Optional[int] = None
    last_used: Optional[datetime] = None


class AccountResponse(AccountBase):
    """Schema for account response."""
    id: int
    cookies: Optional[dict] = None
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class AccountBulkImport(BaseModel):
    """Schema for bulk importing accounts."""
    accounts: list[AccountCreate]


class AccountTestLogin(BaseModel):
    """Schema for testing account login."""
    account_id: int


class AccountTestLoginResponse(BaseModel):
    """Schema for test login response."""
    account_id: int
    success: bool
    error_message: Optional[str] = None
    cookies: Optional[dict] = None

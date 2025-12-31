"""Dependency injection functions for FastAPI routes."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated

from app.database import get_db
from app.models.user import User
from app.core.security import decode_access_token


# HTTP Bearer token scheme for JWT authentication
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: The HTTP authorization credentials containing the JWT token
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If the token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode the JWT token
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    # Extract user_id from token
    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get the current active user.

    Args:
        current_user: The current authenticated user

    Returns:
        User: The current active user

    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

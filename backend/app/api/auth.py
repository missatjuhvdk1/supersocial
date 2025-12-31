"""Authentication router for user registration, login, and profile management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
from datetime import timedelta

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from app.core.deps import get_current_user
from app.config import settings


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Register a new user.

    Creates a new user account with the provided email, username, and password.
    Returns a JWT access token upon successful registration.

    Args:
        user_data: User registration data (email, username, password)
        db: Database session

    Returns:
        Token: JWT access token and token type

    Raises:
        HTTPException: If email or username already exists
    """
    # Check if user with email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_data.email} already exists"
        )

    # Check if user with username already exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username {user_data.username} already taken"
        )

    # Create new user with hashed password
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Authenticate a user and return a JWT token.

    Validates user credentials and returns a JWT access token if successful.

    Args:
        credentials: User login credentials (email and password)
        db: Database session

    Returns:
        Token: JWT access token and token type

    Raises:
        HTTPException: If credentials are invalid or user is inactive
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get the current authenticated user's profile.

    This is a protected endpoint that requires a valid JWT token.

    Args:
        current_user: The authenticated user from JWT token

    Returns:
        UserResponse: The current user's profile information
    """
    return current_user


@router.post("/logout")
async def logout() -> dict:
    """
    Logout the current user.

    This is a placeholder endpoint. In a stateless JWT implementation,
    logout is typically handled on the client side by removing the token.

    For a more robust solution, you could:
    - Implement a token blacklist in Redis
    - Use refresh tokens with shorter-lived access tokens
    - Track active sessions in the database

    Returns:
        dict: Success message
    """
    return {"message": "Successfully logged out"}

"""Security utilities for password hashing and JWT token management."""
from datetime import datetime, timedelta
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to compare against

    Returns:
        bool: True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta (default: 7 days)

    Returns:
        str: The encoded JWT refresh token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify
        token_type: The expected token type ("access" or "refresh")

    Returns:
        dict | None: The decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode a JWT access token (alias for verify_token with type="access").

    Args:
        token: The JWT token to decode

    Returns:
        dict | None: The decoded token payload or None if invalid
    """
    return verify_token(token, token_type="access")

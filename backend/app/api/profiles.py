from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.profile import BrowserProfile
from app.schemas.profile import (
    BrowserProfileCreate,
    BrowserProfileUpdate,
    BrowserProfileResponse,
    BrowserProfileTemplate
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


# Pre-defined browser profile templates
PROFILE_TEMPLATES = {
    "chrome_windows": BrowserProfileTemplate(
        template_name="Chrome on Windows 11",
        description="Standard Chrome browser on Windows 11",
        profile=BrowserProfileCreate(
            name="Chrome Windows 11",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            timezone="America/New_York",
            locale="en-US",
            fingerprint={
                "canvas": {"noise": 0.01},
                "webgl": {"vendor": "Google Inc.", "renderer": "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)"},
                "audio": {"noise": 0.001}
            }
        )
    ),
    "chrome_mac": BrowserProfileTemplate(
        template_name="Chrome on macOS",
        description="Standard Chrome browser on macOS",
        profile=BrowserProfileCreate(
            name="Chrome macOS",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            timezone="America/Los_Angeles",
            locale="en-US",
            fingerprint={
                "canvas": {"noise": 0.01},
                "webgl": {"vendor": "Google Inc.", "renderer": "ANGLE (Intel Inc., Intel Iris OpenGL Engine)"},
                "audio": {"noise": 0.001}
            }
        )
    ),
    "mobile_android": BrowserProfileTemplate(
        template_name="Chrome on Android",
        description="Chrome browser on Android mobile device",
        profile=BrowserProfileCreate(
            name="Chrome Android",
            user_agent="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
            viewport={"width": 412, "height": 915},
            timezone="America/New_York",
            locale="en-US",
            fingerprint={
                "canvas": {"noise": 0.01},
                "webgl": {"vendor": "Qualcomm", "renderer": "Adreno (TM) 640"},
                "audio": {"noise": 0.001}
            }
        )
    )
}


@router.get("/", response_model=List[BrowserProfileResponse])
async def list_profiles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[BrowserProfile]:
    """List all browser profiles with pagination."""
    result = await db.execute(
        select(BrowserProfile).offset(skip).limit(limit)
    )
    profiles = result.scalars().all()
    return list(profiles)


@router.get("/templates", response_model=List[BrowserProfileTemplate])
async def list_templates() -> List[BrowserProfileTemplate]:
    """Get list of available browser profile templates."""
    return list(PROFILE_TEMPLATES.values())


@router.get("/{profile_id}", response_model=BrowserProfileResponse)
async def get_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db)
) -> BrowserProfile:
    """Get a specific browser profile by ID."""
    result = await db.execute(
        select(BrowserProfile).where(BrowserProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Browser profile with id {profile_id} not found"
        )

    return profile


@router.post("/", response_model=BrowserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: BrowserProfileCreate,
    db: AsyncSession = Depends(get_db)
) -> BrowserProfile:
    """Create a new browser profile."""
    # Check if profile with name already exists
    result = await db.execute(
        select(BrowserProfile).where(BrowserProfile.name == profile_data.name)
    )
    existing_profile = result.scalar_one_or_none()

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Browser profile with name '{profile_data.name}' already exists"
        )

    profile = BrowserProfile(**profile_data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return profile


@router.post("/from-template/{template_name}", response_model=BrowserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile_from_template(
    template_name: str,
    db: AsyncSession = Depends(get_db)
) -> BrowserProfile:
    """Create a new browser profile from a template."""
    template = PROFILE_TEMPLATES.get(template_name)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_name}' not found"
        )

    # Check if profile with name already exists
    result = await db.execute(
        select(BrowserProfile).where(BrowserProfile.name == template.profile.name)
    )
    existing_profile = result.scalar_one_or_none()

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Browser profile with name '{template.profile.name}' already exists"
        )

    profile = BrowserProfile(**template.profile.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return profile


@router.put("/{profile_id}", response_model=BrowserProfileResponse)
async def update_profile(
    profile_id: int,
    profile_data: BrowserProfileUpdate,
    db: AsyncSession = Depends(get_db)
) -> BrowserProfile:
    """Update an existing browser profile."""
    result = await db.execute(
        select(BrowserProfile).where(BrowserProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Browser profile with id {profile_id} not found"
        )

    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a browser profile."""
    result = await db.execute(
        select(BrowserProfile).where(BrowserProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Browser profile with id {profile_id} not found"
        )

    await db.delete(profile)
    await db.commit()

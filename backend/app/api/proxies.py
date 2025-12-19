from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import csv
import io
from datetime import datetime

from app.database import get_db
from app.models.proxy import Proxy
from app.schemas.proxy import (
    ProxyCreate,
    ProxyUpdate,
    ProxyResponse,
    ProxyBulkImport,
    ProxyHealthCheck
)

router = APIRouter(prefix="/proxies", tags=["proxies"])


@router.get("/", response_model=List[ProxyResponse])
async def list_proxies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[Proxy]:
    """List all proxies with pagination."""
    result = await db.execute(
        select(Proxy).offset(skip).limit(limit)
    )
    proxies = result.scalars().all()
    return list(proxies)


@router.get("/{proxy_id}", response_model=ProxyResponse)
async def get_proxy(
    proxy_id: int,
    db: AsyncSession = Depends(get_db)
) -> Proxy:
    """Get a specific proxy by ID."""
    result = await db.execute(
        select(Proxy).where(Proxy.id == proxy_id)
    )
    proxy = result.scalar_one_or_none()

    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proxy with id {proxy_id} not found"
        )

    return proxy


@router.post("/", response_model=ProxyResponse, status_code=status.HTTP_201_CREATED)
async def create_proxy(
    proxy_data: ProxyCreate,
    db: AsyncSession = Depends(get_db)
) -> Proxy:
    """Create a new proxy."""
    proxy = Proxy(**proxy_data.model_dump())
    db.add(proxy)
    await db.commit()
    await db.refresh(proxy)

    return proxy


@router.put("/{proxy_id}", response_model=ProxyResponse)
async def update_proxy(
    proxy_id: int,
    proxy_data: ProxyUpdate,
    db: AsyncSession = Depends(get_db)
) -> Proxy:
    """Update an existing proxy."""
    result = await db.execute(
        select(Proxy).where(Proxy.id == proxy_id)
    )
    proxy = result.scalar_one_or_none()

    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proxy with id {proxy_id} not found"
        )

    # Update only provided fields
    update_data = proxy_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proxy, field, value)

    await db.commit()
    await db.refresh(proxy)

    return proxy


@router.delete("/{proxy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proxy(
    proxy_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a proxy."""
    result = await db.execute(
        select(Proxy).where(Proxy.id == proxy_id)
    )
    proxy = result.scalar_one_or_none()

    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proxy with id {proxy_id} not found"
        )

    await db.delete(proxy)
    await db.commit()


@router.post("/bulk-import", response_model=List[ProxyResponse])
async def bulk_import_proxies(
    bulk_data: ProxyBulkImport,
    db: AsyncSession = Depends(get_db)
) -> List[Proxy]:
    """Bulk import proxies from JSON."""
    created_proxies = []

    for proxy_data in bulk_data.proxies:
        proxy = Proxy(**proxy_data.model_dump())
        db.add(proxy)
        created_proxies.append(proxy)

    await db.commit()

    # Refresh all created proxies
    for proxy in created_proxies:
        await db.refresh(proxy)

    return created_proxies


@router.post("/bulk-import-txt", response_model=List[ProxyResponse])
async def bulk_import_proxies_txt(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> List[Proxy]:
    """Bulk import proxies from TXT file.

    Supported formats (one proxy per line):
    - host:port
    - host:port:username:password
    - ip:port
    - ip:port:username:password
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    contents = await file.read()
    lines = contents.decode('utf-8').strip().split('\n')

    created_proxies = []
    errors = []

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):  # Skip empty lines and comments
            continue

        parts = line.split(':')

        try:
            if len(parts) == 2:
                # host:port format
                host, port = parts
                proxy_data = ProxyCreate(
                    host=host.strip(),
                    port=int(port.strip()),
                    username=None,
                    password=None,
                )
            elif len(parts) == 4:
                # host:port:username:password format
                host, port, username, password = parts
                proxy_data = ProxyCreate(
                    host=host.strip(),
                    port=int(port.strip()),
                    username=username.strip() if username.strip() else None,
                    password=password.strip() if password.strip() else None,
                )
            else:
                errors.append(f"Line {line_num}: Invalid format '{line}'")
                continue

            proxy = Proxy(**proxy_data.model_dump())
            db.add(proxy)
            created_proxies.append(proxy)

        except ValueError as e:
            errors.append(f"Line {line_num}: {str(e)}")
            continue
        except Exception as e:
            errors.append(f"Line {line_num}: {str(e)}")
            continue

    if created_proxies:
        await db.commit()
        for proxy in created_proxies:
            await db.refresh(proxy)

    return created_proxies


@router.post("/bulk-import-csv", response_model=List[ProxyResponse])
async def bulk_import_proxies_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> List[Proxy]:
    """Bulk import proxies from CSV file.

    CSV format: host,port,username,password,type,status
    """
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )

    contents = await file.read()
    csv_data = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.DictReader(csv_data)

    created_proxies = []

    for row in csv_reader:
        try:
            proxy_data = ProxyCreate(
                host=row['host'],
                port=int(row['port']),
                username=row.get('username') or None,
                password=row.get('password') or None,
                type=row.get('type', 'residential'),
                status=row.get('status', 'active'),
            )

            proxy = Proxy(**proxy_data.model_dump())
            db.add(proxy)
            created_proxies.append(proxy)

        except Exception as e:
            # Skip invalid rows
            continue

    await db.commit()

    # Refresh all created proxies
    for proxy in created_proxies:
        await db.refresh(proxy)

    return created_proxies


@router.post("/{proxy_id}/health-check", response_model=ProxyHealthCheck)
async def check_proxy_health(
    proxy_id: int,
    db: AsyncSession = Depends(get_db)
) -> ProxyHealthCheck:
    """Check the health of a specific proxy.

    This endpoint would integrate with your proxy testing logic.
    For now, it's a placeholder that returns a mock response.
    """
    result = await db.execute(
        select(Proxy).where(Proxy.id == proxy_id)
    )
    proxy = result.scalar_one_or_none()

    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proxy with id {proxy_id} not found"
        )

    # TODO: Implement actual proxy health check logic here
    # This is a placeholder response
    # Update proxy last_checked timestamp
    proxy.last_checked = datetime.utcnow()
    await db.commit()

    return ProxyHealthCheck(
        proxy_id=proxy.id,
        is_healthy=False,
        latency_ms=None,
        error_message="Health check not implemented yet"
    )


@router.post("/health-check-all", response_model=List[ProxyHealthCheck])
async def check_all_proxies_health(
    db: AsyncSession = Depends(get_db)
) -> List[ProxyHealthCheck]:
    """Check the health of all proxies.

    This endpoint would integrate with your proxy testing logic.
    For now, it's a placeholder that returns mock responses.
    """
    result = await db.execute(select(Proxy))
    proxies = result.scalars().all()

    health_checks = []
    for proxy in proxies:
        # TODO: Implement actual proxy health check logic here
        proxy.last_checked = datetime.utcnow()

        health_checks.append(
            ProxyHealthCheck(
                proxy_id=proxy.id,
                is_healthy=False,
                latency_ms=None,
                error_message="Health check not implemented yet"
            )
        )

    await db.commit()
    return health_checks

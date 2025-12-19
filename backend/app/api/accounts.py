from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import csv
import io

from app.database import get_db
from app.models.account import Account, AccountStatus
from app.schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountBulkImport,
    AccountTestLogin,
    AccountTestLoginResponse
)
from app.worker.tasks import warmup_account_task, warmup_all_pending_accounts_task

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/", response_model=List[AccountResponse])
async def list_accounts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[Account]:
    """List all accounts with pagination."""
    result = await db.execute(
        select(Account).offset(skip).limit(limit)
    )
    accounts = result.scalars().all()
    return list(accounts)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
) -> Account:
    """Get a specific account by ID."""
    result = await db.execute(
        select(Account).where(Account.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with id {account_id} not found"
        )

    return account


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db)
) -> Account:
    """Create a new account."""
    # Check if account with email already exists
    result = await db.execute(
        select(Account).where(Account.email == account_data.email)
    )
    existing_account = result.scalar_one_or_none()

    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account with email {account_data.email} already exists"
        )

    account = Account(**account_data.model_dump())
    db.add(account)
    await db.commit()
    await db.refresh(account)

    return account


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: AsyncSession = Depends(get_db)
) -> Account:
    """Update an existing account."""
    result = await db.execute(
        select(Account).where(Account.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with id {account_id} not found"
        )

    # Update only provided fields
    update_data = account_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    await db.commit()
    await db.refresh(account)

    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete an account."""
    result = await db.execute(
        select(Account).where(Account.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with id {account_id} not found"
        )

    await db.delete(account)
    await db.commit()


@router.post("/bulk-import", response_model=List[AccountResponse])
async def bulk_import_accounts(
    bulk_data: AccountBulkImport,
    db: AsyncSession = Depends(get_db)
) -> List[Account]:
    """Bulk import accounts from JSON."""
    created_accounts = []

    for account_data in bulk_data.accounts:
        # Check if account already exists
        result = await db.execute(
            select(Account).where(Account.email == account_data.email)
        )
        existing_account = result.scalar_one_or_none()

        if not existing_account:
            account = Account(**account_data.model_dump())
            db.add(account)
            created_accounts.append(account)

    await db.commit()

    # Refresh all created accounts
    for account in created_accounts:
        await db.refresh(account)

    return created_accounts


@router.post("/bulk-import-csv", response_model=List[AccountResponse])
async def bulk_import_accounts_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> List[Account]:
    """Bulk import accounts from CSV file.

    CSV format: email,password,status,proxy_id,profile_id
    """
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )

    contents = await file.read()
    csv_data = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.DictReader(csv_data)

    created_accounts = []

    for row in csv_reader:
        try:
            account_data = AccountCreate(
                email=row['email'],
                password=row['password'],
                status=row.get('status', 'inactive'),  # Default to inactive for warmup
                proxy_id=int(row['proxy_id']) if row.get('proxy_id') else None,
                profile_id=int(row['profile_id']) if row.get('profile_id') else None,
            )

            # Check if account already exists
            result = await db.execute(
                select(Account).where(Account.email == account_data.email)
            )
            existing_account = result.scalar_one_or_none()

            if not existing_account:
                account = Account(**account_data.model_dump())
                db.add(account)
                created_accounts.append(account)

        except Exception as e:
            # Skip invalid rows
            continue

    await db.commit()

    # Refresh all created accounts
    for account in created_accounts:
        await db.refresh(account)

    return created_accounts


@router.post("/{account_id}/warmup")
async def warmup_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Trigger warmup for a single account.

    This schedules a warmup task for the specified account.
    """
    # Verify account exists
    result = await db.execute(
        select(Account).where(Account.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with id {account_id} not found"
        )

    # Schedule warmup task
    task_result = warmup_account_task.delay(account_id)

    return {
        "message": "Warmup started",
        "task_id": task_result.id,
        "account_id": account_id,
        "account_email": account.email
    }


@router.post("/warmup-all")
async def warmup_all_accounts(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Trigger warmup for all pending accounts.

    This schedules warmup tasks for all accounts with INACTIVE status.
    """
    # Count inactive accounts
    result = await db.execute(
        select(Account).where(Account.status == AccountStatus.INACTIVE)
    )
    pending_accounts = result.scalars().all()
    account_count = len(pending_accounts)

    # Schedule warmup task for all pending accounts
    task_result = warmup_all_pending_accounts_task.delay()

    return {
        "message": f"Warmup started for {account_count} accounts",
        "task_id": task_result.id,
        "account_count": account_count
    }


@router.post("/test-login", response_model=AccountTestLoginResponse)
async def test_account_login(
    test_data: AccountTestLogin,
    db: AsyncSession = Depends(get_db)
) -> AccountTestLoginResponse:
    """Test login for an account.

    This endpoint would integrate with your TikTok automation logic.
    For now, it's a placeholder that returns a mock response.
    """
    result = await db.execute(
        select(Account).where(Account.id == test_data.account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with id {test_data.account_id} not found"
        )

    # TODO: Implement actual TikTok login test logic here
    # This is a placeholder response
    return AccountTestLoginResponse(
        account_id=account.id,
        success=False,
        error_message="Login test not implemented yet",
        cookies=None
    )

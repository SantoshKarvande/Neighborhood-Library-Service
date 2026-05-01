from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import TransactionStatus
from app.schemas.schemas import (
    BorrowRequest, FinePayRequest, FineResponse,
    LibraryStats, ReturnRequest, TransactionResponse,
)
from app.services import loans_service

router = APIRouter(prefix="/loans", tags=["Loans"])


# ─── Stats (place first so /stats isn't shadowed by /{id}) ───────────────────

@router.get("/stats", response_model=LibraryStats, tags=["Stats"])
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Library-wide dashboard statistics."""
    return await loans_service.get_stats(db)


# ─── Borrow queries ───────────────────────────────────────────────────────────

@router.get("/borrowed", response_model=dict)
async def get_borrowed_books(
    skip:      int           = Query(0, ge=0),
    limit:     int           = Query(20, ge=1, le=100),
    member_id: Optional[int] = Query(None, description="Filter by member"),
    db: AsyncSession         = Depends(get_db),
):
    """
    All books currently borrowed (not yet returned).
    Optionally filter to a single member.
    """
    total, rows = await loans_service.get_borrowed_books(db, skip, limit, member_id)
    return {
        "total": total, "skip": skip, "limit": limit,
        "items": [TransactionResponse.model_validate(r) for r in rows],
    }


@router.get("/due", response_model=dict)
async def get_due_books(
    skip:  int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """All overdue loans — books not returned past their due date."""
    total, rows = await loans_service.get_due_books(db, skip, limit)
    return {
        "total": total, "skip": skip, "limit": limit,
        "items": [TransactionResponse.model_validate(r) for r in rows],
    }


@router.get("/", response_model=dict)
async def list_loans(
    skip:         int                         = Query(0, ge=0),
    limit:        int                         = Query(20, ge=1, le=100),
    member_id:    Optional[int]               = Query(None),
    book_id:      Optional[int]               = Query(None),
    tx_status:    Optional[TransactionStatus] = Query(None, alias="status"),
    overdue_only: bool                        = Query(False),
    db: AsyncSession                          = Depends(get_db),
):
    """Full loan history with rich filters."""
    total, rows = await loans_service.list_transactions(
        db, skip, limit, member_id, book_id, tx_status, overdue_only
    )
    return {
        "total": total, "skip": skip, "limit": limit,
        "items": [TransactionResponse.model_validate(r) for r in rows],
    }


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_loan(transaction_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single loan transaction by ID."""
    tx = await loans_service.get_tx_or_404(db, transaction_id)
    return loans_service._enrich(tx)


# ─── Borrow / Return ──────────────────────────────────────────────────────────

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def borrow_book(data: BorrowRequest, db: AsyncSession = Depends(get_db)):
    """
    Record a book borrowing.

    - `copy_id`   : the specific physical copy to check out
    - `member_id` : the borrowing member
    - `due_date`  : expected return date/time (must be in the future)
    """
    return await loans_service.borrow_book(db, data)


@router.post("/{transaction_id}/return", response_model=TransactionResponse)
async def return_book(
    transaction_id: int,
    data: ReturnRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Record a book return.
    If the book is returned after the due date, a fine is computed automatically
    using `fine_per_day` (default $0.50 / day).
    """
    return await loans_service.return_book(db, transaction_id, data)


@router.post("/mark-overdue", response_model=dict, tags=["Admin"])
async def mark_overdue(db: AsyncSession = Depends(get_db)):
    """
    Admin/cron endpoint: transition all BORROWED transactions past their
    due date to OVERDUE. Returns the count of records updated.
    """
    count = await loans_service.mark_overdue(db)
    return {"updated": count, "message": f"{count} transaction(s) marked as OVERDUE"}


# ─── Fines ────────────────────────────────────────────────────────────────────

@router.get("/{transaction_id}/fines", response_model=list[FineResponse])
async def get_fines_for_transaction(
    transaction_id: int, db: AsyncSession = Depends(get_db)
):
    """List all fines attached to a specific loan transaction."""
    return await loans_service.get_fines_for_transaction(db, transaction_id)


@router.get("/members/{member_id}/fines", response_model=list[FineResponse], tags=["Fines"])
async def get_fines_for_member(
    member_id:   int  = ...,
    unpaid_only: bool = Query(False, description="Show only unpaid fines"),
    db: AsyncSession  = Depends(get_db),
):
    """List all fines for a given member, optionally only unpaid ones."""
    return await loans_service.get_fines_for_member(db, member_id, unpaid_only)


@router.post("/fines/pay", response_model=list[FineResponse], tags=["Fines"])
async def pay_fines(data: FinePayRequest, db: AsyncSession = Depends(get_db)):
    """Mark one or more fines as paid by providing their IDs."""
    return await loans_service.pay_fines(db, data)



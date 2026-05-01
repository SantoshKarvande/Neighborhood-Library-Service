"""
Service layer for borrow/return/fine operations.

Business rules
──────────────
• A copy must be AVAILABLE to be borrowed.
• Returning a copy transitions:
    copy.status        → AVAILABLE
    transaction.status → RETURNED  (or OVERDUE if past due_date)
  If the return is late a Fine record is created automatically.
• Marking overdue: any BORROWED transaction past due_date → OVERDUE.
• Fines can be paid individually or in bulk.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    Book, BookCopy, BookStatus,
    BorrowTransaction, Fine, Member,
    TransactionStatus,
)
from app.schemas.schemas import BorrowRequest, FinePayRequest, ReturnRequest


# ─── helpers ──────────────────────────────────────────────────────────────────

def _tx_options():
    return [
        selectinload(BorrowTransaction.fines),
        selectinload(BorrowTransaction.copy).selectinload(BookCopy.book),
        selectinload(BorrowTransaction.member),
    ]


def _enrich(tx: BorrowTransaction) -> BorrowTransaction:
    """Attach display fields for the response schema."""
    tx.book_title  = tx.copy.book.title if tx.copy and tx.copy.book else None
    tx.member_name = tx.member.name      if tx.member else None
    return tx


def _as_db_naive(dt: datetime) -> datetime:
    """Normalize datetimes for timestamp-without-timezone DB columns."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone().replace(tzinfo=None)


async def get_tx_or_404(db: AsyncSession, transaction_id: int) -> BorrowTransaction:
    row = (
        await db.execute(
            select(BorrowTransaction)
            .options(*_tx_options())
            .where(BorrowTransaction.transaction_id == transaction_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Transaction {transaction_id} not found")
    return row


# ─── Borrow ───────────────────────────────────────────────────────────────────

async def borrow_book(db: AsyncSession, data: BorrowRequest) -> BorrowTransaction:
    # Load copy with its book
    copy = (
        await db.execute(
            select(BookCopy)
            .options(selectinload(BookCopy.book))
            .where(BookCopy.copy_id == data.copy_id)
        )
    ).scalar_one_or_none()

    if copy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"BookCopy {data.copy_id} not found")
    if copy.status != BookStatus.AVAILABLE:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Copy {data.copy_id} is not available (current status: {copy.status.value})",
        )

    # Validate member exists
    member = await db.get(Member, data.member_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Member {data.member_id} not found")

    # Create transaction
    tx = BorrowTransaction(
        copy_id   = data.copy_id,
        member_id = data.member_id,
        due_date  = _as_db_naive(data.due_date),
        status    = TransactionStatus.BORROWED,
    )
    copy.status = BookStatus.BORROWED

    db.add(tx)
    await db.commit()
    tx = await get_tx_or_404(db, tx.transaction_id)
    return _enrich(tx)


# ─── Return ───────────────────────────────────────────────────────────────────

async def return_book(
    db: AsyncSession, transaction_id: int, data: ReturnRequest
) -> BorrowTransaction:
    tx = await get_tx_or_404(db, transaction_id)

    if tx.status == TransactionStatus.RETURNED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Book has already been returned")

    now = datetime.now()
    tx.return_date = now
    due_date = _as_db_naive(tx.due_date)

    # Determine final status and compute fine
    if now > due_date:
        tx.status = TransactionStatus.RETURNED   # we record RETURNED even if it was overdue
        overdue_days = (now.date() - due_date.date()).days
        fine_amount  = Decimal(str(data.fine_per_day)) * overdue_days
        if fine_amount > 0:
            db.add(Fine(transaction_id=tx.transaction_id, amount=float(fine_amount)))
    else:
        tx.status = TransactionStatus.RETURNED

    # Restore copy availability
    tx.copy.status = BookStatus.AVAILABLE

    await db.commit()
    tx = await get_tx_or_404(db, transaction_id)
    return _enrich(tx)


# ─── Mark overdue (batch job helper) ─────────────────────────────────────────

async def mark_overdue(db: AsyncSession) -> int:
    """
    Transition all BORROWED transactions past their due_date to OVERDUE.
    Returns number of records updated.  Typically called by a scheduler.
    """
    now  = datetime.now()
    rows = (
        await db.execute(
            select(BorrowTransaction).where(
                BorrowTransaction.status == TransactionStatus.BORROWED,
                BorrowTransaction.due_date < now,
            )
        )
    ).scalars().all()

    for tx in rows:
        if _as_db_naive(tx.due_date) < now:
            tx.status = TransactionStatus.OVERDUE

    await db.commit()
    return sum(1 for tx in rows if tx.status == TransactionStatus.OVERDUE)


# ─── List queries ─────────────────────────────────────────────────────────────

async def list_transactions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    member_id:    Optional[int]               = None,
    book_id:      Optional[int]               = None,
    tx_status:    Optional[TransactionStatus] = None,
    overdue_only: bool = False,
) -> tuple[int, Sequence[BorrowTransaction]]:
    q = select(BorrowTransaction).options(*_tx_options())

    if member_id is not None:
        q = q.where(BorrowTransaction.member_id == member_id)

    if book_id is not None:
        q = (
            q.join(BookCopy, BookCopy.copy_id == BorrowTransaction.copy_id)
             .where(BookCopy.book_id == book_id)
        )

    if tx_status is not None:
        q = q.where(BorrowTransaction.status == tx_status)

    if overdue_only:
        now = datetime.now()
        q = q.where(
            BorrowTransaction.status.in_([TransactionStatus.BORROWED, TransactionStatus.OVERDUE]),
            BorrowTransaction.due_date < now,
        )

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows  = (
        await db.execute(
            q.order_by(BorrowTransaction.borrow_date.desc()).offset(skip).limit(limit)
        )
    ).scalars().all()

    return total, [_enrich(tx) for tx in rows]


async def get_borrowed_books(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    member_id: Optional[int] = None,
) -> tuple[int, Sequence[BorrowTransaction]]:
    """All currently borrowed (not yet returned) transactions."""
    return await list_transactions(
        db, skip, limit,
        member_id=member_id,
        tx_status=TransactionStatus.BORROWED,
    )


async def get_due_books(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> tuple[int, Sequence[BorrowTransaction]]:
    """Books that are overdue (past due_date and not returned)."""
    return await list_transactions(db, skip, limit, overdue_only=True)


# ─── Fines ────────────────────────────────────────────────────────────────────

async def get_fines_for_transaction(
    db: AsyncSession, transaction_id: int
) -> Sequence[Fine]:
    await get_tx_or_404(db, transaction_id)   # 404 guard
    rows = (
        await db.execute(
            select(Fine)
            .where(Fine.transaction_id == transaction_id)
            .order_by(Fine.fine_id)
        )
    ).scalars().all()
    return rows


async def get_fines_for_member(
    db: AsyncSession,
    member_id: int,
    unpaid_only: bool = False,
) -> Sequence[Fine]:
    q = (
        select(Fine)
        .join(BorrowTransaction, BorrowTransaction.transaction_id == Fine.transaction_id)
        .where(BorrowTransaction.member_id == member_id)
    )
    if unpaid_only:
        q = q.where(Fine.paid == False)   # noqa: E712
    return (await db.execute(q.order_by(Fine.fine_id))).scalars().all()


async def pay_fines(db: AsyncSession, data: FinePayRequest) -> Sequence[Fine]:
    rows = (
        await db.execute(select(Fine).where(Fine.fine_id.in_(data.fine_ids)))
    ).scalars().all()

    found_ids = {f.fine_id for f in rows}
    missing   = set(data.fine_ids) - found_ids
    if missing:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Fine IDs not found: {sorted(missing)}",
        )

    for fine in rows:
        fine.paid = True

    await db.commit()
    for fine in rows:
        await db.refresh(fine)
    return rows


# ─── Statistics ───────────────────────────────────────────────────────────────

async def get_stats(db: AsyncSession) -> dict:
    total_books      = (await db.execute(select(func.count()).select_from(Book))).scalar_one()
    total_copies     = (await db.execute(select(func.count()).select_from(BookCopy))).scalar_one()
    available_copies = (
        await db.execute(
            select(func.count()).select_from(BookCopy).where(BookCopy.status == BookStatus.AVAILABLE)
        )
    ).scalar_one()
    total_members  = (await db.execute(select(func.count()).select_from(Member))).scalar_one()
    active_loans   = (
        await db.execute(
            select(func.count()).select_from(BorrowTransaction).where(
                BorrowTransaction.status == TransactionStatus.BORROWED
            )
        )
    ).scalar_one()
    now = datetime.now()
    overdue_loans = (
        await db.execute(
            select(func.count()).select_from(BorrowTransaction).where(
                BorrowTransaction.status.in_([TransactionStatus.BORROWED, TransactionStatus.OVERDUE]),
                BorrowTransaction.due_date < now,
            )
        )
    ).scalar_one()
    unpaid_fines = (
        await db.execute(
            select(func.coalesce(func.sum(Fine.amount), 0)).where(Fine.paid == False)   # noqa: E712
        )
    ).scalar_one()

    return {
        "total_books":        total_books,
        "total_copies":       total_copies,
        "available_copies":   available_copies,
        "total_members":      total_members,
        "active_loans":       active_loans,
        "overdue_loans":      overdue_loans,
        "total_fines_unpaid": float(unpaid_fines),
    }

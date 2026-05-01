"""Service layer for Member operations."""

from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Member
from app.schemas.schemas import MemberCreate, MemberUpdate


async def get_or_404(db: AsyncSession, member_id: int) -> Member:
    row = await db.get(Member, member_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Member {member_id} not found")
    return row


async def list_members(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
) -> tuple[int, Sequence[Member]]:
    q = select(Member)
    if search:
        q = q.where(Member.name.ilike(f"%{search}%") | Member.email.ilike(f"%{search}%"))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows  = (await db.execute(q.order_by(Member.name).offset(skip).limit(limit))).scalars().all()
    return total, rows


async def create_member(db: AsyncSession, data: MemberCreate) -> Member:
    if data.email:
        dup = (
            await db.execute(select(Member).where(Member.email == data.email))
        ).scalar_one_or_none()
        if dup:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Email '{data.email}' is already registered (member_id={dup.member_id})",
            )

    member = Member(name=data.name, email=data.email, phone=data.phone)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def update_member(db: AsyncSession, member_id: int, data: MemberUpdate) -> Member:
    member  = await get_or_404(db, member_id)
    updates = data.model_dump(exclude_unset=True)

    if "email" in updates and updates["email"] and updates["email"] != member.email:
        dup = (
            await db.execute(
                select(Member).where(
                    Member.email == updates["email"],
                    Member.member_id != member_id,
                )
            )
        ).scalar_one_or_none()
        if dup:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Email '{updates['email']}' is already registered",
            )

    for field, val in updates.items():
        setattr(member, field, val)

    await db.commit()
    await db.refresh(member)
    return member


async def delete_member(db: AsyncSession, member_id: int) -> None:
    from app.models.models import BorrowTransaction, TransactionStatus

    member = await get_or_404(db, member_id)

    active = (
        await db.execute(
            select(BorrowTransaction).where(
                BorrowTransaction.member_id == member_id,
                BorrowTransaction.status != TransactionStatus.RETURNED,
            )
        )
    ).scalar_one_or_none()

    if active:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Member has active loans; all books must be returned before deletion.",
        )

    await db.delete(member)
    await db.commit()



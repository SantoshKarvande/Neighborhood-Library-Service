"""Service layer for Author operations."""

from typing import List, Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Author
from app.schemas.schemas import AuthorCreate, AuthorUpdate


async def get_or_404(db: AsyncSession, author_id: int) -> Author:
    row = await db.get(Author, author_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Author {author_id} not found")
    return row


async def list_authors(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
) -> tuple[int, Sequence[Author]]:
    q = select(Author)
    if search:
        q = q.where(Author.name.ilike(f"%{search}%"))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows  = (await db.execute(q.order_by(Author.name).offset(skip).limit(limit))).scalars().all()
    return total, rows


async def create_author(db: AsyncSession, data: AuthorCreate) -> Author:
    author = Author(name=data.name)
    db.add(author)
    await db.commit()
    await db.refresh(author)
    return author


async def update_author(db: AsyncSession, author_id: int, data: AuthorUpdate) -> Author:
    author = await get_or_404(db, author_id)
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(author, field, val)
    await db.commit()
    await db.refresh(author)
    return author


async def delete_author(db: AsyncSession, author_id: int) -> None:
    author = await get_or_404(db, author_id)
    await db.delete(author)
    await db.commit()


